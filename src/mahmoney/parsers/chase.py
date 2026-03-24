import csv
import io
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from mahmoney.models.enums import Category, PaymentMethod, Source
from mahmoney.schemas.expense import ExpenseCreate

logger = logging.getLogger(__name__)


class ChaseParser:
    bank_name = "chase"

    def parse(self, content: str, filename: str) -> tuple[list[ExpenseCreate], list[str]]:
        expenses: list[ExpenseCreate] = []
        errors: list[str] = []

        reader = csv.DictReader(io.StringIO(content))

        for i, row in enumerate(reader, start=2):
            try:
                # Chase CSV: Transaction Date, Post Date, Description, Category, Type, Amount, Memo
                date_str = row.get("Transaction Date") or row.get("Posting Date") or ""
                description = row.get("Description") or ""
                amount_str = row.get("Amount") or "0"

                if not date_str or not description:
                    continue

                date = datetime.strptime(date_str.strip(), "%m/%d/%Y").replace(
                    tzinfo=UTC
                )
                amount = Decimal(amount_str.strip())

                # Chase uses negative for charges
                if amount >= 0:
                    continue

                expenses.append(
                    ExpenseCreate(
                        supplier_name=description.strip(),
                        supplier_country="US",
                        date=date,
                        total_amount=abs(amount),
                        currency="USD",
                        payment_method=PaymentMethod.CARD,
                        category=Category.OTHER,
                        source=Source.CSV_IMPORT,
                        source_file=filename,
                    )
                )
            except (ValueError, InvalidOperation) as e:
                errors.append(f"Row {i}: {e}")

        return expenses, errors
