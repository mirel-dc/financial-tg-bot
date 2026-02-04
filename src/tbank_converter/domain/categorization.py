"""Categorization logic for operations."""

from tbank_converter.config import Config
from tbank_converter.domain.models import Operation


class Categorizer:
    """Categorizes operations based on configuration rules."""

    def __init__(self, config: Config):
        """Initialize categorizer.

        Args:
            config: Configuration with categories and mappings.
        """
        self.config = config

    def categorize(self, operation: Operation) -> str:
        """Determine category for an operation.

        Priority:
        1. Bank category (if present and not empty)
        2. Description mapping (exact match or substring)
        3. Fallback to uncategorized label

        Args:
            operation: Operation to categorize.

        Returns:
            Category name.
        """
        # Priority 1: Use bank category if available
        bank_category = operation.bank_category
        if bank_category and bank_category.strip():
            return bank_category.strip()

        # Priority 2: Check description mapping (exact match first)
        description = operation.description
        if description in self.config.description_mapping:
            return self.config.description_mapping[description]

        # Check substring matches in description
        for keyword, category in self.config.description_mapping.items():
            if keyword.lower() in description.lower():
                return category

        # Priority 3: Fallback to uncategorized
        return self.config.settings.uncategorized_label

    def apply_categories(self, operations: list[Operation]) -> None:
        """Apply categorization to all operations in-place.

        Updates bank_category field with final category (bank → description mapping → uncategorized).

        Args:
            operations: List of operations to categorize.
        """
        for operation in operations:
            # Update bank_category with the final determined category
            operation.bank_category = self.categorize(operation)
