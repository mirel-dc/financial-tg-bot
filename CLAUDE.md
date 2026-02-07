# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

T-Bank CSV to XLSX Converter — CLI utility that converts T-Bank (Russian bank) CSV export files into categorized XLSX spreadsheets using double-entry bookkeeping format. Designed for import into Google Sheets financial tracking spreadsheets.

## Development Commands

All commands should be run from the `src/` directory unless otherwise specified.

### Environment Setup
```bash
# Sync dependencies (creates .venv automatically)
cd src && uv sync --extra dev

# Run from repository root using Makefile
make sync
```

### Testing
```bash
# Run all tests with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest --cov=tbank_converter tests/

# Run specific test file
uv run pytest tests/test_transform.py -v

# From repository root
make test
make coverage
```

### Running the CLI
```bash
# Basic conversion
uv run tbank-convert -i input.csv -o output.xlsx

# With custom config
uv run tbank-convert -i input.csv -o output.xlsx -c configs/my_config.yaml

# Using Makefile from root
make run INPUT=input.csv OUTPUT=output.xlsx
```

### Cleanup
```bash
make clean  # Removes .pytest_cache, .coverage, htmlcov, *.xlsx, __pycache__
```

## Architecture

### Pipeline Architecture

The codebase follows a clean pipeline pattern with clear separation of concerns:

```
CSV Input → Parsing → Transformation → Merge Transfers → Categorization → XLSX Generation → Output
```

**Key Flow (pipeline.py):**
1. `TBankCSVReader` reads and validates 15-column CSV format (semicolon-delimited)
2. `DataTransformer` converts raw strings to typed `Operation` objects with proper date/decimal parsing
3. `DataTransformer.merge_paired_transfers()` merges paired inter-account transfers into single operations
4. `Categorizer.apply_double_entry()` applies double-entry bookkeeping: determines debit/credit accounts, categories, subcategories
5. `XLSXWriter` generates Excel file with 9-column double-entry format

### Domain Models (domain/models.py)

**Operation** (dataclass): Core data model with 15 CSV fields + 5 double-entry fields:
- CSV fields: dates, amounts (Decimal), card number, MCC, description, etc.
- Double-entry: `debit_account`, `credit_account`, `category`, `subcategory`, `comment`

**Report** (dataclass): Aggregation with operations list, categories, auto-calculated period dates.

### Configuration System (config.py + configs/default.yaml)

Pydantic-validated YAML config with:
- `settings`: uncategorized_label, default_currency, date_format, default_account, service_accounts
- `categories`: List of valid expense categories
- `account_mappings`: Card number → account name (e.g., `"*1234": "Счет Тбанка"`)
- `bank_category_mapping`: T-Bank category → expense category (can include subcategory via `BankCategoryMapping`)
- `description_mapping`: Description → expense category (higher priority than bank category)
- `subcategory_mappings`: Description keyword → subcategory
- `income_description_mapping`: Description keyword → income category
- `transfer_account_mapping`: Transfer description → target account name

**Categorization Priority (domain/categorization.py, `_get_category`):**
1. Exact match in description_mapping
2. Substring match in description_mapping (case-insensitive)
3. T-Bank bank_category_mapping
4. Fallback to uncategorized_label ("прочее")

### XLSX Output Structure (io/xlsx_writer.py)

**9 Columns:**
1. Дата (date as YYYY-MM-DD)
2. Дебет (Куда) — debit account
3. Кредит (Откуда) — credit account
4. Сумма — amount (always positive, formatted with currency symbol)
5. Валюта — currency code
6. Описание — description
7. Комментарий — empty for user
8. Категория — expense/income category
9. Подкатегория — subcategory

**Currency:** Configurable via `default_currency` in config. Symbol resolved from `CURRENCY_SYMBOLS` mapping (RUB→₽, USD→$, EUR→€, etc.)

**Sheet naming:** Auto-generated from period start date (e.g., "January2026").

### Transfer Merging (domain/transform.py, `merge_paired_transfers`)

T-Bank exports inter-account transfers as two paired operations:
- One with negative amount (money leaving)
- One with positive amount (money entering)

Merging logic: matches pairs by description "Между своими счетами", opposite amounts, within 5-second window. Produces single operation with both debit and credit card numbers filled.

## Package Structure

```
src/tbank_converter/
├── cli.py                   # Click-based CLI interface
├── pipeline.py              # Main orchestrator (ConversionPipeline)
├── config.py                # Pydantic config models + YAML loading
├── domain/
│   ├── models.py            # Operation and Report dataclasses
│   ├── transform.py         # CSV → typed objects, transfer merging
│   └── categorization.py    # Double-entry logic + category mapping
└── io/
    ├── csv_reader.py        # T-Bank CSV parser (15 columns, semicolon-separated)
    └── xlsx_writer.py       # Excel file generation
```

## CSV Format Expectations

T-Bank exports use specific format:
- Delimiter: semicolon (`;`)
- Decimal separator: comma (`,`) — converted to dot for Decimal
- Date format: `"%d.%m.%Y %H:%M:%S"` (configurable in settings)
- Exactly 15 columns expected (reader validates this)
- UTF-8 encoding with BOM

## Testing Notes

- Test fixtures in `tests/fixtures/sample_tbank.csv`
- `tests/helpers.py` provides `make_operation(**overrides)` factory for creating Operation objects with sensible defaults
- Tests cover: CSV parsing, transformation, categorization, XLSX generation
- `test_xlsx_smoke.py` creates actual XLSX files in tmp_path
- Use `-v` flag for detailed test output

## Technology Stack

- **uv**: Fast package manager (replaces pip/poetry/venv)
- **Click**: CLI framework with path validation
- **OpenPyXL**: Excel file creation (no pandas dependency)
- **Pydantic**: Config validation (not used for Operation model — plain dataclass)
- **PyYAML**: Config file parsing
- **Python 3.11+**: Uses modern type hints (e.g., `dict[str, str]`, `Path | None`)

## Important Patterns

1. **Decimal arithmetic**: All money amounts use `Decimal` to avoid floating-point errors
2. **No side effects in getters**: `_get_category` returns `(category, subcategory)` tuple, `_get_subcategory` takes `bank_subcategory` as explicit parameter
3. **Workbook lifecycle**: `XLSXWriter` creates Workbook inside `write()`, not in `__init__` — safe to call multiple times
4. **Config-driven currency**: Currency symbol derived from `default_currency` setting, not hardcoded
5. **Working directory**: All commands assume you're in `src/` directory (virtual env, module imports, config paths)
