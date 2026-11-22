import asyncio
import logging
from app.config import settings
from app.gmail import GmailClient
from app.pipeline import process_incoming_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logger = logging.getLogger("lumen-poller")


async def run_poller() -> None:
    gmail = GmailClient()
    logger.info("Lumen Poller running (interval: %ss)... Press Ctrl+C to stop.", settings.poll_interval_seconds)
    while True:
        try:
            for email_data in gmail.fetch_unprocessed_messages(max_results=10):
                await process_incoming_email(gmail, email_data)
        except Exception as exc:
            logger.exception("Poll error: %s", exc)
        await asyncio.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_poller())
