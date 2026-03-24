from decimal import Decimal

from pydantic import BaseModel


class OcrLineItem(BaseModel):
    description: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None


class OcrResult(BaseModel):
    supplier_name: str | None = None
    supplier_afm: str | None = None
    supplier_country: str | None = None
    invoice_number: str | None = None
    date: str | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    vat_rate: Decimal | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    payment_method: str | None = None
    line_items: list[OcrLineItem] | None = None
    mark_number: str | None = None
    confidence: Decimal | None = None
