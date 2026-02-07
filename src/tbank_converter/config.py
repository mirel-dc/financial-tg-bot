"""Configuration management."""

from pathlib import Path
from typing import Any, Union

import yaml
from pydantic import BaseModel, Field, model_validator


class BankCategoryMapping(BaseModel):
    """T-Bank category mapping with optional subcategory."""

    category: str
    subcategory: str = ""


class ServiceAccounts(BaseModel):
    """Service accounts for double-entry bookkeeping."""

    income: str = "доходы"
    expense: str = "расходы"


class Settings(BaseModel):
    """General settings."""

    uncategorized_label: str = "прочее"
    default_currency: str = "RUB"
    date_format: str = "%d.%m.%Y %H:%M:%S"
    default_account: str = "Счет Тбанка"  # Used when card_number is empty
    service_accounts: ServiceAccounts = Field(default_factory=ServiceAccounts)


class Config(BaseModel):
    """Main configuration model."""

    version: str
    settings: Settings
    categories: list[str] = Field(min_length=1)
    account_mappings: dict[str, str] = Field(default_factory=dict)
    bank_category_mapping: dict[str, Union[str, BankCategoryMapping]] = Field(default_factory=dict)
    subcategory_mappings: dict[str, str] = Field(default_factory=dict)
    description_mapping: dict[str, str] = Field(default_factory=dict)
    income_description_mapping: dict[str, str] = Field(default_factory=dict)
    transfer_account_mapping: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_mappings(self) -> 'Config':
        """Validate that mapped categories exist in categories list."""
        category_set = set(self.categories)

        # Validate description_mapping
        for source, target in self.description_mapping.items():
            if target not in category_set:
                raise ValueError(
                    f"description_mapping: '{target}' (from '{source}') "
                    f"is not in categories list"
                )

        # Validate bank_category_mapping
        for source, target in self.bank_category_mapping.items():
            # Target can be either string (category only) or BankCategoryMapping object
            category = target if isinstance(target, str) else target.category
            if category not in category_set:
                raise ValueError(
                    f"bank_category_mapping: '{category}' (from T-Bank category '{source}') "
                    f"is not in categories list"
                )

        return self


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default config.

    Returns:
        Validated Config object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config validation fails.
    """
    if config_path is None:
        # Default config location (go up to package root)
        config_path = Path(__file__).parent.parent / "configs" / "default.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    return Config(**data)
