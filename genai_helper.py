"""
GenAI Helper Module

This module provides optional GenAI integration for:
1. Converting natural language rules to structured DSL format
2. Suggesting validation rules based on data profiling
3. Explaining reconciliation discrepancies
4. Generating rule documentation
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class GenAIConfig:
    """Configuration for GenAI integration."""
    enabled: bool = False
    provider: str = "Claude"
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    model: str = "claude-3-5-sonnet-20241022"


class GenAIHelper:
    """
    Helper class for GenAI-powered features in the reconciliation tool.
    """
    
    def __init__(self, config: GenAIConfig, logger=None):
        """
        Initialize the GenAI helper.
        
        Args:
            config: GenAI configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.client = None
        
        if config.enabled:
            self._initialize_client()
    
    def log(self, level: str, component: str, message: str):
        """Log a message if logger is available."""
        if self.logger:
            self.logger.log(level, component, message)
    
    def _initialize_client(self):
        """Initialize the API client based on provider."""
        try:
            if self.config.provider.lower() == "claude":
                # Use OpenAI-compatible client for Claude via the configured endpoint
                from openai import OpenAI
                
                # The system has OPENAI_API_KEY configured for OpenAI-compatible API
                # For Claude, user would need to set ANTHROPIC_API_KEY
                api_key = os.environ.get(self.config.api_key_env_var)
                
                if api_key:
                    # If using Anthropic directly
                    try:
                        import anthropic
                        self.client = anthropic.Anthropic(api_key=api_key)
                        self.client_type = "anthropic"
                        self.log("INFO", "GenAI", "Initialized Anthropic client")
                    except ImportError:
                        # Fall back to OpenAI-compatible endpoint
                        self.client = OpenAI()
                        self.client_type = "openai"
                        self.log("INFO", "GenAI", "Initialized OpenAI-compatible client")
                else:
                    # Use default OpenAI-compatible endpoint
                    self.client = OpenAI()
                    self.client_type = "openai"
                    self.log("INFO", "GenAI", "Initialized OpenAI-compatible client (default)")
                    
        except Exception as e:
            self.log("ERROR", "GenAI", f"Failed to initialize client: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if GenAI is available and configured."""
        return self.config.enabled and self.client is not None
    
    def parse_natural_language_rule(self, nl_rule: str, rule_type: str = "reconciliation",
                                    context: Optional[Dict] = None) -> Optional[Dict]:
        """
        Convert a natural language rule description to structured DSL format.
        
        Args:
            nl_rule: Natural language rule description
            rule_type: Type of rule ('reconciliation' or 'validation')
            context: Optional context about available columns and data sources
            
        Returns:
            Structured rule dictionary or None if parsing fails
        """
        if not self.is_available():
            self.log("WARNING", "GenAI", "GenAI not available for rule parsing")
            return None
        
        # Build the prompt
        if rule_type == "reconciliation":
            schema_description = """
            {
                "rule_id": "auto-generated",
                "rule_name": "descriptive name",
                "active": "TRUE",
                "source1": "source1_filename.csv",
                "source2": "source2_filename.csv",
                "key_column_s1": "column name for matching in source 1",
                "key_column_s2": "column name for matching in source 2",
                "check_type": "one of: key_match, value_equals, fuzzy_match, aggregate_sum, aggregate_count, aggregate_avg",
                "compare_column_s1": "column to compare in source 1 (if applicable)",
                "compare_column_s2": "column to compare in source 2 (if applicable)",
                "tolerance": "numeric tolerance value (if applicable)",
                "tolerance_type": "one of: percentage, absolute, days, similarity_score",
                "description": "human-readable description"
            }
            """
        else:
            schema_description = """
            {
                "rule_id": "auto-generated",
                "rule_name": "descriptive name",
                "active": "TRUE",
                "data_source": "filename.csv",
                "column": "column name to validate",
                "check_type": "one of: not_null, not_empty, greater_than, less_than, between, equals, is_in_list, regex_match, is_date, is_numeric, unique",
                "parameter_1": "first parameter (threshold, pattern, list, etc.)",
                "parameter_2": "second parameter (for 'between' check)",
                "severity": "one of: ERROR, WARNING, INFO",
                "description": "human-readable description"
            }
            """
        
        context_str = ""
        if context:
            context_str = f"\n\nAvailable context:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""You are a data quality expert. Convert the following natural language rule into a structured JSON format.

Rule Type: {rule_type}
Natural Language Rule: "{nl_rule}"

Expected JSON Schema:
{schema_description}
{context_str}

Return ONLY the JSON object, no explanation or markdown formatting."""

        try:
            response = self._call_api(prompt)
            if response:
                # Parse JSON from response
                # Clean up response if it contains markdown code blocks
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                
                return json.loads(response)
        except json.JSONDecodeError as e:
            self.log("ERROR", "GenAI", f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.log("ERROR", "GenAI", f"Error in rule parsing: {e}")
        
        return None
    
    def suggest_validation_rules(self, df_profile: Dict, column_name: str) -> List[Dict]:
        """
        Suggest validation rules based on data profiling results.
        
        Args:
            df_profile: Data profile dictionary containing statistics
            column_name: Name of the column to suggest rules for
            
        Returns:
            List of suggested rule dictionaries
        """
        if not self.is_available():
            return []
        
        prompt = f"""You are a data quality expert. Based on the following data profile for column '{column_name}', 
suggest appropriate validation rules.

Data Profile:
{json.dumps(df_profile, indent=2)}

Return a JSON array of validation rules. Each rule should follow this schema:
{{
    "rule_name": "descriptive name",
    "check_type": "validation check type",
    "parameter_1": "parameter if needed",
    "parameter_2": "second parameter if needed",
    "severity": "ERROR or WARNING",
    "rationale": "why this rule is suggested"
}}

Return ONLY the JSON array, no explanation."""

        try:
            response = self._call_api(prompt)
            if response:
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                return json.loads(response)
        except Exception as e:
            self.log("ERROR", "GenAI", f"Error suggesting rules: {e}")
        
        return []
    
    def explain_discrepancy(self, discrepancy: Dict, context: Optional[Dict] = None) -> str:
        """
        Generate a human-readable explanation for a reconciliation discrepancy.
        
        Args:
            discrepancy: Discrepancy details dictionary
            context: Optional additional context
            
        Returns:
            Human-readable explanation string
        """
        if not self.is_available():
            return "GenAI explanation not available."
        
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""You are a data reconciliation expert. Explain the following discrepancy in plain English,
including possible causes and recommended actions.

Discrepancy Details:
{json.dumps(discrepancy, indent=2)}
{context_str}

Provide a concise explanation (2-3 sentences) focusing on:
1. What the discrepancy means
2. Possible causes
3. Recommended action"""

        try:
            response = self._call_api(prompt)
            return response if response else "Unable to generate explanation."
        except Exception as e:
            self.log("ERROR", "GenAI", f"Error explaining discrepancy: {e}")
            return f"Error generating explanation: {e}"
    
    def generate_rule_documentation(self, rules: List[Dict], rule_type: str) -> str:
        """
        Generate documentation for a set of rules.
        
        Args:
            rules: List of rule dictionaries
            rule_type: Type of rules ('reconciliation' or 'validation')
            
        Returns:
            Markdown-formatted documentation string
        """
        if not self.is_available():
            return self._generate_basic_documentation(rules, rule_type)
        
        prompt = f"""You are a technical writer. Generate clear, professional documentation for the following {rule_type} rules.

Rules:
{json.dumps(rules, indent=2)}

Generate Markdown documentation that includes:
1. Overview section
2. Table summarizing all rules
3. Detailed explanation of each rule
4. Usage notes

Keep the documentation concise but comprehensive."""

        try:
            response = self._call_api(prompt)
            return response if response else self._generate_basic_documentation(rules, rule_type)
        except Exception as e:
            self.log("ERROR", "GenAI", f"Error generating documentation: {e}")
            return self._generate_basic_documentation(rules, rule_type)
    
    def _generate_basic_documentation(self, rules: List[Dict], rule_type: str) -> str:
        """Generate basic documentation without GenAI."""
        doc = f"# {rule_type.title()} Rules Documentation\n\n"
        doc += f"Total Rules: {len(rules)}\n\n"
        doc += "## Rules Summary\n\n"
        doc += "| Rule ID | Rule Name | Check Type | Status |\n"
        doc += "|---------|-----------|------------|--------|\n"
        
        for rule in rules:
            rule_id = rule.get("rule_id", "N/A")
            rule_name = rule.get("rule_name", "N/A")
            check_type = rule.get("check_type", "N/A")
            active = rule.get("active", "TRUE")
            doc += f"| {rule_id} | {rule_name} | {check_type} | {active} |\n"
        
        return doc
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """
        Make an API call to the configured GenAI provider.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text or None
        """
        if not self.client:
            return None
        
        try:
            if self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            else:
                # OpenAI-compatible API
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",  # Use available model
                    messages=[
                        {"role": "system", "content": "You are a helpful data quality and reconciliation expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.3
                )
                return response.choices[0].message.content
                
        except Exception as e:
            self.log("ERROR", "GenAI", f"API call failed: {e}")
            return None


def profile_dataframe(df, column_name: str) -> Dict:
    """
    Generate a profile of a DataFrame column for rule suggestion.
    
    Args:
        df: pandas DataFrame
        column_name: Name of column to profile
        
    Returns:
        Dictionary containing profile statistics
    """
    import pandas as pd
    import numpy as np
    
    col = df[column_name]
    profile = {
        "column_name": column_name,
        "dtype": str(col.dtype),
        "total_count": len(col),
        "null_count": int(col.isna().sum()),
        "null_percentage": round(col.isna().sum() / len(col) * 100, 2),
        "unique_count": int(col.nunique()),
        "unique_percentage": round(col.nunique() / len(col) * 100, 2),
    }
    
    # Add numeric statistics if applicable
    if pd.api.types.is_numeric_dtype(col):
        profile["is_numeric"] = True
        profile["min"] = float(col.min()) if not col.isna().all() else None
        profile["max"] = float(col.max()) if not col.isna().all() else None
        profile["mean"] = float(col.mean()) if not col.isna().all() else None
        profile["median"] = float(col.median()) if not col.isna().all() else None
        profile["std"] = float(col.std()) if not col.isna().all() else None
        
        # Check for negative values
        profile["has_negatives"] = bool((col < 0).any())
        
        # Check if values appear to be percentages
        if profile["min"] is not None and profile["max"] is not None:
            profile["appears_percentage"] = profile["min"] >= 0 and profile["max"] <= 100
    else:
        profile["is_numeric"] = False
        
        # String statistics
        non_null = col.dropna().astype(str)
        if len(non_null) > 0:
            profile["min_length"] = int(non_null.str.len().min())
            profile["max_length"] = int(non_null.str.len().max())
            profile["avg_length"] = round(non_null.str.len().mean(), 2)
            
            # Sample values
            profile["sample_values"] = non_null.head(5).tolist()
            
            # Check for common patterns
            profile["has_empty_strings"] = bool((non_null == "").any())
    
    return profile
