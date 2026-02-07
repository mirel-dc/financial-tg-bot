"""Domain models for T-Bank operations."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Operation:
    """T-Bank operation data model."""

    # Original CSV fields (15 columns)
    operation_date: datetime
    payment_date: datetime | None
    card_number: str
    status: str
    operation_amount: Decimal
    operation_currency: str
    payment_amount: Decimal
    payment_currency: str
    cashback: Decimal
    bank_category: str
    mcc: str
    description: str
    bonus_count: str
    investment_amount: Decimal
    total_payment_amount: Decimal

    # Double-entry bookkeeping fields (5 columns)
    debit_account: str = ""      # Дебет (Куда)
    credit_account: str = ""     # Кредит (Откуда)
    category: str = ""           # Категория (только для расходов)
    subcategory: str = ""        # Подкатегория (только для расходов)
    comment: str = ""            # Комментарий (пустой, для пользователя)


@dataclass
class Report:
    """Conversion report with operations and statistics."""

    operations: list[Operation]
    categories: list[str]
    period_start: datetime | None = None
    period_end: datetime | None = None

    def __post_init__(self):
        """Calculate statistics after initialization."""
        if self.operations:
            dates = [op.operation_date for op in self.operations if op.operation_date]
            if dates:
                self.period_start = min(dates)
                self.period_end = max(dates)
