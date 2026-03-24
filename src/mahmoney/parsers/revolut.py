import csv
import io
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from mahmoney.models.enums import Category, PaymentMethod, Source
from mahmoney.schemas.expense import ExpenseCreate

logger = logging.getLogger(__name__)


class RevolutParser:
    bank_name = "revolut"

    def parse(self, content: str, filename: str) -> tuple[list[ExpenseCreate], list[str]]:
        expenses: list[ExpenseCreate] = []
        errors: list[str] = []

        reader = csv.DictReader(io.StringIO(content))

        for i, row in enumerate(reader, start=2):
            try:
                # Revolut CSV: Type, Product, Started Date, Completed Date,
                # Description, Amount, Fee, Currency, State, Balance
                date_str = row.get("Completed Date") or row.get("Started Date") or ""
                description = row.get("Description") or ""
                amount_str = row.get("Amount") or "0"
                currency = row.get("Currency") or "EUR"
                state = row.get("State") or ""

                if not date_str or not description:
                    continue

                # Skip non-completed transactions
                if state.lower() not in ("completed", ""):
                    continue

                date = self._parse_date(date_str)
                amount = Decimal(amount_str.strip())

                # Negative = expense
                if amount >= 0:
                    continue

                expenses.append(
                    ExpenseCreate(
                        supplier_name=description.strip(),
                        supplier_country="GR",  # Default, user can edit
                        date=date,
                        total_amount=abs(amount),
                        currency=currency.strip().upper(),
                        payment_method=PaymentMethod.CARD,
                        category=Category.OTHER,
                        source=Source.CSV_IMPORT,
                        source_file=filename,
                    )
                )
            except (ValueError, InvalidOperation) as e:
                errors.append(f"Row {i}: {e}")

        return expenses, errors

    def _parse_date(self, date_str: str) -> datetime:
        date_str = date_str.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %b %Y"):
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        msg = f"Cannot parse date: {date_str}"
        raise ValueError(msg)
