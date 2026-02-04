"""XLSX writer for converted operations."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from tbank_converter.config import Config
from tbank_converter.domain.models import Report
from tbank_converter.formulas.builder import CellRange, FormulaBuilder


# Column indices (1-based for openpyxl)
COL_DATE = 1  # A
COL_DESCRIPTION = 2  # B
COL_CATEGORY = 3  # C
COL_AMOUNT = 4  # D

# Summary columns (to the right)
COL_SUMMARY_CATEGORY = 6  # F
COL_SUMMARY_SUM = 7  # G
COL_SUMMARY_COUNT = 8  # H

# Column headers
HEADERS = [
    "Дата операции",
    "Описание",
    "Категория",
    "Сумма операции",
]


class XLSXWriter:
    """Writes Report to XLSX file with formulas."""

    def __init__(self, report: Report, config: Config):
        """Initialize writer.

        Args:
            report: Report object with operations and categories.
            config: Configuration with colors and settings.
        """
        self.report = report
        self.config = config
        self.wb = Workbook()
        self.ws = self.wb.active

        # Set sheet name based on report period
        if report.period_start:
            # Format: "January2026"
            sheet_name = report.period_start.strftime("%B%Y")
        else:
            sheet_name = "Операции"

        # Excel sheet names max length is 31 chars
        self.ws.title = sheet_name[:31]

    def write(self, output_path: Path) -> None:
        """Write report to XLSX file.

        Args:
            output_path: Path for output XLSX file.
        """
        self._write_header()
        data_end_row = self._write_data()
        self._write_summary(data_end_row)  # Now writes to the right
        self._apply_styles(data_end_row)
        self._apply_conditional_formatting(data_end_row)
        self._set_column_widths()

        self.wb.save(output_path)

    def _write_header(self) -> None:
        """Write header row with column names."""
        for col_idx, header in enumerate(HEADERS, start=1):
            cell = self.ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

    def _write_data(self) -> int:
        """Write operation data rows.

        Returns:
            Last row number with data.
        """
        for row_idx, op in enumerate(self.report.operations, start=2):
            # Date
            self.ws.cell(row=row_idx, column=COL_DATE, value=op.operation_date.strftime("%d.%m.%Y %H:%M:%S"))

            # Description
            self.ws.cell(row=row_idx, column=COL_DESCRIPTION, value=op.description)

            # Category (from bank)
            self.ws.cell(row=row_idx, column=COL_CATEGORY, value=op.bank_category)

            # Amount
            self.ws.cell(row=row_idx, column=COL_AMOUNT, value=float(op.operation_amount))

        return len(self.report.operations) + 1  # +1 for header row

    def _write_summary(self, data_end_row: int) -> None:
        """Write summary block with all categories from config.

        Args:
            data_end_row: Last row with data.
        """
        # Summary starts at row 1, to the right of main data
        summary_start_row = 1

        # Headers
        self.ws.cell(row=summary_start_row, column=COL_SUMMARY_CATEGORY, value="Категория").font = Font(bold=True)
        self.ws.cell(row=summary_start_row, column=COL_SUMMARY_SUM, value="Сумма").font = Font(bold=True)
        self.ws.cell(row=summary_start_row, column=COL_SUMMARY_COUNT, value="Операций").font = Font(bold=True)

        # Style summary headers
        for col in [COL_SUMMARY_CATEGORY, COL_SUMMARY_SUM, COL_SUMMARY_COUNT]:
            cell = self.ws.cell(row=summary_start_row, column=col)
            cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Category ranges for formulas - use large range to allow manual additions
        category_range = CellRange(
            start_row=2,
            end_row=1000,
            column=get_column_letter(COL_CATEGORY),
        )
        amount_range = CellRange(
            start_row=2,
            end_row=1000,
            column=get_column_letter(COL_AMOUNT),
        )

        # Use ALL categories from config - this allows adding any category from config
        # Categories will show even with zero amounts, giving users flexibility
        ignore_label = self.config.settings.ignore_label
        categories_for_summary = [cat for cat in self.config.categories if cat != ignore_label]

        # Category rows
        current_row = summary_start_row + 1
        for category in categories_for_summary:
            # Category name with color
            category_cell = self.ws.cell(row=current_row, column=COL_SUMMARY_CATEGORY, value=category)

            # Apply category color to the category cell
            if category in self.config.category_colors:
                color = self.config.category_colors[category]
                category_cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

            # Sum formula
            sum_formula = FormulaBuilder.sumif_formula(category_range, category, amount_range)
            self.ws.cell(row=current_row, column=COL_SUMMARY_SUM, value=sum_formula)

            # Count formula
            count_formula = FormulaBuilder.countif_formula(category_range, category)
            self.ws.cell(row=current_row, column=COL_SUMMARY_COUNT, value=count_formula)

            current_row += 1

        # Total row - sum only displayed categories (excluding ignore category)
        total_row = current_row + 1
        total_cell = self.ws.cell(row=total_row, column=COL_SUMMARY_CATEGORY, value="ИТОГО")
        total_cell.font = Font(bold=True)

        # Total sum formula - sum all amounts in summary column
        summary_start = summary_start_row + 1
        summary_end = current_row
        total_formula = f"=SUM($G${summary_start}:$G${summary_end})"

        total_sum_cell = self.ws.cell(row=total_row, column=COL_SUMMARY_SUM, value=total_formula)
        total_sum_cell.font = Font(bold=True)

    def _apply_styles(self, data_end_row: int) -> None:
        """Apply number formatting and alignment.

        Args:
            data_end_row: Last row with data.
        """
        # Amount column in main data: number format with currency
        for row in range(2, data_end_row + 1):
            cell = self.ws.cell(row=row, column=COL_AMOUNT)
            cell.number_format = '#,##0.00 "₽"'
            cell.alignment = Alignment(horizontal="right")

        # Summary amounts: apply format to a reasonable range
        # Since summary is dynamic, we apply format to a larger range
        summary_data_start = 2  # Summary starts at row 2 (after header)
        summary_end = summary_data_start + 30  # Format up to 30 rows for dynamic array

        for row in range(summary_data_start, summary_end + 1):
            cell = self.ws.cell(row=row, column=COL_SUMMARY_SUM)
            cell.number_format = '#,##0.00 "₽"'
            cell.alignment = Alignment(horizontal="right")

    def _apply_conditional_formatting(self, data_end_row: int) -> None:
        """Apply conditional formatting for category colors.

        Args:
            data_end_row: Last row with data.
        """
        # Define range for main data (all columns in data rows)
        data_range = f"A2:D{data_end_row}"

        # Create conditional formatting rule for each category
        for category, color in self.config.category_colors.items():
            # Escape quotes in category name for formula
            category_escaped = category.replace('"', '""')

            # Formula: if category column equals this category
            # $C2 refers to the category column (COL_CATEGORY = 3 = C)
            formula = f'$C2="{category_escaped}"'

            # Create fill pattern
            fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

            # Create rule
            rule = FormulaRule(formula=[formula], fill=fill, stopIfTrue=True)

            # Apply rule to data range
            self.ws.conditional_formatting.add(data_range, rule)

        # Apply conditional formatting to summary category column as well
        # Since summary is dynamic, apply to a larger range
        ignore_label = self.config.settings.ignore_label
        summary_end_row = 2 + 30  # Format up to 30 rows for dynamic categories

        summary_category_range = f"F2:F{summary_end_row}"

        for category, color in self.config.category_colors.items():
            if category == ignore_label:
                continue

            category_escaped = category.replace('"', '""')
            formula = f'$F2="{category_escaped}"'
            fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            rule = FormulaRule(formula=[formula], fill=fill, stopIfTrue=True)
            self.ws.conditional_formatting.add(summary_category_range, rule)

    def _set_column_widths(self) -> None:
        """Set column widths for better readability."""
        column_widths = {
            COL_DATE: 20,  # Date
            COL_DESCRIPTION: 50,  # Description
            COL_CATEGORY: 25,  # Category
            COL_AMOUNT: 18,  # Amount
            # Empty column E for spacing
            COL_SUMMARY_CATEGORY: 25,  # Summary: Category
            COL_SUMMARY_SUM: 18,  # Summary: Sum
            COL_SUMMARY_COUNT: 12,  # Summary: Count
        }

        for col_idx, width in column_widths.items():
            col_letter = get_column_letter(col_idx)
            self.ws.column_dimensions[col_letter].width = width
