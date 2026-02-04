"""Tests for categorization logic."""

from datetime import datetime
from decimal import Decimal

import pytest

from tbank_converter.config import Config, Settings
from tbank_converter.domain.categorization import Categorizer
from tbank_converter.domain.models import Operation


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        version="1.0",
        settings=Settings(uncategorized_label="Нет категории"),
        categories=["Супермаркеты", "Рестораны", "Хобби", "Подписки", "Нет категории"],
        description_mapping={
            "Леонардо": "Хобби",
            "Boosty.to": "Подписки",
            "Пятёрочка": "Супермаркеты",
        },
    )


@pytest.fixture
def sample_operation():
    """Create sample operation."""
    return Operation(
        operation_date=datetime.now(),
        payment_date=None,
        card_number="*1234",
        status="OK",
        operation_amount=Decimal("-100"),
        operation_currency="RUB",
        payment_amount=Decimal("-100"),
        payment_currency="RUB",
        cashback=Decimal("0"),
        bank_category="",  # Empty by default
        mcc="0000",
        description="Test",
        bonus_count="0",
        investment_amount=Decimal("0"),
        total_payment_amount=Decimal("-100"),
    )


def test_categorize_bank_category_has_priority(config, sample_operation):
    """Test that bank category has priority over description mapping."""
    categorizer = Categorizer(config)
    sample_operation.bank_category = "Супермаркеты"
    sample_operation.description = "Леонардо"  # Would match "Хобби" by description

    category = categorizer.categorize(sample_operation)
    assert category == "Супермаркеты"  # Bank category wins


def test_categorize_by_description_exact(config, sample_operation):
    """Test categorization by exact description match when bank category is empty."""
    categorizer = Categorizer(config)
    sample_operation.bank_category = ""
    sample_operation.description = "Леонардо"

    category = categorizer.categorize(sample_operation)
    assert category == "Хобби"


def test_categorize_by_description_substring(config, sample_operation):
    """Test categorization by substring in description when bank category is empty."""
    categorizer = Categorizer(config)
    sample_operation.bank_category = ""
    sample_operation.description = "Покупка в Пятёрочка №123"

    category = categorizer.categorize(sample_operation)
    assert category == "Супермаркеты"


def test_categorize_uncategorized(config, sample_operation):
    """Test fallback to uncategorized when no matches."""
    categorizer = Categorizer(config)
    sample_operation.bank_category = ""
    sample_operation.description = "Unknown Transaction"

    category = categorizer.categorize(sample_operation)
    assert category == "Нет категории"


def test_apply_categories(config, sample_operation):
    """Test applying categories to operations list updates bank_category."""
    categorizer = Categorizer(config)
    operations = [sample_operation]
    sample_operation.bank_category = ""
    sample_operation.description = "Леонардо"

    categorizer.apply_categories(operations)

    assert operations[0].bank_category == "Хобби"
