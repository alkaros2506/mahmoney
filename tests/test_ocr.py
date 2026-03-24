import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from mahmoney.services.ocr import process_receipt

MOCK_VLM_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": json.dumps(
                    {
                        "supplier_name": "ΣΚΛΑΒΕΝΙΤΗΣ",
                        "supplier_afm": "094aborteduage",
                        "supplier_country": "GR",
                        "invoice_number": "A-12345",
                        "date": "2026-01-15",
                        "net_amount": 40.32,
                        "vat_amount": 9.68,
                        "vat_rate": 24,
                        "total_amount": 50.00,
                        "currency": "EUR",
                        "payment_method": "card",
                        "line_items": [
                            {
                                "description": "Milk 1L",
                                "quantity": 2,
                                "unit_price": 1.50,
                                "amount": 3.00,
                            }
                        ],
                        "mark_number": None,
                        "confidence": 0.92,
                    }
                )
            }
        }
    ]
}


@pytest.mark.asyncio
async def test_process_receipt_success():
    mock_request = httpx.Request("POST", "https://api.test.com/v1/chat/completions")
    mock_response = httpx.Response(200, json=MOCK_VLM_RESPONSE, request=mock_request)

    with (
        patch("mahmoney.services.ocr.get_settings") as mock_settings,
        patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response),
    ):
        mock_settings.return_value.vlm_api_key = "test-key"
        mock_settings.return_value.vlm_api_url = "https://api.test.com/v1"
        mock_settings.return_value.vlm_model = "test-model"

        result = await process_receipt(b"fake-image-bytes")

    assert result is not None
    assert result.supplier_name == "ΣΚΛΑΒΕΝΙΤΗΣ"
    assert result.total_amount == 50.00
    assert result.vat_rate == 24
    assert result.confidence == Decimal("0.92")


@pytest.mark.asyncio
async def test_process_receipt_no_api_key():
    with patch("mahmoney.services.ocr.get_settings") as mock_settings:
        mock_settings.return_value.vlm_api_key = ""

        result = await process_receipt(b"fake-image-bytes")

    assert result is None


@pytest.mark.asyncio
async def test_process_receipt_api_error():
    with (
        patch("mahmoney.services.ocr.get_settings") as mock_settings,
        patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPError("Connection failed"),
        ),
    ):
        mock_settings.return_value.vlm_api_key = "test-key"
        mock_settings.return_value.vlm_api_url = "https://api.test.com/v1"
        mock_settings.return_value.vlm_model = "test-model"

        result = await process_receipt(b"fake-image-bytes")

    assert result is None
