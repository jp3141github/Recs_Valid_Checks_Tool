# Recs Valid Checks Tool

A data quality automation system for reconciliation and validation operations.

## Project Structure

```
Recs_Valid_Checks_Tool/
├── recon_tool.py           # Main entry point and orchestrator
├── recon_engine.py         # Reconciliation logic engine
├── validation_engine.py    # Validation logic engine (19 check types)
├── genai_helper.py         # Optional GenAI integration
├── README.md               # This file
└── archive/                # Non-critical archived files
    ├── utilities/          # Development and testing utilities
    │   ├── generate_synthetic_data.py  # Test data generator
    │   └── create_config_template.py   # Config template generator
    ├── docs/               # Documentation
    │   └── system_design.pdf
    └── backups/            # Backup files
        └── recon_tool.zip
```

## Core Components

### Critical Path Files

| File | Lines | Purpose |
|------|-------|---------|
| `recon_tool.py` | 542 | Main orchestrator - loads config, runs workflows, generates output |
| `recon_engine.py` | 734 | Reconciliation engine - compares data sources, identifies discrepancies |
| `validation_engine.py` | 915 | Validation engine - 19 validation check types for data quality |
| `genai_helper.py` | 407 | AI integration - natural language rules, auto-suggestions |

### Reconciliation Check Types
- `key_match` - Verify records exist in both sources
- `value_equals` - Compare field values with optional tolerance
- `fuzzy_match` - Text comparison using sequence matching
- `aggregate_sum` - Compare total sums between sources
- `aggregate_count` - Compare record counts
- `aggregate_avg` - Compare average values

### Validation Check Types (19 total)
`not_null`, `not_empty`, `greater_than`, `less_than`, `between`, `equals`, `not_equals`, `is_in_list`, `not_in_list`, `regex_match`, `is_date`, `is_numeric`, `is_integer`, `unique`, `min_length`, `max_length`, `starts_with`, `ends_with`, `contains`

## Usage

```bash
python recon_tool.py <config_file.xlsx>
```

## Dependencies

- pandas
- numpy
- openpyxl
- anthropic (optional, for GenAI features)

## Archived Utilities

The `archive/` directory contains non-critical utilities for development/testing:

- **generate_synthetic_data.py** - Creates realistic test datasets with intentional discrepancies
- **create_config_template.py** - Generates Excel configuration templates
- **system_design.pdf** - Architecture documentation
