from typing import Protocol

from mahmoney.schemas.expense import ExpenseCreate


class BaseCSVParser(Protocol):
    bank_name: str

    def parse(self, content: str, filename: str) -> tuple[list[ExpenseCreate], list[str]]:
        """Parse CSV content into expense records.

        Returns (expenses, errors).
        """
        ...
