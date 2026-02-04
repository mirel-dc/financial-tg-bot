"""Smoke tests for XLSX generation."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from tbank_converter.config import Config, Settings
from tbank_converter.domain.models import Operation, Report
from tbank_converter.io.xlsx_writer import XLSXWriter


@pytest.fixture
def sample_config():
    """Create sample config."""
    return Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="Нет категории",
            ignore_label="Не учитывать",
        ),
        categories=["Супермаркеты", "Рестораны", "Не учитывать", "Нет категории"],
        category_colors={
            "Супермаркеты": "C6EFCE",
            "Рестораны": "FFC7CE",
            "Не учитывать": "D9D9D9",
            "Нет категории": "FFFFFF",
        },
    )


@pytest.fixture
def sample_report():
    """Create sample report."""
    operations = [
        Operation(
            operation_date=datetime(2026, 1, 15, 12, 0, 0),
            payment_date=None,
            card_number="*1234",
            status="OK",
            operation_amount=Decimal("-100.50"),
            operation_currency="RUB",
            payment_amount=Decimal("-100.50"),
            payment_currency="RUB",
            cashback=Decimal("0"),
            bank_category="Супермаркеты",
            mcc="5411",
            description="Пятёрочка",
            bonus_count="0",
            investment_amount=Decimal("0"),
            total_payment_amount=Decimal("-100.50"),
        ),
        Operation(
            operation_date=datetime(2026, 1, 16, 14, 30, 0),
            payment_date=None,
            card_number="*1234",
            status="OK",
            operation_amount=Decimal("-50.00"),
            operation_currency="RUB",
            payment_amount=Decimal("-50.00"),
            payment_currency="RUB",
            cashback=Decimal("0"),
            bank_category="Рестораны",
            mcc="5812",
            description="Макдоналдс",
            bonus_count="0",
            investment_amount=Decimal("0"),
            total_payment_amount=Decimal("-50.00"),
        ),
    ]

    return Report(
        operations=operations,
        categories=["Супермаркеты", "Рестораны", "Нет категории"],
    )


def test_xlsx_creates_file(tmp_path, sample_report, sample_config):
    """Test that XLSX file is created."""
    output_path = tmp_path / "test.xlsx"

    writer = XLSXWriter(sample_report, sample_config)
    writer.write(output_path)

    assert output_path.exists()


def test_xlsx_has_formulas(tmp_path, sample_report, sample_config):
    """Test that XLSX contains expected formulas in summary."""
    output_path = tmp_path / "test.xlsx"

    writer = XLSXWriter(sample_report, sample_config)
    writer.write(output_path)

    # Load and check formulas
    wb = load_workbook(output_path)
    ws = wb.active

    # Check summary has SUMIF formulas (summary is in column G, starting at row 2)
    summary_data_row = 2
    sum_cell = ws.cell(row=summary_data_row, column=7)  # Column G
    assert sum_cell.value.startswith("=SUMIF")

    wb.close()


def test_xlsx_has_correct_headers(tmp_path, sample_report, sample_config):
    """Test that XLSX has correct column headers."""
    output_path = tmp_path / "test.xlsx"

    writer = XLSXWriter(sample_report, sample_config)
    writer.write(output_path)

    wb = load_workbook(output_path)
    ws = wb.active

    # Main data headers
    assert ws["A1"].value == "Дата операции"
    assert ws["B1"].value == "Описание"
    assert ws["C1"].value == "Категория"
    assert ws["D1"].value == "Сумма операции"

    # Summary headers (to the right)
    assert ws["F1"].value == "Категория"
    assert ws["G1"].value == "Сумма"
    assert ws["H1"].value == "Операций"

    wb.close()


def test_xlsx_sheet_name_from_date(tmp_path, sample_report, sample_config):
    """Test that sheet name is set from report period."""
    output_path = tmp_path / "test.xlsx"

    writer = XLSXWriter(sample_report, sample_config)
    writer.write(output_path)

    wb = load_workbook(output_path)
    ws = wb.active

    # Sheet name should be formatted as "MonthYear" (e.g., "January2026")
    assert ws.title == "January2026"

    wb.close()


def test_xlsx_summary_all_categories(tmp_path, sample_report, sample_config):
    """Test that summary includes all categories from config."""
    output_path = tmp_path / "test.xlsx"

    writer = XLSXWriter(sample_report, sample_config)
    writer.write(output_path)

    wb = load_workbook(output_path)
    ws = wb.active

    # Check that summary shows all categories from config (except "Не учитывать")
    # Config has: Супермаркеты, Рестораны, Не учитывать, Нет категории
    # Summary should show: Супермаркеты, Рестораны, Нет категории

    # F2, F3, F4 should contain category names
    assert ws["F2"].value == "Супермаркеты"
    assert ws["F3"].value == "Рестораны"

    # Check that G2 (sum column) has SUMIF formula
    sum_cell = ws["G2"]
    assert sum_cell.value is not None
    assert "SUMIF" in str(sum_cell.value).upper()

    # Check that H2 (count column) has COUNTIF formula
    count_cell = ws["H2"]
    assert count_cell.value is not None
    assert "COUNTIF" in str(count_cell.value).upper()

    wb.close()
