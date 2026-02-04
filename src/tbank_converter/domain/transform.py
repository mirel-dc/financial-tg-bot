"""Data transformation utilities."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from tbank_converter.domain.models import Operation


class DataTransformer:
    """Transforms raw CSV data into typed Operation objects."""

    def __init__(self, date_format: str = "%d.%m.%Y %H:%M:%S"):
        """Initialize transformer.

        Args:
            date_format: Date format string for parsing.
        """
        self.date_format = date_format

    def transform_operation(self, raw_data: dict[str, str]) -> Operation:
        """Transform raw CSV data into Operation object.

        Args:
            raw_data: Dictionary with string values from CSV.

        Returns:
            Operation object with properly typed fields.

        Raises:
            ValueError: If data cannot be parsed.
        """
        try:
            # Parse payment date (may be in different format)
            payment_date = None
            if raw_data["payment_date"].strip():
                try:
                    payment_date = self.parse_date(raw_data["payment_date"])
                except ValueError:
                    # Try date-only format
                    payment_date = self.parse_date(raw_data["payment_date"], "%d.%m.%Y")

            return Operation(
                operation_date=self.parse_date(raw_data["operation_date"]),
                payment_date=payment_date,
                card_number=self.normalize_string(raw_data["card_number"]),
                status=self.normalize_string(raw_data["status"]),
                operation_amount=self.parse_amount(raw_data["operation_amount"]),
                operation_currency=self.normalize_string(raw_data["operation_currency"]),
                payment_amount=self.parse_amount(raw_data["payment_amount"]),
                payment_currency=self.normalize_string(raw_data["payment_currency"]),
                cashback=self.parse_amount(raw_data["cashback"]),
                bank_category=self.normalize_string(raw_data["bank_category"]),
                mcc=self.normalize_string(raw_data["mcc"]),
                description=self.normalize_string(raw_data["description"]),
                bonus_count=self.normalize_string(raw_data["bonus_count"]),
                investment_amount=self.parse_amount(raw_data["investment_amount"]),
                total_payment_amount=self.parse_amount(raw_data["total_payment_amount"]),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to transform operation: {e}") from e

    @staticmethod
    def parse_date(date_str: str, date_format: str = "%d.%m.%Y %H:%M:%S") -> datetime:
        """Parse date string to datetime object.

        Args:
            date_str: Date string (e.g., "30.01.2026 19:32:00").
            date_format: Format string for parsing.

        Returns:
            Parsed datetime object.

        Raises:
            ValueError: If date cannot be parsed.
        """
        try:
            return datetime.strptime(date_str.strip(), date_format)
        except ValueError as e:
            raise ValueError(f"Invalid date format: '{date_str}'") from e

    @staticmethod
    def parse_amount(amount_str: str) -> Decimal:
        """Parse amount string to Decimal.

        Converts comma to dot and handles empty strings.

        Args:
            amount_str: Amount string (e.g., "-2234,86" or "1000,00").

        Returns:
            Decimal value.

        Raises:
            ValueError: If amount cannot be parsed.
        """
        try:
            # Handle empty strings
            if not amount_str.strip():
                return Decimal("0")

            # Replace comma with dot (T-Bank uses comma as decimal separator)
            normalized = amount_str.strip().replace(",", ".")

            return Decimal(normalized)
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid amount format: '{amount_str}'") from e

    @staticmethod
    def normalize_string(value: str) -> str:
        """Normalize string value (trim whitespace).

        Args:
            value: Raw string value.

        Returns:
            Normalized string.
        """
        return value.strip()
