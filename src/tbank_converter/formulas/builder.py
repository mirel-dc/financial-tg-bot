"""Excel formula builders."""

from typing import NamedTuple


class CellRange(NamedTuple):
    """Excel cell range definition."""

    start_row: int
    end_row: int
    column: str


class FormulaBuilder:
    """Builds Excel formulas for the report."""

    @staticmethod
    def final_category_formula(row: int, manual_col: str, auto_col: str) -> str:
        """Build formula for final category column.

        Returns manual category if not empty, otherwise auto category.

        Args:
            row: Row number.
            manual_col: Column letter for manual category.
            auto_col: Column letter for auto category.

        Returns:
            Excel IF formula.
        """
        return f'=IF({manual_col}{row}<>"", {manual_col}{row}, {auto_col}{row})'

    @staticmethod
    def sumif_formula(
        data_range: CellRange,
        category: str,
        sum_range: CellRange,
    ) -> str:
        """Build SUMIF formula for category sum.

        Args:
            data_range: Range with category values.
            category: Category to sum.
            sum_range: Range with amounts to sum.

        Returns:
            Excel SUMIF formula.
        """
        criteria_range = f"${data_range.column}${data_range.start_row}:${data_range.column}${data_range.end_row}"
        values_range = f"${sum_range.column}${sum_range.start_row}:${sum_range.column}${sum_range.end_row}"
        return f'=SUMIF({criteria_range}, "{category}", {values_range})'

    @staticmethod
    def countif_formula(data_range: CellRange, category: str) -> str:
        """Build COUNTIF formula for category count.

        Args:
            data_range: Range with category values.
            category: Category to count.

        Returns:
            Excel COUNTIF formula.
        """
        range_ref = f"${data_range.column}${data_range.start_row}:${data_range.column}${data_range.end_row}"
        return f'=COUNTIF({range_ref}, "{category}")'

    @staticmethod
    def sum_formula(sum_range: CellRange) -> str:
        """Build SUM formula for total.

        Args:
            sum_range: Range with amounts to sum.

        Returns:
            Excel SUM formula.
        """
        range_ref = f"${sum_range.column}${sum_range.start_row}:${sum_range.column}${sum_range.end_row}"
        return f"=SUM({range_ref})"
