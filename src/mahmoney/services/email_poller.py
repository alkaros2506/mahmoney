import email
import imaplib
import logging
from datetime import UTC, datetime
from email.message import Message

from sqlalchemy.ext.asyncio import AsyncSession

from mahmoney.config import Settings
from mahmoney.models.enums import ExpenseStatus, Source
from mahmoney.models.expense import Expense
from mahmoney.services.ocr import process_receipt
from mahmoney.services.storage import save_file

logger = logging.getLogger(__name__)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/tiff"}
ALLOWED_TYPES = IMAGE_TYPES | {"application/pdf"}


def _extract_attachments(msg: Message) -> list[tuple[str, bytes]]:
    """Extract image/PDF attachments from an email message."""
    attachments: list[tuple[str, bytes]] = []
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type in ALLOWED_TYPES:
            payload = part.get_payload(decode=True)
            if payload:
                filename = part.get_filename() or f"attachment.{content_type.split('/')[-1]}"
                attachments.append((filename, payload))
    return attachments


async def poll_mailbox(settings: Settings, db: AsyncSession) -> int:
    """Poll IMAP mailbox for new emails with receipt attachments.

    Returns number of expenses created.
    """
    if not settings.imap_host or not settings.imap_user:
        logger.info("IMAP not configured, skipping email poll")
        return 0

    created = 0

    try:
        mail = imaplib.IMAP4_SSL(settings.imap_host)
        mail.login(settings.imap_user, settings.imap_password)
        mail.select(settings.imap_folder)

        _, message_ids = mail.search(None, "UNSEEN")
        if not message_ids[0]:
            logger.debug("No new emails")
            mail.logout()
            return 0

        for msg_id in message_ids[0].split():
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0]
            if isinstance(raw_email, tuple):
                raw_email = raw_email[1]

            msg = email.message_from_bytes(raw_email)
            subject = msg.get("Subject", "")
            sender = msg.get("From", "")
            logger.info("Processing email: %s from %s", subject, sender)

            attachments = _extract_attachments(msg)
            if not attachments:
                logger.debug("No relevant attachments in email: %s", subject)
                continue

            for filename, content in attachments:
                file_path = await save_file(content, filename)

                # Run OCR
                ocr_result = await process_receipt(content)

                expense = Expense(
                    supplier_name=ocr_result.supplier_name if ocr_result else f"From: {sender}",
                    supplier_country=ocr_result.supplier_country or "GR" if ocr_result else "GR",
                    date=datetime.now(tz=UTC),
                    total_amount=ocr_result.total_amount or 0 if ocr_result else 0,
                    currency=ocr_result.currency or "EUR" if ocr_result else "EUR",
                    source=Source.EMAIL,
                    source_file=filename,
                    receipt_image_path=str(file_path),
                    status=ExpenseStatus.PENDING_REVIEW,
                    notes=f"Email subject: {subject}",
                )

                if ocr_result:
                    expense.supplier_afm = ocr_result.supplier_afm
                    expense.invoice_number = ocr_result.invoice_number
                    expense.net_amount = ocr_result.net_amount
                    expense.vat_amount = ocr_result.vat_amount
                    expense.vat_rate = ocr_result.vat_rate
                    expense.mark_number = ocr_result.mark_number
                    expense.ocr_raw_response = ocr_result.model_dump()
                    expense.ocr_confidence = ocr_result.confidence
                    if ocr_result.payment_method:
                        expense.payment_method = ocr_result.payment_method

                db.add(expense)
                created += 1

            # Mark as seen (already done by fetching UNSEEN, but explicit)
            mail.store(msg_id, "+FLAGS", "\\Seen")

        await db.commit()
        mail.logout()

    except Exception:
        logger.exception("Error polling mailbox")

    logger.info("Created %d expenses from email", created)
    return created
