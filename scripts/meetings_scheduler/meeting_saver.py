from sqlalchemy.orm import Session
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import models


def insert_scheduled_part_message(week_number: int, course_id: int, text: str):
    with Session(models.engine) as session:
        message = models.ScheduledPartMessages(
            week_number=week_number,
            course_id=course_id,
            text=text
        )
        session.add(message)
        session.commit()
        return message
