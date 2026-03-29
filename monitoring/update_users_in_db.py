from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

import models


async def update_users_after_broadcast(success_ids, failed_ids):
    now = datetime.utcnow()

    with Session(models.engine) as session:
        if success_ids:
            session.execute(update(models.User).where(models.User.tg_id.in_(success_ids)).values(
                is_last_message_successful=True,
                last_message_try_time=now,
            ))

        if failed_ids:
            session.execute(update(models.User).where(models.User.tg_id.in_(failed_ids)).values(
                is_last_message_successful=False,
                last_message_try_time=now,
            ))

        session.commit()
