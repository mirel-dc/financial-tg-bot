"""T-Bank CSV reader."""

from collections.abc import Iterator
from pathlib import Path


# T-Bank CSV format constants
DELIMITER = ";"
ENCODING = "utf-8"

# Expected column headers from T-Bank CSV
EXPECTED_HEADERS = [
    "Дата операции",
    "Дата платежа",
    "Номер карты",
    "Статус",
    "Сумма операции",
    "Валюта операции",
    "Сумма платежа",
    "Валюта платежа",
    "Кэшбэк",
    "Категория",
    "MCC",
    "Описание",
    "Бонусы (включая кэшбэк)",
    "Округление на инвесткопилку",
    "Сумма операции с округлением",
]

# Mapping from CSV column names to Operation model fields
COLUMN_MAPPING = {
    "Дата операции": "operation_date",
    "Дата платежа": "payment_date",
    "Номер карты": "card_number",
    "Статус": "status",
    "Сумма операции": "operation_amount",
    "Валюта операции": "operation_currency",
    "Сумма платежа": "payment_amount",
    "Валюта платежа": "payment_currency",
    "Кэшбэк": "cashback",
    "Категория": "bank_category",
    "MCC": "mcc",
    "Описание": "description",
    "Бонусы (включая кэшбэк)": "bonus_count",
    "Округление на инвесткопилку": "investment_amount",
    "Сумма операции с округлением": "total_payment_amount",
}


class TBankCSVReader:
    """Reader for T-Bank CSV export files."""

    def __init__(self, csv_path: Path):
        """Initialize reader.

        Args:
            csv_path: Path to T-Bank CSV file.

        Raises:
            FileNotFoundError: If CSV file doesn't exist.
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        self.csv_path = csv_path

    def read(self) -> Iterator[dict[str, str]]:
        """Read CSV file and yield operations as dictionaries.

        T-Bank exports CSV in format: "value1"";"value2"";"value3""
        This is non-standard and requires custom parsing.

        Yields:
            Dictionary with mapped field names (operation_date, description, etc.)

        Raises:
            ValueError: If CSV headers don't match expected format.
        """
        with open(self.csv_path, "r", encoding=ENCODING) as f:
            lines = f.readlines()

        if not lines:
            raise ValueError("CSV file is empty")

        # Parse header
        headers = self._parse_line(lines[0])
        self._validate_headers(headers)

        # Parse data rows
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue

            row = self._parse_line(line)
            if len(row) != len(headers):
                continue  # Skip malformed rows

            row_dict = dict(zip(headers, row))
            yield self._map_row(row_dict)

    def _parse_line(self, line: str) -> list[str]:
        """Parse a T-Bank CSV line.

        T-Bank format: "value1";"value2";"value3"

        Args:
            line: Raw CSV line.

        Returns:
            List of values.
        """
        line = line.strip()

        # Split by ";" pattern (this is the actual field separator in T-Bank CSV)
        values = line.split('";\"')

        # Clean up each value
        cleaned_values = []
        for value in values:
            # Remove leading and trailing quotes
            value = value.strip('"')
            # Handle escaped quotes within values (if any)
            value = value.replace('""', '"')
            cleaned_values.append(value)

        return cleaned_values

    def _validate_headers(self, actual_headers: list[str]) -> None:
        """Validate that CSV has expected headers.

        Args:
            actual_headers: Headers from CSV file.

        Raises:
            ValueError: If headers don't match expected format.
        """
        if len(actual_headers) != len(EXPECTED_HEADERS):
            raise ValueError(
                f"Expected {len(EXPECTED_HEADERS)} columns, "
                f"got {len(actual_headers)}. "
                f"Is this a T-Bank CSV export?"
            )

        for expected, actual in zip(EXPECTED_HEADERS, actual_headers):
            if expected != actual:
                raise ValueError(
                    f"Expected column '{expected}', got '{actual}'. "
                    f"Is this a T-Bank CSV export?"
                )

    def _map_row(self, row: dict[str, str]) -> dict[str, str]:
        """Map CSV column names to model field names.

        Args:
            row: Dictionary with CSV column names as keys.

        Returns:
            Dictionary with model field names as keys.
        """
        return {
            COLUMN_MAPPING[csv_col]: value
            for csv_col, value in row.items()
            if csv_col in COLUMN_MAPPING
        }
