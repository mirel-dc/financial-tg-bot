"""Tests for double-entry categorization."""

from datetime import datetime
from decimal import Decimal

from tbank_converter.config import BankCategoryMapping, Config, Settings, ServiceAccounts
from tbank_converter.domain.categorization import Categorizer
from tbank_converter.domain.models import Operation

from tests.helpers import make_operation


def test_expense_operation():
    """Test expense operation gets correct debit/credit and category."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["продукты", "прочее"],
        account_mappings={"*1234": "Счёт ТБанка"},
        subcategory_mappings={"пятёрочка": "еда"},
        description_mapping={"Пятёрочка": "продукты"},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("-500.00"),
            payment_amount=Decimal("-500.00"),
            total_payment_amount=Decimal("-500.00"),
            mcc="5411",
            description="Пятёрочка",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "расходы"
    assert op.credit_account == "Счёт ТБанка"
    assert op.category == "продукты"
    assert op.subcategory == "еда"
    assert op.comment == ""


def test_income_operation():
    """Test income operation gets correct debit/credit and no category."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*5678": "ТИнвестиции"},
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            card_number="*5678",
            operation_amount=Decimal("10000.00"),
            payment_amount=Decimal("10000.00"),
            total_payment_amount=Decimal("10000.00"),
            description="Зарплата",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "ТИнвестиции"
    assert op.credit_account == "доходы"
    assert op.category == ""
    assert op.subcategory == ""
    assert op.comment == ""


def test_transfer_debit_operation():
    """Test transfer with negative amount (money leaving account)."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*1234": "Счёт ТБанка"},
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 22, 15, 46, 24),
            operation_amount=Decimal("-10000.00"),
            payment_amount=Decimal("-10000.00"),
            total_payment_amount=Decimal("-10000.00"),
            description="Между своими счетами",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == ""  # Empty for user to fill
    assert op.credit_account == "Счёт ТБанка"
    assert op.category == ""
    assert op.subcategory == ""


def test_transfer_credit_operation():
    """Test transfer with positive amount (money entering account)."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*5678": "Вклад ТБанка"},
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 22, 15, 46, 25),
            card_number="*5678",
            operation_amount=Decimal("10000.00"),
            payment_amount=Decimal("10000.00"),
            total_payment_amount=Decimal("10000.00"),
            description="Между своими счетами",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "Вклад ТБанка"
    assert op.credit_account == ""  # Empty for user to fill
    assert op.category == ""
    assert op.subcategory == ""


def test_account_mapping_fallback():
    """Test that unmapped card numbers fall back to card_number itself."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={},
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(card_number="*9999", description="Test"),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.credit_account == "*9999"  # Falls back to card_number


def test_category_fallback_to_uncategorized():
    """Test that expenses without mapping get uncategorized label."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={},
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(description="Unknown store"),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == "прочее"


def test_subcategory_mapping():
    """Test subcategory mapping with substring match."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["транспорт", "прочее"],
        account_mappings={},
        subcategory_mappings={
            "яндекс такси": "такси",
            "метро": "общественный",
        },
        description_mapping={"Яндекс": "транспорт"},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("-350.00"),
            payment_amount=Decimal("-350.00"),
            total_payment_amount=Decimal("-350.00"),
            description="Яндекс Такси поездка",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == "транспорт"
    assert op.subcategory == "такси"


def test_bank_category_mapping():
    """Test that T-Bank categories are mapped correctly."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["продукты", "кафе", "прочее"],
        account_mappings={},
        bank_category_mapping={
            "Супермаркеты": "продукты",
            "Рестораны": "кафе",
        },
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("-500.00"),
            payment_amount=Decimal("-500.00"),
            total_payment_amount=Decimal("-500.00"),
            bank_category="Супермаркеты",
            mcc="5411",
            description="Неизвестный магазин",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == "продукты"  # Mapped from "Супермаркеты"


