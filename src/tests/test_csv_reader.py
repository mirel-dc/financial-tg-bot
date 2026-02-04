"""Tests for CSV reader."""

import pytest
from pathlib import Path

from tbank_converter.io.csv_reader import TBankCSVReader


def test_read_sample_csv():
    """Test reading sample T-Bank CSV file."""
    csv_path = Path(__file__).parent / "fixtures" / "sample_tbank.csv"

    if not csv_path.exists():
        pytest.skip("Sample CSV not found")

    reader = TBankCSVReader(csv_path)
    operations = list(reader.read())

    assert len(operations) > 0
    assert "operation_date" in operations[0]
    assert "description" in operations[0]
    assert "operation_amount" in operations[0]


def test_validates_headers(tmp_path):
    """Test that invalid CSV headers are rejected."""
    invalid_csv = tmp_path / "invalid.csv"
    invalid_csv.write_text("col1;col2;col3\nval1;val2;val3\n", encoding="utf-8")

    reader = TBankCSVReader(invalid_csv)

    with pytest.raises(ValueError, match="Expected 15 columns"):
        list(reader.read())


def test_file_not_found():
    """Test error when CSV file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        TBankCSVReader(Path("nonexistent.csv"))
