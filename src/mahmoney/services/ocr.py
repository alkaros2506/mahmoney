import base64
import json
import logging

import httpx

from mahmoney.config import get_settings
from mahmoney.schemas.ocr import OcrResult

logger = logging.getLogger(__name__)

OCR_SYSTEM_PROMPT = """You are an invoice/receipt OCR extraction system. Extract structured data from the provided image.

Return ONLY valid JSON matching this schema:
{
  "supplier_name": "string or null",
  "supplier_afm": "string or null (Greek tax ID / ΑΦΜ if visible)",
  "supplier_country": "string or null (2-letter ISO code, e.g. GR, US, DE)",
  "invoice_number": "string or null",
  "date": "string or null (YYYY-MM-DD format)",
  "net_amount": number or null,
  "vat_amount": number or null,
  "vat_rate": number or null (percentage, e.g. 24 for 24%),
  "total_amount": number or null,
  "currency": "string or null (3-letter ISO code, e.g. EUR, USD)",
  "payment_method": "string or null (cash, card, or bank_transfer)",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "amount": number}] or null,
  "mark_number": "string or null (ΜΑΡΚ number if visible on Greek invoices)",
  "confidence": number (0.0 to 1.0, your confidence in the extraction)
}

Important:
- For Greek invoices, look for ΑΦΜ (tax ID) and ΜΑΡΚ number
- Always try to separate net amount and VAT if visible
- Use null for fields you cannot determine
- Return ONLY the JSON object, no other text"""


async def process_receipt(image_bytes: bytes) -> OcrResult | None:
    settings = get_settings()

    if not settings.vlm_api_key:
        logger.warning("VLM API key not configured, skipping OCR")
        return None

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": settings.vlm_model,
        "messages": [
            {"role": "system", "content": OCR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                    {
                        "type": "text",
                        "text": "Extract all data from this invoice/receipt.",
                    },
                ],
            },
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.vlm_api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.vlm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return OcrResult.model_validate(parsed)

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            logger.warning("OCR attempt %d failed: %s", attempt + 1, e)
            if attempt == max_retries - 1:
                logger.exception("OCR failed after %d attempts", max_retries)
                return None

    return None
