from sqlalchemy.orm import Session

import models


def get_course_name(course_id: int) -> str:
    with Session(models.engine) as session:
        result = session.query(models.Course).filter(models.Course.id == course_id).one_or_none()
    if result:
        return result.name
    else:
        raise Exception(f"Invalid course_id: {course_id}")
