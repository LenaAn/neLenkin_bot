import sys
import os

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import engine, MockSignUp


def get_users_with_mock_counts(start_week: int, end_week: int) -> list:
    with Session(engine) as session:
        results = (
            session.query(
                MockSignUp.tg_id,
                func.array_agg(func.distinct(MockSignUp.tg_username)).label("usernames"),
                func.count().label("mock_count")
            )
            .filter(
                and_(
                    MockSignUp.week_number >= start_week,
                    MockSignUp.week_number <= end_week,
                )
            )
            .group_by(MockSignUp.tg_id)
            .order_by(func.count().desc())
            .all()
        )
        return results


def get_number_all_registrations(start_week: int, end_week: int) -> int:
    with Session(engine) as session:
        number_of_registrations = session.query(MockSignUp).filter(
                and_(
                    MockSignUp.week_number >= start_week,
                    MockSignUp.week_number <= end_week,
                )).count()
        return number_of_registrations


if __name__ == "__main__":
    # todo: that will break when the year changes and the week number starts from 1 again
    if len(sys.argv) != 3:
        print("Usage: uv run script.py <start_week_number> <end_week_number>  (both inclusive)")
        sys.exit(1)

    start_week = int(sys.argv[1])
    end_week = int(sys.argv[2])
    print(f"{start_week=}, {end_week=}")

    users = get_users_with_mock_counts(start_week, end_week)

    registration_count = get_number_all_registrations(start_week, end_week)
    print(f"In {end_week-start_week+1} weeks happened {registration_count} registartions, "
          f"approximately {registration_count/2} mocks")

    for user in users:
        tg_id, tg_username, mock_count = user
        print(f"tg_id={tg_id}, username={tg_username}, mocks={mock_count}")
