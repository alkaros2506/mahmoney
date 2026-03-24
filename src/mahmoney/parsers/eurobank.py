import csv
import io
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from mahmoney.models.enums import Category, PaymentMethod, Source
from mahmoney.schemas.expense import ExpenseCreate

logger = logging.getLogger(__name__)


class EurobankParser:
    bank_name = "eurobank"

    def parse(self, content: str, filename: str) -> tuple[list[ExpenseCreate], list[str]]:
        expenses: list[ExpenseCreate] = []
        errors: list[str] = []

        reader = csv.DictReader(io.StringIO(content))

        for i, row in enumerate(reader, start=2):
            try:
                # Eurobank CSV typically has: Ημερομηνία, Περιγραφή, Ποσό, Υπόλοιπο
                # or English: Date, Description, Amount, Balance
                date_str = row.get("Ημερομηνία") or row.get("Date") or ""
                description = row.get("Περιγραφή") or row.get("Description") or ""
                amount_str = row.get("Ποσό") or row.get("Amount") or "0"

                if not date_str or not description:
                    continue

                # Parse date (DD/MM/YYYY format common for Eurobank)
                date = self._parse_date(date_str)
                amount = self._parse_amount(amount_str)

                # Only import debits (negative amounts = expenses)
                if amount >= 0:
                    continue

                expenses.append(
                    ExpenseCreate(
                        supplier_name=description.strip(),
                        supplier_country="GR",
                        date=date,
                        total_amount=abs(amount),
                        currency="EUR",
                        payment_method=PaymentMethod.BANK_TRANSFER,
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
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        msg = f"Cannot parse date: {date_str}"
        raise ValueError(msg)

    def _parse_amount(self, amount_str: str) -> Decimal:
        # Handle Greek number format: 1.234,56 -> 1234.56
        cleaned = amount_str.strip().replace(" ", "")
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        return Decimal(cleaned)
