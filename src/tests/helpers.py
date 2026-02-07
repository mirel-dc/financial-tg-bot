"""Shared test helpers."""

from datetime import datetime
from decimal import Decimal

from tbank_converter.domain.models import Operation


_OPERATION_DEFAULTS = {
    "operation_date": datetime(2026, 1, 30, 12, 0, 0),
    "payment_date": None,
    "card_number": "*1234",
    "status": "OK",
    "operation_amount": Decimal("-100.00"),
    "operation_currency": "RUB",
    "payment_amount": Decimal("-100.00"),
    "payment_currency": "RUB",
    "cashback": Decimal("0"),
    "bank_category": "",
    "mcc": "",
    "description": "Test",
    "bonus_count": "",
    "investment_amount": Decimal("0"),
    "total_payment_amount": Decimal("-100.00"),
}


def make_operation(**overrides) -> Operation:
    """Create an Operation with sensible defaults, overriding specific fields."""
    fields = {**_OPERATION_DEFAULTS, **overrides}
    return Operation(**fields)
