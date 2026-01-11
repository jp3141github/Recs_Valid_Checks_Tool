"""
Validation Engine Module

This module contains the core logic for performing data validation checks
on individual data sources based on rules defined in the configuration.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class ValidationResult:
    """Data class to store a single validation result."""
    rule_id: str
    rule_name: str
    record_key: str
    column: str
    value: Any
    expected: str
    status: str  # PASS, FAIL, WARNING
    severity: str
    details: str


@dataclass
class ValidationSummary:
    """Data class to store validation summary statistics."""
    total_records: int = 0
    records_passed: int = 0
    records_with_errors: int = 0
    records_with_warnings: int = 0
    rules_executed: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    results: List[ValidationResult] = field(default_factory=list)


class ValidationEngine:
    """
    Core engine for performing data validation checks on a single data source.
    """
    
    def __init__(self, config: Dict, logger=None):
        """
        Initialize the validation engine.
        
        Args:
            config: Configuration dictionary from Excel config sheet
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.data_sources: Dict[str, pd.DataFrame] = {}
        self.summary = ValidationSummary()
        
        # Register validation check functions
        self.check_functions: Dict[str, Callable] = {
            "not_null": self._check_not_null,
            "not_empty": self._check_not_empty,
            "greater_than": self._check_greater_than,
            "less_than": self._check_less_than,
            "between": self._check_between,
            "equals": self._check_equals,
            "not_equals": self._check_not_equals,
            "is_in_list": self._check_is_in_list,
            "not_in_list": self._check_not_in_list,
            "regex_match": self._check_regex_match,
            "is_date": self._check_is_date,
            "is_numeric": self._check_is_numeric,
            "is_integer": self._check_is_integer,
            "unique": self._check_unique,
            "min_length": self._check_min_length,
            "max_length": self._check_max_length,
            "starts_with": self._check_starts_with,
            "ends_with": self._check_ends_with,
            "contains": self._check_contains,
        }
    
    def log(self, level: str, component: str, message: str):
        """Log a message if logger is available."""
        if self.logger:
            self.logger.log(level, component, message)
    
    def load_data_source(self, name: str, path: str, file_type: str = "CSV",
                         encoding: str = "utf-8", delimiter: str = ",") -> pd.DataFrame:
        """
        Load a data source from file.
        
        Args:
            name: Name identifier for the data source
            path: File path to the data source
            file_type: Type of file (CSV, Excel)
            encoding: File encoding
            delimiter: Delimiter for CSV files
            
        Returns:
            Loaded DataFrame
        """
        self.log("INFO", "DataLoader", f"Loading validation data: {name} from {path}")
        
        try:
            if file_type.upper() == "CSV":
                df = pd.read_csv(path, encoding=encoding, delimiter=delimiter)
            elif file_type.upper() in ["EXCEL", "XLSX", "XLS"]:
                df = pd.read_excel(path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            self.data_sources[name] = df
            self.log("INFO", "DataLoader", f"Loaded {len(df)} records from {name}")
            return df
            
        except Exception as e:
            self.log("ERROR", "DataLoader", f"Failed to load {name}: {str(e)}")
            raise
    
    def execute_rule(self, rule: Dict) -> List[ValidationResult]:
        """
        Execute a single validation rule.
        
        Args:
            rule: Rule dictionary containing rule parameters
            
        Returns:
            List of ValidationResult objects
        """
        rule_id = rule.get("rule_id", "UNKNOWN")
        rule_name = rule.get("rule_name", "Unnamed Rule")
        check_type = rule.get("check_type", "").lower()
        
        self.log("INFO", "ValidationEngine", f"Executing rule {rule_id}: {rule_name}")
        
        results = []
        
        try:
            if check_type in self.check_functions:
                results = self.check_functions[check_type](rule)
            else:
                self.log("WARNING", "ValidationEngine", f"Unknown check type: {check_type}")
                results = [ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key="N/A",
                    column="N/A",
                    value="N/A",
                    expected="N/A",
                    status="SKIP",
                    severity="WARNING",
                    details=f"Unknown check type: {check_type}"
                )]
            
            self.summary.rules_executed += 1
            
        except Exception as e:
            self.log("ERROR", "ValidationEngine", f"Error executing rule {rule_id}: {str(e)}")
            results = [ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key="N/A",
                column="N/A",
                value="N/A",
                expected="N/A",
                status="ERROR",
                severity="ERROR",
                details=f"Execution error: {str(e)}"
            )]
        
        return results
    
    def _get_source_by_name(self, name: str) -> Optional[pd.DataFrame]:
        """Get a data source by partial name match."""
        for key, df in self.data_sources.items():
            if name.lower().replace(".csv", "") in key.lower():
                return df
        return None
    
    def _get_record_key(self, df: pd.DataFrame, idx: int) -> str:
        """Get a record key for identification."""
        # Try common key column names
        for col in ['record_id', 'id', 'transaction_id', 'key']:
            if col in df.columns:
                return str(df.iloc[idx][col])
        return f"Row_{idx + 1}"
    
    def _check_not_null(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are not null/None."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        null_mask = df[column].isna()
        fail_count = 0
        
        for idx in df[null_mask].index:
            fail_count += 1
            results.append(ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key=self._get_record_key(df, idx),
                column=column,
                value="NULL",
                expected="NOT NULL",
                status="FAIL",
                severity=severity,
                details=f"Value is null/None in column '{column}'"
            ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_not_empty(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values are not empty."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.isna(value) or str(value).strip() == "":
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value) if not pd.isna(value) else "NULL",
                    expected="NOT EMPTY",
                    status="FAIL",
                    severity=severity,
                    details=f"Value is empty in column '{column}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_greater_than(self, rule: Dict) -> List[ValidationResult]:
        """Check that numeric values are greater than a threshold."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        threshold = float(rule.get("parameter_1", 0))
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            try:
                if pd.notna(value) and float(value) <= threshold:
                    results.append(ValidationResult(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        record_key=self._get_record_key(df, idx),
                        column=column,
                        value=str(value),
                        expected=f"> {threshold}",
                        status="FAIL",
                        severity=severity,
                        details=f"Value {value} is not greater than {threshold}"
                    ))
            except (ValueError, TypeError):
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"> {threshold}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' is not numeric"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_less_than(self, rule: Dict) -> List[ValidationResult]:
        """Check that numeric values are less than a threshold."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        threshold = float(rule.get("parameter_1", 0))
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            try:
                if pd.notna(value) and float(value) >= threshold:
                    results.append(ValidationResult(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        record_key=self._get_record_key(df, idx),
                        column=column,
                        value=str(value),
                        expected=f"< {threshold}",
                        status="FAIL",
                        severity=severity,
                        details=f"Value {value} is not less than {threshold}"
                    ))
            except (ValueError, TypeError):
                pass
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_between(self, rule: Dict) -> List[ValidationResult]:
        """Check that numeric values are between min and max."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        min_val = float(rule.get("parameter_1", 0))
        max_val = float(rule.get("parameter_2", 100))
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            try:
                if pd.notna(value):
                    num_val = float(value)
                    if num_val < min_val or num_val > max_val:
                        results.append(ValidationResult(
                            rule_id=rule_id,
                            rule_name=rule_name,
                            record_key=self._get_record_key(df, idx),
                            column=column,
                            value=str(value),
                            expected=f"[{min_val}, {max_val}]",
                            status="FAIL",
                            severity=severity,
                            details=f"Value {value} is not between {min_val} and {max_val}"
                        ))
            except (ValueError, TypeError):
                pass
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_equals(self, rule: Dict) -> List[ValidationResult]:
        """Check that values equal an expected value."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        expected = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if str(value).strip() != str(expected).strip():
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=str(expected),
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' does not equal '{expected}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_not_equals(self, rule: Dict) -> List[ValidationResult]:
        """Check that values do not equal a specific value."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        forbidden = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if str(value).strip() == str(forbidden).strip():
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"NOT '{forbidden}'",
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' equals forbidden value '{forbidden}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_is_in_list(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are in a valid list."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        valid_list = [v.strip() for v in str(rule.get("parameter_1", "")).split(",")]
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and str(value).strip() not in valid_list:
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"One of: {valid_list}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' is not in valid list"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_not_in_list(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are not in a forbidden list."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        forbidden_list = [v.strip() for v in str(rule.get("parameter_1", "")).split(",")]
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and str(value).strip() in forbidden_list:
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Not one of: {forbidden_list}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' is in forbidden list"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_regex_match(self, rule: Dict) -> List[ValidationResult]:
        """Check that values match a regex pattern."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        pattern = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return [self._error_result(rule_id, rule_name, f"Invalid regex: {e}")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and not regex.match(str(value)):
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Match pattern: {pattern}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value '{value}' does not match pattern"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_is_date(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are valid dates."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        date_format = rule.get("parameter_1", "%Y-%m-%d")
        severity = rule.get("severity", "ERROR")
        
        # Convert format string
        format_map = {
            "YYYY-MM-DD": "%Y-%m-%d",
            "MM/DD/YYYY": "%m/%d/%Y",
            "DD/MM/YYYY": "%d/%m/%Y",
            "YYYY/MM/DD": "%Y/%m/%d",
        }
        py_format = format_map.get(date_format, date_format)
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value):
                try:
                    datetime.strptime(str(value), py_format)
                except ValueError:
                    results.append(ValidationResult(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        record_key=self._get_record_key(df, idx),
                        column=column,
                        value=str(value),
                        expected=f"Valid date ({date_format})",
                        status="FAIL",
                        severity=severity,
                        details=f"Value '{value}' is not a valid date"
                    ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_is_numeric(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are numeric."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value):
                try:
                    float(value)
                except (ValueError, TypeError):
                    results.append(ValidationResult(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        record_key=self._get_record_key(df, idx),
                        column=column,
                        value=str(value),
                        expected="Numeric value",
                        status="FAIL",
                        severity=severity,
                        details=f"Value '{value}' is not numeric"
                    ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_is_integer(self, rule: Dict) -> List[ValidationResult]:
        """Check that values are integers."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value):
                try:
                    if float(value) != int(float(value)):
                        raise ValueError()
                except (ValueError, TypeError):
                    results.append(ValidationResult(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        record_key=self._get_record_key(df, idx),
                        column=column,
                        value=str(value),
                        expected="Integer value",
                        status="FAIL",
                        severity=severity,
                        details=f"Value '{value}' is not an integer"
                    ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_unique(self, rule: Dict) -> List[ValidationResult]:
        """Check that values in a column are unique."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        duplicates = df[df.duplicated(subset=[column], keep=False)]
        
        for idx, row in duplicates.iterrows():
            results.append(ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key=self._get_record_key(df, idx),
                column=column,
                value=str(row[column]),
                expected="Unique value",
                status="FAIL",
                severity=severity,
                details=f"Duplicate value '{row[column]}' found"
            ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_min_length(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values have minimum length."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        min_len = int(rule.get("parameter_1", 0))
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and len(str(value)) < min_len:
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Min length: {min_len}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value length {len(str(value))} is less than {min_len}"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_max_length(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values have maximum length."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        max_len = int(rule.get("parameter_1", 255))
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and len(str(value)) > max_len:
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value)[:50] + "...",
                    expected=f"Max length: {max_len}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value length {len(str(value))} exceeds {max_len}"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_starts_with(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values start with a prefix."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        prefix = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and not str(value).startswith(prefix):
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Starts with: {prefix}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value does not start with '{prefix}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_ends_with(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values end with a suffix."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        suffix = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and not str(value).endswith(suffix):
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Ends with: {suffix}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value does not end with '{suffix}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _check_contains(self, rule: Dict) -> List[ValidationResult]:
        """Check that string values contain a substring."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        source_name = rule.get("data_source", "")
        column = rule.get("column", "")
        substring = rule.get("parameter_1", "")
        severity = rule.get("severity", "ERROR")
        
        df = self._get_source_by_name(source_name)
        if df is None:
            return [self._error_result(rule_id, rule_name, "Data source not found")]
        
        for idx, row in df.iterrows():
            value = row[column]
            if pd.notna(value) and substring not in str(value):
                results.append(ValidationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=self._get_record_key(df, idx),
                    column=column,
                    value=str(value),
                    expected=f"Contains: {substring}",
                    status="FAIL",
                    severity=severity,
                    details=f"Value does not contain '{substring}'"
                ))
        
        self._update_summary(results, len(df), severity)
        return results if results else [self._pass_result(rule_id, rule_name, column, len(df))]
    
    def _error_result(self, rule_id: str, rule_name: str, message: str) -> ValidationResult:
        """Create an error result."""
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            record_key="N/A",
            column="N/A",
            value="N/A",
            expected="N/A",
            status="ERROR",
            severity="ERROR",
            details=message
        )
    
    def _pass_result(self, rule_id: str, rule_name: str, column: str, count: int) -> ValidationResult:
        """Create a pass result."""
        self.summary.rules_passed += 1
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            record_key="ALL",
            column=column,
            value=f"{count} values",
            expected="Valid",
            status="PASS",
            severity="INFO",
            details=f"All {count} records passed validation"
        )
    
    def _update_summary(self, results: List[ValidationResult], total: int, severity: str):
        """Update summary statistics based on results."""
        if results:
            self.summary.rules_failed += 1
            if severity == "ERROR":
                self.summary.records_with_errors += len(results)
            else:
                self.summary.records_with_warnings += len(results)
    
    def run_all_rules(self, rules: List[Dict]) -> ValidationSummary:
        """
        Execute all validation rules.
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            ValidationSummary with all results
        """
        self.log("INFO", "Engine", f"Starting validation with {len(rules)} rules")
        
        # Get total records from first data source
        if self.data_sources:
            first_source = list(self.data_sources.values())[0]
            self.summary.total_records = len(first_source)
        
        for rule in rules:
            if str(rule.get("active", "TRUE")).upper() == "TRUE":
                results = self.execute_rule(rule)
                self.summary.results.extend(results)
            else:
                self.log("INFO", "Engine", f"Skipping inactive rule: {rule.get('rule_id')}")
        
        # Calculate records passed
        failed_records = set()
        for result in self.summary.results:
            if result.status == "FAIL":
                failed_records.add(result.record_key)
        
        self.summary.records_passed = self.summary.total_records - len(failed_records)
        
        self.log("INFO", "Engine", 
                f"Validation complete: {self.summary.rules_passed} passed, "
                f"{self.summary.rules_failed} failed")
        
        return self.summary
