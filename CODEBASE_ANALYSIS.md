# Codebase Analysis: Reconciliation & Validation Checks Tool

**Document Version:** 1.0
**Generated:** January 13, 2026
**Total Codebase:** 2,598 lines across 4 core Python modules

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Modules](#core-modules)
   - [recon_tool.py](#1-recon_toolpy---main-orchestrator)
   - [recon_engine.py](#2-recon_enginepy---reconciliation-logic)
   - [validation_engine.py](#3-validation_enginepy---data-quality-validation)
   - [genai_helper.py](#4-genai_helperpy---optional-ai-integration)
4. [Data Flow](#data-flow)
5. [Configuration Format](#configuration-format)
6. [Output Sheets Reference](#output-sheets-reference)
7. [Algorithm Details](#algorithm-details)
8. [Usage Examples](#usage-examples)
9. [Dependencies](#dependencies)
10. [Executive Summary](#executive-summary-for-management)

---

## Overview

This is a **Python-based Data Quality Automation System** designed for enterprise reconciliation and validation operations. The tool compares data between sources (reconciliation) and validates data quality within single sources (validation), producing professionally formatted Excel reports.

### Key Statistics

| Metric | Value |
|--------|-------|
| Total Lines of Code | 2,598 |
| Core Modules | 4 |
| Reconciliation Check Types | 6 |
| Validation Check Types | 19 |
| Supported File Formats | CSV, XLSX, XLS |

---

## Architecture

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                     │
│                   Excel Config File (.xlsx)                           │
│                                                                       │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│   │   Config    │ │  Column     │ │   Recon     │ │ Validation  │   │
│   │   Sheet     │ │  Mappings   │ │   Rules     │ │   Rules     │   │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     recon_tool.py (ORCHESTRATOR)                      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  ReconTool Class                                                │  │
│  │  • load_configuration() - Parse Excel config                    │  │
│  │  • run_reconciliation() - Execute recon workflow                │  │
│  │  • run_validation() - Execute validation workflow               │  │
│  │  • generate_output() - Create formatted Excel report            │  │
│  │  • run() - Master orchestration method                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  ExecutionLog Class - Audit trail management                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         ▼                                           ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│   recon_engine.py       │             │  validation_engine.py   │
│   RECONCILIATION        │             │  VALIDATION             │
│                         │             │                         │
│   ReconciliationEngine  │             │   ValidationEngine      │
│   ├── key_match         │             │   ├── not_null          │
│   ├── value_equals      │             │   ├── not_empty         │
│   ├── fuzzy_match       │             │   ├── greater_than      │
│   ├── aggregate_sum     │             │   ├── less_than         │
│   ├── aggregate_count   │             │   ├── between           │
│   └── aggregate_avg     │             │   ├── equals            │
│                         │             │   ├── is_in_list        │
│   Tolerance Types:      │             │   ├── regex_match       │
│   • percentage          │             │   ├── is_date           │
│   • absolute            │             │   ├── is_numeric        │
│   • days                │             │   ├── unique            │
│                         │             │   └── ... (8 more)      │
└─────────────────────────┘             └─────────────────────────┘
         │                                           │
         └─────────────────────┬─────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 genai_helper.py (OPTIONAL)                            │
│                                                                       │
│   GenAIHelper Class                                                   │
│   • parse_natural_language_rule() - NL to DSL conversion             │
│   • suggest_validation_rules() - AI-powered rule suggestions         │
│   • explain_discrepancy() - Plain English explanations               │
│   • generate_rule_documentation() - Auto-generate docs               │
│                                                                       │
│   Supported Providers: Anthropic Claude, OpenAI-compatible APIs      │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    OUTPUT: Timestamped Excel Report                   │
│                    (e.g., project_20260113_143022.xlsx)               │
│                                                                       │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│   │ OutputSummary│ │ ReconResults │ │  Validation  │                │
│   │    Sheet     │ │    Sheet     │ │   Results    │                │
│   └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                       │
│   ┌──────────────┐ ┌──────────────┐                                  │
│   │ ExecutionLog │ │ Original     │                                  │
│   │    Sheet     │ │ Config Sheets│                                  │
│   └──────────────┘ └──────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
                    ┌─────────────────┐
                    │   User runs:    │
                    │ python recon_   │
                    │ tool.py cfg.xlsx│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Load Config     │
                    │ (4 Excel sheets)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Recon Rules     │          │ Validation Rules│
     │ defined?        │          │ defined?        │
     └────────┬────────┘          └────────┬────────┘
              │ YES                        │ YES
              ▼                            ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Load Source1    │          │ Load Data       │
     │ Load Source2    │          │ Source          │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              ▼                            ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Apply Column    │          │ Execute Each    │
     │ Mappings        │          │ Validation Rule │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              ▼                            ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Execute Each    │          │ Collect Results │
     │ Recon Rule      │          │ & Summaries     │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              └──────────────┬─────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Generate Output │
                    │ Excel Report    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Return Output   │
                    │ File Path       │
                    └─────────────────┘
```

---

## Core Modules

### 1. `recon_tool.py` - Main Orchestrator

**Lines:** 542
**Purpose:** Entry point that coordinates the entire workflow

#### Classes

| Class | Purpose |
|-------|---------|
| `ExecutionLog` | Dataclass storing timestamped log entries for audit trails |
| `ReconTool` | Main controller class that orchestrates all operations |

#### Critical Methods

| Method | Lines | Function |
|--------|-------|----------|
| `__init__()` | 45-70 | Initialize tool with optional GenAI config |
| `load_configuration()` | 86-153 | Parse Excel config with 4 sheets |
| `run_reconciliation()` | 165-212 | Load sources, apply mappings, execute rules |
| `run_validation()` | 214-259 | Load data, execute validation rules |
| `_load_data_source()` | 261-276 | Load CSV/Excel with encoding handling |
| `generate_output()` | 278-320 | Create formatted Excel report |
| `_apply_excel_formatting()` | 322-380 | Apply colors, borders, column widths |
| `run()` | 460-496 | Master workflow orchestrator |

#### Excel Formatting Constants (Lines 73-84)

```python
HEADER_FILL = PatternFill(start_color="4472C4", fill_type="solid")  # Blue
HEADER_FONT = Font(bold=True, color="FFFFFF")                        # White bold
PASS_FILL = PatternFill(start_color="C6EFCE", fill_type="solid")    # Green
FAIL_FILL = PatternFill(start_color="FFC7CE", fill_type="solid")    # Red
WARNING_FILL = PatternFill(start_color="FFEB9C", fill_type="solid") # Yellow
```

#### Execution Flow

```python
def run(self):
    """Master workflow execution."""
    # 1. Load configuration
    self.load_configuration()

    # 2. Run reconciliation if rules exist
    if self.recon_rules:
        self.run_reconciliation()

    # 3. Run validation if rules exist
    if self.validation_rules:
        self.run_validation()

    # 4. Generate output report
    output_path = self.generate_output()

    return output_path
```

---

### 2. `recon_engine.py` - Reconciliation Logic

**Lines:** 734
**Purpose:** Compares data between two sources to find discrepancies

#### Classes

| Class | Purpose |
|-------|---------|
| `ReconciliationResult` | Dataclass for individual comparison results |
| `ReconciliationSummary` | Aggregate statistics (matched/unmatched counts) |
| `ReconciliationEngine` | Core comparison logic with 6 check types |

#### Reconciliation Check Types

| Check Type | Method | Lines | Description | Use Case |
|------------|--------|-------|-------------|----------|
| `key_match` | `_check_key_match()` | 188-286 | Find records in one source but not the other | Missing transactions |
| `value_equals` | `_check_value_equals()` | 288-395 | Compare field values with optional tolerance | Amount mismatches |
| `fuzzy_match` | `_check_fuzzy_match()` | 397-497 | Text comparison using SequenceMatcher | Name variations |
| `aggregate_sum` | `_check_aggregate_sum()` | 499-561 | Compare total sums between sources | Balance verification |
| `aggregate_count` | `_check_aggregate_count()` | 563-602 | Compare record counts | Volume reconciliation |
| `aggregate_avg` | `_check_aggregate_avg()` | 604-650 | Compare average values | Rate verification |

#### Tolerance System

The `_compare_values()` method (Lines 668-709) supports three tolerance types:

```
┌─────────────────┬────────────────────────────────────────────────┐
│ Tolerance Type  │ Calculation                                    │
├─────────────────┼────────────────────────────────────────────────┤
│ percentage      │ |value1 - value2| / value1 <= tolerance/100   │
│ absolute        │ |value1 - value2| <= tolerance                │
│ days            │ |date1 - date2| in days <= tolerance          │
└─────────────────┴────────────────────────────────────────────────┘
```

#### Key Match Algorithm

```
Algorithm: key_match
─────────────────────────────────────────────────────────
INPUT:  Source1 DataFrame, Source2 DataFrame, Key Columns

STEP 1: Extract key values from Source1
        keys_s1 = set(Source1[key_column].values)

STEP 2: Extract key values from Source2
        keys_s2 = set(Source2[key_column].values)

STEP 3: Find matches
        matched = keys_s1 ∩ keys_s2

STEP 4: Find Source1-only records
        only_in_s1 = keys_s1 - keys_s2

STEP 5: Find Source2-only records
        only_in_s2 = keys_s2 - keys_s1

OUTPUT: ReconciliationResult with:
        - status: PASS if only_in_s1 and only_in_s2 are empty
        - matched_count, s1_only_count, s2_only_count
        - List of unmatched keys
─────────────────────────────────────────────────────────
```

#### Fuzzy Match Algorithm

```
Algorithm: fuzzy_match (using SequenceMatcher)
─────────────────────────────────────────────────────────
INPUT:  String1, String2, Threshold (default: 0.8)

STEP 1: Normalize strings
        s1 = String1.strip().lower()
        s2 = String2.strip().lower()

STEP 2: Calculate similarity ratio
        ratio = SequenceMatcher(None, s1, s2).ratio()

STEP 3: Compare to threshold
        IF ratio >= threshold:
            RETURN PASS (similarity_score = ratio)
        ELSE:
            RETURN FAIL (similarity_score = ratio)

OUTPUT: Match status and similarity score (0.0 to 1.0)
─────────────────────────────────────────────────────────
```

---

### 3. `validation_engine.py` - Data Quality Validation

**Lines:** 915
**Purpose:** Checks data quality within a single source against defined rules

#### Classes

| Class | Purpose |
|-------|---------|
| `ValidationResult` | Dataclass for individual validation check results |
| `ValidationSummary` | Aggregate pass/fail statistics |
| `ValidationEngine` | Core validation logic with 19 check types |

#### All 19 Validation Check Types

| Category | Check Type | Method | Lines | Purpose |
|----------|------------|--------|-------|---------|
| **Null/Empty** | `not_null` | `_check_not_null()` | 190-221 | Ensure values exist |
| | `not_empty` | `_check_not_empty()` | 223-252 | Ensure strings aren't blank |
| **Numeric Comparison** | `greater_than` | `_check_greater_than()` | 254-297 | Value > threshold |
| | `less_than` | `_check_less_than()` | 299-332 | Value < threshold |
| | `between` | `_check_between()` | 334-370 | Value within range |
| **Type Validation** | `is_numeric` | `_check_is_numeric()` | 581-613 | Verify numeric type |
| | `is_integer` | `_check_is_integer()` | 615-648 | Verify whole numbers |
| | `is_date` | `_check_is_date()` | 537-579 | Valid date format |
| **Equality** | `equals` | `_check_equals()` | 372-402 | Exact value match |
| | `not_equals` | `_check_not_equals()` | 404-434 | Value exclusion |
| **List Membership** | `is_in_list` | `_check_is_in_list()` | 436-466 | Value in allowed set |
| | `not_in_list` | `_check_not_in_list()` | 468-498 | Value not in forbidden set |
| **Pattern Matching** | `regex_match` | `_check_regex_match()` | 500-535 | Regular expression match |
| **Uniqueness** | `unique` | `_check_unique()` | 650-679 | No duplicates |
| **String Length** | `min_length` | `_check_min_length()` | 681-711 | Minimum character count |
| | `max_length` | `_check_max_length()` | 713-743 | Maximum character count |
| **String Content** | `starts_with` | `_check_starts_with()` | 745-775 | Prefix check |
| | `ends_with` | `_check_ends_with()` | 777-807 | Suffix check |
| | `contains` | `_check_contains()` | 809-839 | Substring check |

#### Severity Levels

```
┌──────────┬─────────────────────────────────────────────────────┐
│ Severity │ Use Case                                            │
├──────────┼─────────────────────────────────────────────────────┤
│ ERROR    │ Critical issues that must be fixed                  │
│ WARNING  │ Issues that should be reviewed but may be OK        │
│ INFO     │ Informational flags, no action required             │
└──────────┴─────────────────────────────────────────────────────┘
```

#### Record Identification Logic

The engine automatically identifies records using this priority (Lines 165-188):

```
1. Check for 'id' column
2. Check for 'record_id' column
3. Check for 'transaction_id' column
4. Fall back to row number (row_0, row_1, ...)
```

#### Validation Execution Algorithm

```
Algorithm: execute_validation
─────────────────────────────────────────────────────────
INPUT:  DataFrame, List of Rules

FOR EACH rule IN rules:
    IF rule.active == FALSE:
        SKIP rule

    column = rule.column
    check_type = rule.check_type

    # Get appropriate check method
    check_method = _get_check_method(check_type)

    FOR EACH row IN DataFrame:
        value = row[column]
        record_id = _get_record_id(row)

        result = check_method(value, rule.parameters)

        IF result.failed:
            ADD to failed_records:
                - record_id
                - column
                - value
                - expected
                - actual
                - message

    # Create summary
    summary = ValidationSummary(
        total_records = len(DataFrame),
        passed = total - failed,
        failed = len(failed_records),
        pass_rate = passed / total * 100
    )

OUTPUT: List[ValidationResult], List[ValidationSummary]
─────────────────────────────────────────────────────────
```

---

### 4. `genai_helper.py` - Optional AI Integration

**Lines:** 407
**Purpose:** Adds AI-powered features for enhanced automation

#### Classes

| Class | Purpose |
|-------|---------|
| `GenAIConfig` | Configuration dataclass (enabled, provider, api_key, model) |
| `GenAIHelper` | AI feature implementation |

#### AI-Powered Features

| Feature | Method | Lines | Description |
|---------|--------|-------|-------------|
| Rule Parsing | `parse_natural_language_rule()` | 88-173 | Convert plain English to structured DSL |
| Rule Suggestions | `suggest_validation_rules()` | 175-220 | Recommend rules from data profiling |
| Discrepancy Explanation | `explain_discrepancy()` | 222-257 | Plain English issue descriptions |
| Documentation | `generate_rule_documentation()` | 259-308 | Auto-generate Markdown docs |

#### Supported AI Providers

```
┌──────────────────┬─────────────────────────────────────────┐
│ Provider         │ Configuration                           │
├──────────────────┼─────────────────────────────────────────┤
│ Anthropic Claude │ ANTHROPIC_API_KEY env var               │
│ (Primary)        │ Model: claude-3-5-sonnet-20241022       │
├──────────────────┼─────────────────────────────────────────┤
│ OpenAI-compatible│ OPENAI_API_KEY env var                  │
│ (Fallback)       │ Model: gpt-4.1-mini                     │
└──────────────────┴─────────────────────────────────────────┘
```

#### Data Profiling Function

The `profile_dataframe()` function (Lines 351-407) generates statistics for AI-powered suggestions:

```python
profile = {
    "column_name": str,
    "dtype": str,
    "total_count": int,
    "null_count": int,
    "null_percentage": float,
    "unique_count": int,
    "unique_percentage": float,

    # For numeric columns:
    "is_numeric": True,
    "min": float,
    "max": float,
    "mean": float,
    "median": float,
    "std": float,
    "has_negatives": bool,
    "appears_percentage": bool,

    # For string columns:
    "is_numeric": False,
    "min_length": int,
    "max_length": int,
    "avg_length": float,
    "sample_values": list,
    "has_empty_strings": bool
}
```

---

## Data Flow

### Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            INPUT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Configuration File (Excel)          Data Sources (CSV/Excel)          │
│   ┌─────────────────────────┐        ┌─────────────────────────┐       │
│   │ config.xlsx             │        │ source1.csv             │       │
│   │ ├── Config              │        │ source2.csv             │       │
│   │ ├── ColumnMappings      │        │ validation_data.xlsx    │       │
│   │ ├── ReconciliationRules │        └─────────────────────────┘       │
│   │ └── ValidationRules     │                                           │
│   └─────────────────────────┘                                           │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROCESSING LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    recon_tool.py                                 │   │
│   │                                                                  │   │
│   │   load_configuration()                                          │   │
│   │         │                                                        │   │
│   │         ├──────────────────────┬────────────────────────┐       │   │
│   │         ▼                      ▼                        ▼       │   │
│   │   Parse Config           Parse Recon            Parse Valid     │   │
│   │   Sheet                  Rules                  Rules           │   │
│   │         │                      │                        │       │   │
│   │         ▼                      ▼                        ▼       │   │
│   │   ┌──────────┐          ┌──────────┐            ┌──────────┐   │   │
│   │   │ Settings │          │ Rule     │            │ Rule     │   │   │
│   │   │ Dict     │          │ List     │            │ List     │   │   │
│   │   └──────────┘          └──────────┘            └──────────┘   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────┐    ┌─────────────────────────┐           │
│   │   recon_engine.py       │    │  validation_engine.py   │           │
│   │                         │    │                         │           │
│   │   FOR each rule:        │    │   FOR each rule:        │           │
│   │     Load Source1        │    │     Load DataSource     │           │
│   │     Load Source2        │    │     FOR each row:       │           │
│   │     Apply Mappings      │    │       Run check         │           │
│   │     Run check_type      │    │       Record result     │           │
│   │     Record results      │    │     Compute summary     │           │
│   │     Compute summary     │    │                         │           │
│   │                         │    │                         │           │
│   └───────────┬─────────────┘    └───────────┬─────────────┘           │
│               │                              │                          │
│               └──────────────┬───────────────┘                          │
│                              ▼                                          │
│                    ┌─────────────────┐                                  │
│                    │ Aggregate       │                                  │
│                    │ Results         │                                  │
│                    └─────────────────┘                                  │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   generate_output()                                                      │
│         │                                                                │
│         ├──► Create Excel Workbook                                      │
│         │                                                                │
│         ├──► Write OutputSummary Sheet                                  │
│         │      • Project name, timestamp                                │
│         │      • Total rules executed                                   │
│         │      • Pass/fail counts and rates                             │
│         │                                                                │
│         ├──► Write ReconResults Sheet                                   │
│         │      • Rule ID, name, check type                              │
│         │      • Status (PASS/FAIL)                                     │
│         │      • Discrepancy details                                    │
│         │                                                                │
│         ├──► Write ValidationResults Sheet                              │
│         │      • Rule ID, name, check type                              │
│         │      • Status, severity                                       │
│         │      • Failed record IDs                                      │
│         │                                                                │
│         ├──► Write ExecutionLog Sheet                                   │
│         │      • Timestamp, level, component, message                   │
│         │                                                                │
│         ├──► Copy Original Config Sheets                                │
│         │                                                                │
│         └──► Apply Formatting                                           │
│                • Blue headers with white text                           │
│                • Green = PASS, Red = FAIL, Yellow = WARNING             │
│                • Auto-fit column widths                                 │
│                • Borders on all cells                                   │
│                                                                          │
│   OUTPUT: project_YYYYMMDD_HHMMSS.xlsx                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Reconciliation Data Flow Example

```
SCENARIO: Reconcile internal transactions with bank statement
─────────────────────────────────────────────────────────────────

Source 1: internal_transactions.csv       Source 2: bank_statement.csv
┌────────────┬─────────┬────────────┐    ┌────────────┬─────────┬────────┐
│ trans_id   │ amount  │ date       │    │ ref_id     │ value   │ txn_dt │
├────────────┼─────────┼────────────┤    ├────────────┼─────────┼────────┤
│ TXN001     │ 1000.00 │ 2026-01-10 │    │ TXN001     │ 1000.00 │ Jan 10 │
│ TXN002     │ 500.00  │ 2026-01-11 │    │ TXN002     │ 499.50  │ Jan 11 │
│ TXN003     │ 750.00  │ 2026-01-12 │    │ TXN004     │ 250.00  │ Jan 12 │
│ TXN005     │ 200.00  │ 2026-01-13 │    │ TXN005     │ 200.00  │ Jan 13 │
└────────────┴─────────┴────────────┘    └────────────┴─────────┴────────┘

Column Mappings Applied:
  trans_id → ref_id
  amount → value
  date → txn_dt

RULE 1: key_match
─────────────────────
Keys in Source1: {TXN001, TXN002, TXN003, TXN005}
Keys in Source2: {TXN001, TXN002, TXN004, TXN005}

Result:
  Matched: TXN001, TXN002, TXN005 (3 records)
  Source1 only: TXN003 (1 record) ← DISCREPANCY
  Source2 only: TXN004 (1 record) ← DISCREPANCY
  Status: FAIL

RULE 2: value_equals (amount vs value, 1% tolerance)
────────────────────────────────────────────────────
TXN001: 1000.00 vs 1000.00 → MATCH (0% diff)
TXN002: 500.00 vs 499.50   → FAIL (0.1% diff, but below 1% tolerance? Actually 0.1% < 1%, so PASS)
TXN005: 200.00 vs 200.00   → MATCH (0% diff)

Wait, let me recalculate TXN002:
  Difference: |500.00 - 499.50| = 0.50
  Percentage: 0.50 / 500.00 * 100 = 0.1%
  Tolerance: 1%
  Result: 0.1% < 1% → PASS

Status: PASS (all matched records within tolerance)

RULE 3: aggregate_sum
─────────────────────
Source1 total: 1000 + 500 + 750 + 200 = 2450.00
Source2 total: 1000 + 499.50 + 250 + 200 = 1949.50
Difference: 500.50 (20.4%)
Status: FAIL (significant difference due to missing/extra records)

FINAL OUTPUT:
┌─────────────┬──────────────┬────────┬─────────────────────────────────┐
│ Rule        │ Check Type   │ Status │ Details                         │
├─────────────┼──────────────┼────────┼─────────────────────────────────┤
│ RULE_001    │ key_match    │ FAIL   │ 1 in S1 only, 1 in S2 only     │
│ RULE_002    │ value_equals │ PASS   │ All values within 1% tolerance │
│ RULE_003    │ aggregate_sum│ FAIL   │ Totals differ by 20.4%         │
└─────────────┴──────────────┴────────┴─────────────────────────────────┘
```

---

## Configuration Format

### Excel Configuration Structure

The tool requires an Excel file with 4 mandatory sheets:

#### Sheet 1: Config

| Column | Description | Example Values |
|--------|-------------|----------------|
| section | Configuration category | general, sources, output |
| parameter | Parameter name | project_name, source1_path |
| value | Parameter value | Bank Reconciliation, ./data/internal.csv |

**Required Parameters:**

```
┌──────────┬─────────────────┬────────────────────────────────────────┐
│ Section  │ Parameter       │ Description                            │
├──────────┼─────────────────┼────────────────────────────────────────┤
│ general  │ project_name    │ Name for output file prefix            │
│ sources  │ source1_path    │ Path to first data source              │
│ sources  │ source2_path    │ Path to second data source             │
│ sources  │ source1_encoding│ File encoding (utf-8, latin-1, etc.)   │
│ sources  │ source2_encoding│ File encoding                          │
│ output   │ output_directory│ Where to save results                  │
└──────────┴─────────────────┴────────────────────────────────────────┘
```

#### Sheet 2: ColumnMappings

| Column | Description |
|--------|-------------|
| mapping_id | Unique identifier |
| source1_column | Column name in source 1 |
| source2_column | Corresponding column in source 2 |
| data_type | Optional: string, numeric, date |
| description | Human-readable description |

#### Sheet 3: ReconciliationRules

| Column | Description | Required |
|--------|-------------|----------|
| rule_id | Unique identifier | Yes |
| rule_name | Descriptive name | Yes |
| active | TRUE/FALSE | Yes |
| source1 | Source 1 filename | Yes |
| source2 | Source 2 filename | Yes |
| key_column_s1 | Key column in source 1 | Yes |
| key_column_s2 | Key column in source 2 | Yes |
| check_type | One of 6 check types | Yes |
| compare_column_s1 | Column to compare (source 1) | For value checks |
| compare_column_s2 | Column to compare (source 2) | For value checks |
| tolerance | Numeric tolerance value | Optional |
| tolerance_type | percentage/absolute/days | Optional |
| description | Human-readable description | Optional |

#### Sheet 4: ValidationRules

| Column | Description | Required |
|--------|-------------|----------|
| rule_id | Unique identifier | Yes |
| rule_name | Descriptive name | Yes |
| active | TRUE/FALSE | Yes |
| data_source | Source filename | Yes |
| column | Column to validate | Yes |
| check_type | One of 19 check types | Yes |
| parameter_1 | First parameter | Depends on check |
| parameter_2 | Second parameter | For 'between' check |
| severity | ERROR/WARNING/INFO | Yes |
| description | Human-readable description | Optional |

---

## Output Sheets Reference

### OutputSummary Sheet

Contains high-level metrics and status:

| Row | Content |
|-----|---------|
| 1 | Project Name |
| 2 | Execution Timestamp |
| 3 | (blank) |
| 4 | **Reconciliation Summary** |
| 5 | Total Rules: X |
| 6 | Passed: X |
| 7 | Failed: X |
| 8 | Pass Rate: X% |
| 9 | (blank) |
| 10 | **Validation Summary** |
| 11 | Total Rules: X |
| 12 | Passed: X |
| 13 | Failed: X |
| 14 | Pass Rate: X% |

### ReconResults Sheet

| Column | Description |
|--------|-------------|
| rule_id | Rule identifier |
| rule_name | Descriptive name |
| check_type | Type of reconciliation check |
| status | PASS or FAIL |
| source1_count | Records in source 1 |
| source2_count | Records in source 2 |
| matched_count | Successfully matched records |
| discrepancy_count | Number of discrepancies |
| discrepancy_details | JSON or comma-separated list of issues |
| execution_time_ms | Time taken for this rule |

### ValidationResults Sheet

| Column | Description |
|--------|-------------|
| rule_id | Rule identifier |
| rule_name | Descriptive name |
| check_type | Type of validation check |
| column | Column validated |
| status | PASS or FAIL |
| severity | ERROR, WARNING, or INFO |
| total_records | Records checked |
| passed_count | Records passing |
| failed_count | Records failing |
| pass_rate | Percentage passing |
| failed_record_ids | Comma-separated list of failed record IDs |
| sample_failures | Example failure messages |

### ExecutionLog Sheet

| Column | Description |
|--------|-------------|
| timestamp | ISO format timestamp |
| level | INFO, WARNING, ERROR |
| component | Module name (ReconTool, ReconEngine, etc.) |
| message | Log message |

---

## Algorithm Details

### Value Comparison with Tolerance

```python
def _compare_values(value1, value2, tolerance, tolerance_type):
    """
    Compare two values with optional tolerance.

    Args:
        value1: Value from source 1
        value2: Value from source 2
        tolerance: Tolerance threshold
        tolerance_type: 'percentage', 'absolute', or 'days'

    Returns:
        Tuple of (is_match: bool, difference: float)
    """
    if tolerance is None or tolerance == 0:
        # Exact match required
        return value1 == value2, abs(value1 - value2)

    difference = abs(value1 - value2)

    if tolerance_type == 'percentage':
        # Calculate percentage difference relative to value1
        if value1 == 0:
            return value2 == 0, difference
        pct_diff = (difference / abs(value1)) * 100
        return pct_diff <= tolerance, pct_diff

    elif tolerance_type == 'absolute':
        # Direct numeric comparison
        return difference <= tolerance, difference

    elif tolerance_type == 'days':
        # For date comparisons
        day_diff = abs((value1 - value2).days)
        return day_diff <= tolerance, day_diff

    return value1 == value2, difference
```

### Unique Value Check

```python
def _check_unique(df, column):
    """
    Check for duplicate values in a column.

    Algorithm:
    1. Get value counts for the column
    2. Find values that appear more than once
    3. Return list of duplicate values and their counts

    Returns:
        ValidationResult with list of duplicates
    """
    value_counts = df[column].value_counts()
    duplicates = value_counts[value_counts > 1]

    if len(duplicates) == 0:
        return ValidationResult(status='PASS', failed_count=0)

    # Find all rows with duplicate values
    duplicate_values = duplicates.index.tolist()
    failed_rows = df[df[column].isin(duplicate_values)]
    failed_ids = [get_record_id(row) for _, row in failed_rows.iterrows()]

    return ValidationResult(
        status='FAIL',
        failed_count=len(failed_ids),
        failed_record_ids=failed_ids,
        message=f"Found {len(duplicate_values)} duplicate values"
    )
```

### Regex Validation

```python
def _check_regex_match(df, column, pattern):
    """
    Validate column values against a regex pattern.

    Args:
        df: DataFrame to validate
        column: Column name to check
        pattern: Regular expression pattern

    Returns:
        ValidationResult with non-matching records
    """
    import re
    compiled_pattern = re.compile(pattern)

    failed_ids = []
    for idx, row in df.iterrows():
        value = str(row[column]) if pd.notna(row[column]) else ''
        if not compiled_pattern.match(value):
            failed_ids.append(get_record_id(row))

    return ValidationResult(
        status='PASS' if len(failed_ids) == 0 else 'FAIL',
        failed_count=len(failed_ids),
        failed_record_ids=failed_ids
    )
```

---

## Usage Examples

### Example 1: Basic Command Line Usage

```bash
# Run reconciliation and validation
python recon_tool.py config/bank_reconciliation.xlsx

# Output: bank_reconciliation_20260113_143022.xlsx
```

### Example 2: Configuration for Bank Reconciliation

**Config Sheet:**
```
section    | parameter        | value
-----------|------------------|----------------------------------
general    | project_name     | Q4_Bank_Reconciliation
sources    | source1_path     | ./data/internal_ledger.csv
sources    | source2_path     | ./data/bank_statement.csv
sources    | source1_encoding | utf-8
sources    | source2_encoding | utf-8
output     | output_directory | ./reports/
```

**ColumnMappings Sheet:**
```
mapping_id | source1_column | source2_column | data_type
-----------|----------------|----------------|----------
MAP_001    | transaction_id | reference_num  | string
MAP_002    | amount         | txn_amount     | numeric
MAP_003    | post_date      | value_date     | date
```

**ReconciliationRules Sheet:**
```
rule_id  | rule_name          | check_type   | tolerance | tolerance_type
---------|--------------------|--------------|-----------|--------------
REC_001  | Key Match          | key_match    |           |
REC_002  | Amount Comparison  | value_equals | 0.01      | absolute
REC_003  | Total Verification | aggregate_sum| 1         | percentage
```

**ValidationRules Sheet:**
```
rule_id  | rule_name         | check_type   | column   | parameter_1 | severity
---------|-------------------|--------------|----------|-------------|--------
VAL_001  | No Null Amounts   | not_null     | amount   |             | ERROR
VAL_002  | Positive Amounts  | greater_than | amount   | 0           | ERROR
VAL_003  | Valid Date Format | is_date      | post_date| %Y-%m-%d    | ERROR
VAL_004  | Unique Trans ID   | unique       | trans_id |             | ERROR
```

### Example 3: Validation Rule Examples

```
Check Type     | Parameter 1       | Parameter 2 | Example Use
---------------|-------------------|-------------|---------------------------
not_null       | -                 | -           | Ensure required fields
not_empty      | -                 | -           | No blank strings
greater_than   | 0                 | -           | Positive amounts
less_than      | 1000000           | -           | Max transaction limit
between        | 0                 | 100         | Percentage fields
equals         | ACTIVE            | -           | Status field value
is_in_list     | USD,EUR,GBP       | -           | Valid currency codes
regex_match    | ^[A-Z]{3}[0-9]+$  | -           | Reference number format
is_date        | %Y-%m-%d          | -           | ISO date format
unique         | -                 | -           | No duplicate IDs
min_length     | 10                | -           | Minimum field length
max_length     | 50                | -           | Maximum field length
starts_with    | TXN               | -           | Transaction ID prefix
contains       | @                 | -           | Email validation
```

### Example 4: Using GenAI Features (Optional)

```python
from genai_helper import GenAIHelper, GenAIConfig, profile_dataframe
import pandas as pd

# Initialize with GenAI enabled
config = GenAIConfig(
    enabled=True,
    provider="Claude",
    api_key_env_var="ANTHROPIC_API_KEY"
)
helper = GenAIHelper(config)

# Parse natural language rule
nl_rule = "Check that all amounts are between 0 and 10000"
structured_rule = helper.parse_natural_language_rule(
    nl_rule,
    rule_type="validation"
)
# Returns: {"check_type": "between", "column": "amount", "parameter_1": 0, "parameter_2": 10000}

# Get rule suggestions from data profile
df = pd.read_csv("transactions.csv")
profile = profile_dataframe(df, "amount")
suggestions = helper.suggest_validation_rules(profile, "amount")

# Explain a discrepancy
discrepancy = {
    "rule": "value_equals",
    "source1_value": 1000.00,
    "source2_value": 999.50,
    "difference": 0.50
}
explanation = helper.explain_discrepancy(discrepancy)
# Returns: "The amount in the internal system (1000.00) differs from the bank
#          statement (999.50) by 0.50. This could be due to bank fees or
#          rounding differences. Recommend verifying with bank statement details."
```

---

## Dependencies

### Required Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | >= 1.3.0 | Data manipulation and analysis |
| numpy | >= 1.20.0 | Numerical operations |
| openpyxl | >= 3.0.0 | Excel file reading/writing |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| anthropic | >= 0.18.0 | Anthropic Claude API integration |
| openai | >= 1.0.0 | OpenAI-compatible API fallback |

### Installation

```bash
# Required packages
pip install pandas numpy openpyxl

# Optional: For GenAI features
pip install anthropic openai
```

---

## Executive Summary for Management

### What Is This Tool?

This is an **automated data checking system** that helps ensure your data is accurate and complete. Think of it as a tireless assistant that compares spreadsheets and flags anything that doesn't look right.

### What Does It Do?

The tool performs two main jobs:

**1. Reconciliation (Matching)**
- Compares data between two sources to find differences
- *Example:* Checking your internal sales records against what the bank shows
- Finds missing transactions, amount differences, and mismatched records

**2. Validation (Quality Checks)**
- Checks a single data source for errors
- *Example:* Making sure all customer records have valid email addresses
- Catches missing data, wrong formats, duplicates, and out-of-range values

### How Does It Work?

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   1. You provide an Excel spreadsheet with your checking rules  │
│                            ↓                                     │
│   2. The tool reads your data files                             │
│                            ↓                                     │
│   3. It runs all the checks automatically                       │
│                            ↓                                     │
│   4. It produces a color-coded report                           │
│                                                                  │
│        🟢 Green = Everything OK                                  │
│        🔴 Red = Problem found                                    │
│        🟡 Yellow = Warning, needs review                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What Problems Does It Solve?

| Business Challenge | How This Tool Helps |
|-------------------|---------------------|
| Manual reconciliation takes days | Automates checks in minutes |
| Human errors in data review | Consistent, repeatable checks |
| Hard to track what was checked | Complete audit trail in output |
| Different people check differently | Standardized rules everyone follows |
| Data quality issues found too late | Catches problems immediately |

### Key Capabilities

- **25 different check types** (6 for matching, 19 for validation)
- **Flexible tolerance settings** (e.g., allow 1% difference in amounts)
- **Fuzzy text matching** (catches "John Smith" vs "JOHN SMITH")
- **Optional AI features** for plain-English rule creation
- **Audit-ready reports** with timestamps and complete logs

### What You Need to Use It

- Python installed on a computer
- Your data in CSV or Excel format
- A configuration Excel file (template can be generated)

### Investment Summary

| Aspect | Details |
|--------|---------|
| Codebase Size | 4 Python files, ~2,600 lines |
| External Database | Not required |
| Ongoing Costs | None (standard Python libraries) |
| Optional AI | Requires Anthropic or OpenAI API access |

### Bottom Line

This tool transforms manual, error-prone data checking into an automated, auditable process. It can check thousands of records in seconds, flagging exactly which records have issues and why, while maintaining a complete audit trail for compliance purposes.

---

*Document generated by automated codebase analysis*
