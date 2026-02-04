"""Tests for data transformation."""

import pytest
from datetime import datetime
from decimal import Decimal

from tbank_converter.domain.transform import DataTransformer


def test_parse_date():
    """Test date parsing."""
    date_str = "30.01.2026 19:32:00"
    result = DataTransformer.parse_date(date_str)

    assert result == datetime(2026, 1, 30, 19, 32, 0)


def test_parse_date_invalid():
    """Test invalid date parsing."""
    with pytest.raises(ValueError, match="Invalid date format"):
        DataTransformer.parse_date("invalid")


def test_parse_amount():
    """Test amount parsing with comma separator."""
    assert DataTransformer.parse_amount("-2234,86") == Decimal("-2234.86")
    assert DataTransformer.parse_amount("1000,00") == Decimal("1000.00")
    assert DataTransformer.parse_amount("0") == Decimal("0")
    assert DataTransformer.parse_amount("") == Decimal("0")


def test_parse_amount_invalid():
    """Test invalid amount parsing."""
    with pytest.raises(ValueError, match="Invalid amount format"):
        DataTransformer.parse_amount("abc")


def test_normalize_string():
    """Test string normalization."""
    assert DataTransformer.normalize_string("  test  ") == "test"
    assert DataTransformer.normalize_string("test") == "test"


def test_transform_operation():
    """Test full operation transformation."""
    transformer = DataTransformer()

    raw_data = {
        "operation_date": "30.01.2026 19:32:00",
        "payment_date": "01.02.2026 00:00:00",
        "card_number": "*1234",
        "status": "OK",
        "operation_amount": "-100,50",
        "operation_currency": "RUB",
        "payment_amount": "-100,50",
        "payment_currency": "RUB",
        "cashback": "0",
        "bank_category": "Супермаркеты",
        "mcc": "5411",
        "description": "Пятёрочка",
        "bonus_count": "0",
        "investment_amount": "0",
        "total_payment_amount": "-100,50",
    }

    operation = transformer.transform_operation(raw_data)

    assert operation.operation_date == datetime(2026, 1, 30, 19, 32, 0)
    assert operation.operation_amount == Decimal("-100.50")
    assert operation.description == "Пятёрочка"
    assert operation.bank_category == "Супермаркеты"
