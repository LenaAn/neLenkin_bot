from monitoring.push_monitoring import metrics

from sqlalchemy.orm import Session
from membership import fetch_boosty_patrons, fetch_patrons

import models


def users_started_bot_count() -> int:
    with Session(models.engine) as session:
        users_count = session.query(models.User).count()
    return users_count


def users_failed_broadcast_count() -> int:
    with Session(models.engine) as session:
        failed_users_count = session.query(models.User).filter(models.User.is_last_message_successful.is_(False)).count()
    return failed_users_count


# this will be run periodically on cron
if __name__ == "__main__":
    metrics.set("users_started_bot", users_started_bot_count())
    metrics.set("users_failed_broadcast", users_failed_broadcast_count())
    metrics.set("patreon_patrons", len(fetch_patrons.get_patrons_from_redis("active_patron")))
    metrics.set("boosty_patrons", len(fetch_boosty_patrons.get_boosty_patrons_from_redis(1)))
    metrics.push()
