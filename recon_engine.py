"""
Reconciliation Engine Module

This module contains the core logic for performing reconciliation checks
between two data sources based on rules defined in the configuration.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
import re


@dataclass
class ReconciliationResult:
    """Data class to store a single reconciliation result."""
    rule_id: str
    rule_name: str
    record_key: str
    source1_value: Any
    source2_value: Any
    difference: Any
    status: str  # PASS, FAIL, WARNING
    severity: str
    details: str


@dataclass
class ReconciliationSummary:
    """Data class to store reconciliation summary statistics."""
    total_records_source1: int = 0
    total_records_source2: int = 0
    matched_records: int = 0
    unmatched_source1: int = 0
    unmatched_source2: int = 0
    value_discrepancies: int = 0
    rules_executed: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    results: List[ReconciliationResult] = field(default_factory=list)


class ReconciliationEngine:
    """
    Core engine for performing reconciliation checks between data sources.
    """
    
    def __init__(self, config: Dict, logger=None):
        """
        Initialize the reconciliation engine.
        
        Args:
            config: Configuration dictionary from Excel config sheet
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.data_sources: Dict[str, pd.DataFrame] = {}
        self.column_mappings: Dict[str, Dict[str, str]] = {}
        self.summary = ReconciliationSummary()
        
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
        self.log("INFO", "DataLoader", f"Loading data source: {name} from {path}")
        
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
    
    def set_column_mappings(self, mappings: List[Dict]) -> None:
        """
        Set column mappings between sources.
        
        Args:
            mappings: List of mapping dictionaries with source1_col and source2_col
        """
        for mapping in mappings:
            mapping_id = mapping.get("mapping_id", "")
            s1_col = mapping.get("source1_column", "")
            s2_col = mapping.get("source2_column", "")
            if s1_col and s2_col:
                self.column_mappings[s1_col] = {"source2": s2_col, "id": mapping_id}
                self.log("DEBUG", "Mappings", f"Mapped {s1_col} -> {s2_col}")
    
    def get_mapped_column(self, source1_col: str) -> str:
        """Get the corresponding source2 column for a source1 column."""
        if source1_col in self.column_mappings:
            return self.column_mappings[source1_col]["source2"]
        return source1_col
    
    def execute_rule(self, rule: Dict) -> List[ReconciliationResult]:
        """
        Execute a single reconciliation rule.
        
        Args:
            rule: Rule dictionary containing rule parameters
            
        Returns:
            List of ReconciliationResult objects
        """
        rule_id = rule.get("rule_id", "UNKNOWN")
        rule_name = rule.get("rule_name", "Unnamed Rule")
        check_type_raw = rule.get("check_type", "")
        check_type = str(check_type_raw).lower() if pd.notna(check_type_raw) else ""
        
        self.log("INFO", "RuleEngine", f"Executing rule {rule_id}: {rule_name}")
        
        results = []
        
        try:
            if check_type == "key_match":
                results = self._check_key_match(rule)
            elif check_type == "value_equals":
                results = self._check_value_equals(rule)
            elif check_type == "fuzzy_match":
                results = self._check_fuzzy_match(rule)
            elif check_type == "aggregate_sum":
                results = self._check_aggregate_sum(rule)
            elif check_type == "aggregate_count":
                results = self._check_aggregate_count(rule)
            elif check_type == "aggregate_avg":
                results = self._check_aggregate_avg(rule)
            else:
                self.log("WARNING", "RuleEngine", f"Unknown check type: {check_type}")
                results = [ReconciliationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key="N/A",
                    source1_value="N/A",
                    source2_value="N/A",
                    difference="N/A",
                    status="SKIP",
                    severity="WARNING",
                    details=f"Unknown check type: {check_type}"
                )]
            
            self.summary.rules_executed += 1
            
        except Exception as e:
            self.log("ERROR", "RuleEngine", f"Error executing rule {rule_id}: {str(e)}")
            results = [ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key="N/A",
                source1_value="N/A",
                source2_value="N/A",
                difference="N/A",
                status="ERROR",
                severity="ERROR",
                details=f"Execution error: {str(e)}"
            )]
        
        return results
    
    def _check_key_match(self, rule: Dict) -> List[ReconciliationResult]:
        """Check that keys exist in both sources."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        key1 = str(rule.get("key_column_s1", "") or "")
        key2 = str(rule.get("key_column_s2", "") or "")
        
        # Get data sources
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        # Verify key columns exist
        if key1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if key2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        
        # Get keys from both sources
        keys1 = set(df1[key1].astype(str).unique())
        keys2 = set(df2[key2].astype(str).unique())
        
        # Find unmatched keys
        only_in_source1 = keys1 - keys2
        only_in_source2 = keys2 - keys1
        matched = keys1 & keys2
        
        self.summary.total_records_source1 = len(df1)
        self.summary.total_records_source2 = len(df2)
        self.summary.matched_records = len(matched)
        self.summary.unmatched_source1 = len(only_in_source1)
        self.summary.unmatched_source2 = len(only_in_source2)
        
        # Report unmatched in source1
        for key in only_in_source1:
            results.append(ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key=str(key),
                source1_value="EXISTS",
                source2_value="MISSING",
                difference="Missing in Source 2",
                status="FAIL",
                severity="ERROR",
                details=f"Record with key '{key}' exists in Source 1 but not in Source 2"
            ))
        
        # Report unmatched in source2
        for key in only_in_source2:
            results.append(ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key=str(key),
                source1_value="MISSING",
                source2_value="EXISTS",
                difference="Missing in Source 1",
                status="FAIL",
                severity="ERROR",
                details=f"Record with key '{key}' exists in Source 2 but not in Source 1"
            ))
        
        if not results:
            results.append(ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key="ALL",
                source1_value=str(len(keys1)),
                source2_value=str(len(keys2)),
                difference="0",
                status="PASS",
                severity="INFO",
                details=f"All {len(matched)} keys matched between sources"
            ))
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return results
    
    def _check_value_equals(self, rule: Dict) -> List[ReconciliationResult]:
        """Check that values match between sources for matched keys."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        key1 = str(rule.get("key_column_s1", "") or "")
        key2 = str(rule.get("key_column_s2", "") or "")
        col1 = str(rule.get("compare_column_s1", "") or "")
        col2 = str(rule.get("compare_column_s2", "") or "")
        tolerance_raw = rule.get("tolerance", "")
        tolerance = str(tolerance_raw) if pd.notna(tolerance_raw) else ""
        tolerance_type_raw = rule.get("tolerance_type", "")
        tolerance_type = str(tolerance_type_raw).lower() if pd.notna(tolerance_type_raw) else ""
        
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        # Verify columns exist in dataframes
        if key1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if key2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        if col1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Compare column '{col1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if col2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Compare column '{col2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        
        # Merge on keys
        merged = pd.merge(
            df1[[key1, col1]].rename(columns={key1: 'key', col1: 'val1'}),
            df2[[key2, col2]].rename(columns={key2: 'key', col2: 'val2'}),
            on='key',
            how='inner'
        )
        
        discrepancy_count = 0
        
        for _, row in merged.iterrows():
            val1 = row['val1']
            val2 = row['val2']
            key = row['key']
            
            is_match, diff = self._compare_values(val1, val2, tolerance, tolerance_type)
            
            if not is_match:
                discrepancy_count += 1
                results.append(ReconciliationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=str(key),
                    source1_value=str(val1),
                    source2_value=str(val2),
                    difference=str(diff),
                    status="FAIL",
                    severity="ERROR",
                    details=f"Value mismatch for {col1}/{col2}: {val1} vs {val2}"
                ))
        
        self.summary.value_discrepancies += discrepancy_count
        
        if not results:
            results.append(ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key="ALL",
                source1_value=f"{len(merged)} values",
                source2_value=f"{len(merged)} values",
                difference="0",
                status="PASS",
                severity="INFO",
                details=f"All {len(merged)} values matched within tolerance"
            ))
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return results
    
    def _check_fuzzy_match(self, rule: Dict) -> List[ReconciliationResult]:
        """Check text values with fuzzy matching."""
        results = []
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        key1 = str(rule.get("key_column_s1", "") or "")
        key2 = str(rule.get("key_column_s2", "") or "")
        col1 = str(rule.get("compare_column_s1", "") or "")
        col2 = str(rule.get("compare_column_s2", "") or "")
        tolerance_raw = rule.get("tolerance", 80)
        threshold = float(tolerance_raw if pd.notna(tolerance_raw) else 80) / 100  # Convert to 0-1 scale
        
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        # Verify columns exist in dataframes
        if key1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if key2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Key column '{key2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        if col1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Compare column '{col1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if col2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Compare column '{col2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        
        # Merge on keys
        merged = pd.merge(
            df1[[key1, col1]].rename(columns={key1: 'key', col1: 'val1'}),
            df2[[key2, col2]].rename(columns={key2: 'key', col2: 'val2'}),
            on='key',
            how='inner'
        )
        
        for _, row in merged.iterrows():
            val1 = str(row['val1']).lower()
            val2 = str(row['val2']).lower()
            key = row['key']
            
            similarity = SequenceMatcher(None, val1, val2).ratio()
            
            if similarity < threshold:
                results.append(ReconciliationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    record_key=str(key),
                    source1_value=str(row['val1']),
                    source2_value=str(row['val2']),
                    difference=f"{similarity*100:.1f}%",
                    status="FAIL",
                    severity="WARNING",
                    details=f"Fuzzy match below threshold ({similarity*100:.1f}% < {threshold*100:.0f}%)"
                ))
        
        if not results:
            results.append(ReconciliationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                record_key="ALL",
                source1_value=f"{len(merged)} values",
                source2_value=f"{len(merged)} values",
                difference="N/A",
                status="PASS",
                severity="INFO",
                details=f"All {len(merged)} text values matched within similarity threshold"
            ))
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return results
    
    def _check_aggregate_sum(self, rule: Dict) -> List[ReconciliationResult]:
        """Check that sums match between sources."""
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        col1 = str(rule.get("compare_column_s1", "") or "")
        col2 = str(rule.get("compare_column_s2", "") or "")
        tolerance_raw = rule.get("tolerance", "0")
        tolerance = str(tolerance_raw) if pd.notna(tolerance_raw) else "0"
        tolerance_type_raw = rule.get("tolerance_type", "percentage")
        tolerance_type = str(tolerance_type_raw) if pd.notna(tolerance_type_raw) else "percentage"
        
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        # Verify columns exist
        if col1 not in df1.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Column '{col1}' not found in Source 1. Available: {list(df1.columns)}"
            )]
        if col2 not in df2.columns:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details=f"Column '{col2}' not found in Source 2. Available: {list(df2.columns)}"
            )]
        
        sum1 = df1[col1].sum()
        sum2 = df2[col2].sum()
        
        is_match, diff = self._compare_values(sum1, sum2, tolerance, tolerance_type)
        
        status = "PASS" if is_match else "FAIL"
        if is_match:
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return [ReconciliationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            record_key="AGGREGATE_SUM",
            source1_value=f"{sum1:,.2f}",
            source2_value=f"{sum2:,.2f}",
            difference=f"{diff:,.2f}" if isinstance(diff, (int, float)) else str(diff),
            status=status,
            severity="ERROR" if not is_match else "INFO",
            details=f"Sum comparison: {col1}={sum1:,.2f} vs {col2}={sum2:,.2f}"
        )]
    
    def _check_aggregate_count(self, rule: Dict) -> List[ReconciliationResult]:
        """Check that record counts match between sources."""
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        count1 = len(df1)
        count2 = len(df2)
        diff = count1 - count2
        
        status = "PASS" if diff == 0 else "FAIL"
        if status == "PASS":
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return [ReconciliationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            record_key="AGGREGATE_COUNT",
            source1_value=str(count1),
            source2_value=str(count2),
            difference=str(diff),
            status=status,
            severity="WARNING" if diff != 0 else "INFO",
            details=f"Record count: Source1={count1}, Source2={count2}, Difference={diff}"
        )]
    
    def _check_aggregate_avg(self, rule: Dict) -> List[ReconciliationResult]:
        """Check that averages match between sources."""
        rule_id = rule.get("rule_id")
        rule_name = rule.get("rule_name")
        
        source1_name = str(rule.get("source1", "") or "").replace(".csv", "")
        source2_name = str(rule.get("source2", "") or "").replace(".csv", "")
        col1 = str(rule.get("compare_column_s1", "") or "")
        col2 = str(rule.get("compare_column_s2", "") or "")
        tolerance_raw = rule.get("tolerance", "0")
        tolerance = str(tolerance_raw) if pd.notna(tolerance_raw) else "0"
        tolerance_type_raw = rule.get("tolerance_type", "percentage")
        tolerance_type = str(tolerance_type_raw) if pd.notna(tolerance_type_raw) else "percentage"
        
        df1 = self._get_source_by_name(source1_name)
        df2 = self._get_source_by_name(source2_name)
        
        if df1 is None or df2 is None:
            return [ReconciliationResult(
                rule_id=rule_id, rule_name=rule_name, record_key="N/A",
                source1_value="N/A", source2_value="N/A", difference="N/A",
                status="ERROR", severity="ERROR",
                details="Could not find one or both data sources"
            )]
        
        avg1 = df1[col1].mean()
        avg2 = df2[col2].mean()
        
        is_match, diff = self._compare_values(avg1, avg2, tolerance, tolerance_type)
        
        status = "PASS" if is_match else "FAIL"
        if is_match:
            self.summary.rules_passed += 1
        else:
            self.summary.rules_failed += 1
        
        return [ReconciliationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            record_key="AGGREGATE_AVG",
            source1_value=f"{avg1:,.2f}",
            source2_value=f"{avg2:,.2f}",
            difference=f"{diff:,.2f}" if isinstance(diff, (int, float)) else str(diff),
            status=status,
            severity="ERROR" if not is_match else "INFO",
            details=f"Average comparison: {col1}={avg1:,.2f} vs {col2}={avg2:,.2f}"
        )]
    
    def _get_source_by_name(self, name: str) -> Optional[pd.DataFrame]:
        """Get a data source by partial name match."""
        name_lower = name.lower().replace(".csv", "").replace("_", "")
        for key, df in self.data_sources.items():
            key_lower = key.lower().replace("_", "")
            if name_lower in key_lower or key_lower in name_lower:
                return df
        # Also try matching by source1/source2 pattern
        if "source1" in name_lower or "1" in name_lower:
            if "source1" in self.data_sources:
                return self.data_sources["source1"]
        if "source2" in name_lower or "2" in name_lower:
            if "source2" in self.data_sources:
                return self.data_sources["source2"]
        return None
    
    def _compare_values(self, val1: Any, val2: Any, tolerance: str, 
                       tolerance_type: str) -> Tuple[bool, Any]:
        """
        Compare two values with optional tolerance.
        
        Returns:
            Tuple of (is_match, difference)
        """
        # Handle None/NaN
        if pd.isna(val1) and pd.isna(val2):
            return True, 0
        if pd.isna(val1) or pd.isna(val2):
            return False, "NULL mismatch"
        
        # Try numeric comparison
        try:
            num1 = float(val1)
            num2 = float(val2)
            diff = abs(num1 - num2)
            
            if tolerance and tolerance_type:
                tol = float(tolerance)
                if tolerance_type == "percentage":
                    # Tolerance as percentage
                    if num1 != 0:
                        pct_diff = (diff / abs(num1)) * 100
                        return pct_diff <= tol, diff
                    else:
                        return diff == 0, diff
                elif tolerance_type == "absolute":
                    return diff <= tol, diff
                elif tolerance_type == "days":
                    # For date comparison (assuming values are already dates or can be parsed)
                    return diff <= tol, diff
            
            return num1 == num2, diff
            
        except (ValueError, TypeError):
            # String comparison
            str1 = str(val1).strip()
            str2 = str(val2).strip()
            return str1 == str2, "String mismatch" if str1 != str2 else 0
    
    def run_all_rules(self, rules: List[Dict]) -> ReconciliationSummary:
        """
        Execute all reconciliation rules.
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            ReconciliationSummary with all results
        """
        self.log("INFO", "Engine", f"Starting reconciliation with {len(rules)} rules")
        
        for rule in rules:
            if str(rule.get("active", "TRUE")).upper() == "TRUE":
                results = self.execute_rule(rule)
                self.summary.results.extend(results)
            else:
                self.log("INFO", "Engine", f"Skipping inactive rule: {rule.get('rule_id')}")
        
        self.log("INFO", "Engine", 
                f"Reconciliation complete: {self.summary.rules_passed} passed, "
                f"{self.summary.rules_failed} failed")
        
        return self.summary
