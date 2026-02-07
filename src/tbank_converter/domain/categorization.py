"""Categorization logic for operations with double-entry bookkeeping."""

from tbank_converter.config import BankCategoryMapping, Config
from tbank_converter.domain.models import Operation


class Categorizer:
    """Categorizes operations based on double-entry bookkeeping rules."""

    def __init__(self, config: Config):
        """Initialize categorizer.

        Args:
            config: Configuration with categories and mappings.
        """
        self.config = config
        self.description_mapping = config.description_mapping
        self.bank_category_mapping = config.bank_category_mapping
        self.subcategory_mapping = config.subcategory_mappings
        self.account_mappings = config.account_mappings
        self.service_accounts = config.settings.service_accounts
        self.income_description_mapping = config.income_description_mapping
        self.transfer_account_mapping = config.transfer_account_mapping

    def apply_double_entry(self, operations: list[Operation]) -> list[Operation]:
        """Apply double-entry bookkeeping logic to operations.

        For each operation, determines:
        - Debit account (where money goes)
        - Credit account (where money comes from)
        - Category and subcategory (only for expenses)

        Rules:
        - Expense (amount < 0, not transfer): debit="расходы", credit=account, categorized
        - Income (amount > 0, not transfer): debit=account, credit="доходы", no category
        - Transfer ("Между своими счетами"): one field empty for manual entry, no category

        Args:
            operations: List of operations to process.

        Returns:
            Same list with double-entry fields populated.
        """
        for op in operations:
            # Merged transfer: both accounts already filled, just resolve names
            if op.debit_account and op.credit_account:
                op.debit_account = self._resolve_account_name(op.debit_account)
                op.credit_account = self._resolve_account_name(op.credit_account)
                op.category = ""
                op.subcategory = ""
                op.comment = ""
                continue

            # Determine operation type
            is_transfer = (
                "между своими счетами" in op.description.lower()
                or self._matches_transfer_mapping(op.description)
            )
            is_expense = op.operation_amount < 0 and not is_transfer
            is_income = op.operation_amount > 0 and not is_transfer

            # Get account name from mapping
            # Priority: 1. account_mappings, 2. card_number if not empty, 3. default_account
            if op.card_number in self.account_mappings:
                account_name = self.account_mappings[op.card_number]
            elif op.card_number:
                account_name = op.card_number
            else:
                # Empty card_number - use default account
                account_name = self.config.settings.default_account

            # Apply double-entry logic
            if is_expense:
                # Expense: money goes to "expenses", comes from account
                op.debit_account = self.service_accounts.expense  # "расходы"
                op.credit_account = account_name
                category, bank_subcategory = self._get_category(op)
                op.category = category
                op.subcategory = self._get_subcategory(op, bank_subcategory)

            elif is_income:
                # Income: money goes to account, comes from "income"
                op.debit_account = account_name
                op.credit_account = self.service_accounts.income  # "доходы"
                op.category = self._get_income_category(op)
                op.subcategory = ""

            elif is_transfer:
                # Transfer: auto-fill target from mapping, or leave empty
                target = self._get_transfer_target(op.description)
                if op.operation_amount < 0:
                    # Money leaving account
                    op.debit_account = target
                    op.credit_account = account_name
                else:
                    # Money entering account
                    op.debit_account = account_name
                    op.credit_account = target

                op.category = ""
                op.subcategory = ""

            # Comment is always empty (for user to fill)
            op.comment = ""

        return operations

    def _resolve_account_name(self, raw_name: str) -> str:
        """Resolve raw card number to account name via account_mappings.

        Args:
            raw_name: Raw card number (e.g., "*8878") or already-resolved name.

        Returns:
            Mapped account name if found, otherwise the original value.
        """
        return self.account_mappings.get(raw_name, raw_name)

    def _matches_transfer_mapping(self, description: str) -> bool:
        """Check if description matches any transfer_account_mapping key."""
        desc_lower = description.lower()
        return any(key.lower() in desc_lower for key in self.transfer_account_mapping)

    def _get_transfer_target(self, description: str) -> str:
        """Get target account name from transfer_account_mapping."""
        desc_lower = description.lower()
        for key, account in self.transfer_account_mapping.items():
            if key.lower() in desc_lower:
                return account
        return ""

    def _get_income_category(self, op: Operation) -> str:
        """Get income category from income_description_mapping (substring match)."""
        desc_lower = op.description.lower()
        for keyword, category in self.income_description_mapping.items():
            if keyword.lower() in desc_lower:
                return category
        return ""

    def _get_category(self, op: Operation) -> tuple[str, str]:
        """Determine category for an expense operation.

        Priority:
        1. Exact match in description_mapping
        2. Substring match in description_mapping (case-insensitive)
        3. T-Bank category mapping (bank_category field)
        4. Fallback to uncategorized label ("прочее")

        Args:
            op: Operation to categorize.

        Returns:
            Tuple of (category, bank_subcategory). bank_subcategory is non-empty
            only when category comes from bank_category_mapping with subcategory.
        """
        description = op.description

        # Priority 1: Exact match in description_mapping
        if description in self.description_mapping:
            return self.description_mapping[description], ""

        # Priority 2: Substring match in description_mapping (case-insensitive)
        description_lower = description.lower()
        for keyword, category in self.description_mapping.items():
            if keyword.lower() in description_lower:
                return category, ""

        # Priority 3: T-Bank category mapping
        if op.bank_category and op.bank_category in self.bank_category_mapping:
            mapping = self.bank_category_mapping[op.bank_category]
            # Can be either string (category only) or BankCategoryMapping object
            if isinstance(mapping, str):
                return mapping, ""
            return mapping.category, mapping.subcategory

        # Priority 4: Fallback to uncategorized
        return self.config.settings.uncategorized_label, ""

    def _get_subcategory(self, op: Operation, bank_subcategory: str = "") -> str:
        """Determine subcategory for an expense operation.

        Priority:
        1. bank_subcategory (from bank_category_mapping, passed by caller)
        2. Substring match in subcategory_mappings (case-insensitive)

        Args:
            op: Operation to get subcategory for.
            bank_subcategory: Subcategory from bank_category_mapping (if any).

        Returns:
            Subcategory name, or empty string if not found.
        """
        if bank_subcategory:
            return bank_subcategory

        description_lower = op.description.lower()

        for keyword, subcategory in self.subcategory_mapping.items():
            if keyword.lower() in description_lower:
                return subcategory

        return ""  # No subcategory found
