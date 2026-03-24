import asyncio
import logging

from mahmoney.config import get_settings
from mahmoney.database import get_session_factory
from mahmoney.services.email_poller import poll_mailbox

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    logger.info("Email poller started. Polling every %d seconds.", settings.poll_interval_seconds)

    while True:
        try:
            async with session_factory() as session:
                created = await poll_mailbox(settings, session)
                if created:
                    logger.info("Created %d expenses from email", created)
        except Exception:
            logger.exception("Error in polling loop")

        await asyncio.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