def test_category_priority():
    """Test that description_mapping has priority over bank_category_mapping."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["продукты", "кафе", "прочее"],
        account_mappings={},
        bank_category_mapping={
            "Супермаркеты": "продукты",
        },
        subcategory_mappings={},
        description_mapping={
            "Старбакс": "кафе",
        },
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("-300.00"),
            payment_amount=Decimal("-300.00"),
            total_payment_amount=Decimal("-300.00"),
            bank_category="Супермаркеты",
            mcc="5812",
            description="Старбакс",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == "кафе"  # description_mapping wins


def test_brokerage_account_deposit():
    """Test that brokerage account deposits auto-fill target from transfer_account_mapping."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={
            "*7280": "Накопительный счет",
        },
        bank_category_mapping={},
        subcategory_mappings={},
        description_mapping={},
        transfer_account_mapping={
            "Пополнение брокерского счета": "ТИнвестиции",
        },
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 22, 14, 49, 37),
            card_number="*7280",
            operation_amount=Decimal("-7000.00"),
            payment_amount=Decimal("-7000.00"),
            total_payment_amount=Decimal("-7000.00"),
            bank_category="Переводы",
            description="Пополнение брокерского счета",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "ТИнвестиции"
    assert op.credit_account == "Накопительный счет"
    assert op.category == ""
    assert op.subcategory == ""


def test_bank_category_with_subcategory():
    """Test that bank_category_mapping can set both category and subcategory."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["автомобиль", "прочее"],
        account_mappings={},
        bank_category_mapping={
            "Заправки": BankCategoryMapping(
                category="автомобиль",
                subcategory="бензин"
            ),
        },
        subcategory_mappings={},
        description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("-2000.00"),
            payment_amount=Decimal("-2000.00"),
            total_payment_amount=Decimal("-2000.00"),
            bank_category="Заправки",
            mcc="5542",
            description="Лукойл АЗС",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == "автомобиль"
    assert op.subcategory == "бензин"


def test_income_category_mapping():
    """Test that income operations get category from income_description_mapping."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*5851": "Счет Тбанка"},
        subcategory_mappings={},
        description_mapping={},
        income_description_mapping={
            "РОМАШКА": "зарплата",
            "Петров А.": "подработка",
        },
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 15, 12, 0, 0),
            card_number="*5851",
            operation_amount=Decimal("50000.00"),
            payment_amount=Decimal("50000.00"),
            total_payment_amount=Decimal("50000.00"),
            bank_category="Пополнения",
            description='ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "РОМАШКА"',
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "Счет Тбанка"
    assert op.credit_account == "доходы"
    assert op.category == "зарплата"


def test_income_no_mapping_empty_category():
    """Test that income without mapping gets empty category."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={},
        subcategory_mappings={},
        description_mapping={},
        income_description_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_amount=Decimal("5000.00"),
            payment_amount=Decimal("5000.00"),
            total_payment_amount=Decimal("5000.00"),
            description="Неизвестный перевод",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.category == ""  # Empty, not "прочее"


def test_transfer_account_mapping():
    """Test that transfer_account_mapping auto-fills target account."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*8034": "Счет Тбанка"},
        subcategory_mappings={},
        description_mapping={},
        transfer_account_mapping={
            "Перевод на вклад": "Накопительный счет Тбанка",
        },
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 20, 10, 0, 0),
            card_number="*8034",
            operation_amount=Decimal("-15000.00"),
            payment_amount=Decimal("-15000.00"),
            total_payment_amount=Decimal("-15000.00"),
            bank_category="Переводы",
            description="Перевод на вклад",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == "Накопительный счет Тбанка"
    assert op.credit_account == "Счет Тбанка"
    assert op.category == ""


def test_transfer_no_mapping_empty():
    """Test that transfers without mapping leave target empty."""
    config = Config(
        version="1.0",
        settings=Settings(
            uncategorized_label="прочее",
            service_accounts=ServiceAccounts(income="доходы", expense="расходы"),
        ),
        categories=["прочее"],
        account_mappings={"*1234": "Счёт ТБанка"},
        subcategory_mappings={},
        description_mapping={},
        transfer_account_mapping={},
    )
    categorizer = Categorizer(config)

    operations = [
        make_operation(
            operation_date=datetime(2026, 1, 22, 15, 46, 24),
            operation_amount=Decimal("-10000.00"),
            payment_amount=Decimal("-10000.00"),
            total_payment_amount=Decimal("-10000.00"),
            description="Между своими счетами",
        ),
    ]

    result = categorizer.apply_double_entry(operations)

    assert len(result) == 1
    op = result[0]
    assert op.debit_account == ""  # Empty — no mapping
    assert op.credit_account == "Счёт ТБанка"
