"""Tests for data transformation."""

import pytest
from datetime import datetime
from decimal import Decimal

from tbank_converter.domain.transform import DataTransformer
from tbank_converter.domain.models import Operation

from tests.helpers import make_operation


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


def test_merge_paired_transfers():
    """Test that paired inter-account transfers are merged into single operations."""
    transformer = DataTransformer()

    # Create two paired transfer operations
    op1 = make_operation(
        operation_date=datetime(2026, 1, 27, 16, 25, 21),
        card_number="*7280",  # Leaving from this account
        operation_amount=Decimal("-10000.00"),  # Negative = leaving
        payment_amount=Decimal("-10000.00"),
        total_payment_amount=Decimal("-10000.00"),
        bank_category="Переводы",
        description="Между своими счетами",
    )

    op2 = make_operation(
        operation_date=datetime(2026, 1, 27, 16, 25, 22),  # 1 second later
        card_number="*8878",  # Entering this account
        operation_amount=Decimal("10000.00"),  # Positive = entering
        payment_amount=Decimal("10000.00"),
        total_payment_amount=Decimal("10000.00"),
        bank_category="Переводы",
        description="Между своими счетами",
    )

    operations = [op1, op2]
    merged = transformer.merge_paired_transfers(operations)

    # Should be merged into 1 operation
    assert len(merged) == 1
    merged_op = merged[0]

    # Check fields
    assert merged_op.operation_amount == Decimal("10000.00")  # Positive amount
    assert merged_op.credit_account == "*7280"  # Money leaving from this
    assert merged_op.debit_account == "*8878"  # Money entering here
    assert merged_op.description == "Между своими счетами"