"""Conversion pipeline orchestrator."""

from pathlib import Path

from tbank_converter.config import Config, load_config
from tbank_converter.domain.categorization import Categorizer
from tbank_converter.domain.models import Operation, Report
from tbank_converter.domain.transform import DataTransformer
from tbank_converter.io.csv_reader import TBankCSVReader
from tbank_converter.io.xlsx_writer import XLSXWriter


class ConversionPipeline:
    """Orchestrates the CSV to XLSX conversion process."""

    def __init__(self, config: Config):
        """Initialize pipeline.

        Args:
            config: Configuration with categories and mappings.
        """
        self.config = config
        self.transformer = DataTransformer(date_format=config.settings.date_format)
        self.categorizer = Categorizer(config)

    def run(self, input_csv: Path, output_xlsx: Path) -> Report:
        """Run the conversion pipeline.

        Args:
            input_csv: Path to T-Bank CSV file.
            output_xlsx: Path for output XLSX file.

        Returns:
            Report with conversion statistics.

        Raises:
            ValueError: If CSV cannot be parsed or transformed.
            FileNotFoundError: If input CSV doesn't exist.
        """
        # Step 1: Read CSV
        reader = TBankCSVReader(input_csv)

        # Step 2: Transform and collect operations
        operations: list[Operation] = []
        for raw_data in reader.read():
            operation = self.transformer.transform_operation(raw_data)
            operations.append(operation)

        if not operations:
            raise ValueError("No operations found in CSV file")

        # Step 3: Merge paired inter-account transfers
        operations = self.transformer.merge_paired_transfers(operations)

        # Step 4: Apply double-entry bookkeeping logic
        operations = self.categorizer.apply_double_entry(operations)

        # Step 5: Collect unique categories from operations (for reporting)
        unique_categories = sorted(set(op.category for op in operations if op.category))

        # Step 6: Build report
        report = Report(
            operations=operations,
            categories=unique_categories,
        )

        # Step 7: Write XLSX
        writer = XLSXWriter(report)
        writer.write(output_xlsx)

        return report


def convert(
    input_csv: Path,
    output_xlsx: Path,
    config_path: Path | None = None,
) -> Report:
    """Convert T-Bank CSV to XLSX (convenience function).

    Args:
        input_csv: Path to T-Bank CSV file.
        output_xlsx: Path for output XLSX file.
        config_path: Path to config file (optional).

    Returns:
        Report with conversion statistics.
    """
    config = load_config(config_path)
    pipeline = ConversionPipeline(config)
    return pipeline.run(input_csv, output_xlsx)
