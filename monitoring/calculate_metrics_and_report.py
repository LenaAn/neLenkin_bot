import asyncio
import logging
from monitoring.push_monitoring import metrics

from sqlalchemy.orm import Session
from telegram import Bot
from membership import fetch_boosty_patrons, fetch_patrons

import models
import settings

logger = logging.getLogger("metrics_reporter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # prints to stdout (captured by cron log)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def users_started_bot_count() -> int:
    with Session(models.engine) as session:
        users_count = session.query(models.User).count()
    logger.info(f"users_started_bot_count: {users_count}")
    return users_count


def users_failed_broadcast_count() -> int:
    with Session(models.engine) as session:
        failed_users_count = session.query(models.User).filter(models.User.is_last_message_successful.is_(False)).count()
    logger.info(f"users_failed_broadcast_count: {failed_users_count}")
    return failed_users_count


async def calculate_metrics_and_report(bot: Bot = None) -> None:
    logger.info("Starting metrics collection")
    try:
        metrics.set("users_started_bot", users_started_bot_count())
        metrics.set("users_failed_broadcast", users_failed_broadcast_count())
        metrics.set("patreon_patrons", len(fetch_patrons.get_patrons_from_redis("active_patron")))
        metrics.set("boosty_patrons", len(fetch_boosty_patrons.get_boosty_patrons_from_redis(1)))
        metrics.push()
        logger.info("Metrics successfully pushed")
    except Exception as e:
        logger.error("Failed to collect or push metrics")
        if bot:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Failed to collect or push metrics: {e}")


# this will be run periodically on cron
if __name__ == "__main__":
    asyncio.run(calculate_metrics_and_report())
