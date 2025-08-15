from sqlalchemy.orm import declarative_base
import sqlalchemy
from sqlalchemy import Column, create_engine

from settings import DATABASE_URL

Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'

    id = Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(sqlalchemy.Text, nullable=False)
    tg_username = Column(sqlalchemy.Text, nullable=True)
    first_name = Column(sqlalchemy.Text, nullable=True)
    last_name = Column(sqlalchemy.Text, nullable=True)
    date_joined = Column(sqlalchemy.JSON, nullable=True)
    date_membership_started = Column(sqlalchemy.JSON, nullable=True)

    __table_args__ = (
        sqlalchemy.UniqueConstraint('tg_id', name='Users_unique_tg_id'),
    )

    def __repr__(self):
        return f"User(username={self.tg_username}, telegram_id={self.tg_id})"


class Enrollment(Base):
    __tablename__ = 'Enrollments'

    id = Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(sqlalchemy.BigInteger, nullable=True)
    course_id = Column(sqlalchemy.BigInteger, nullable=False)
    tg_id = Column(sqlalchemy.Text, nullable=False)

    __table_args__ = (
        sqlalchemy.UniqueConstraint('tg_id', 'course_id', name='Unique_tg_id_per_course'),
    )

    def __repr__(self):
        return f"Enrollment(user_id={self.user_id}, course_id={self.course_id}, tg_id={self.tg_id}"


class Course(Base):
    __tablename__ = 'Course'

    id = Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = Column(sqlalchemy.Text, nullable=False)
    description = Column(sqlalchemy.Text, nullable=True)
    date_start = Column(sqlalchemy.Date, nullable=True)
    date_end = Column(sqlalchemy.Date, nullable=True)
    curator_tg_id = Column(sqlalchemy.Text, nullable=True)

    def __repr__(self):
        return f"Course(id={self.id}, name={self.name}"


# supposed to be short-lived (couple of months data)
# one message is scheduled in a week per course
# at what time the message is sent in defined in code
class ScheduledPartMessages(Base):
    __tablename__ = 'ScheduledPartMessages'

    id = Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    week_number = Column(sqlalchemy.Integer, nullable=False)
    course_id = Column(sqlalchemy.Integer, nullable=False)
    text = Column(sqlalchemy.Text, nullable=False)
    __table_args__ = (
        sqlalchemy.UniqueConstraint('week_number', 'course_id', name='Unique_message_per_week_and_course'),
    )


class MockSignUp(Base):
    __tablename__ = 'MockSignUp'

    id = Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    # week when user signs up. Sign-ups are allowed from Monday morning to Thursday evening
    week_number = Column(sqlalchemy.Integer, nullable=False)
    # some users don't have username
    tg_username = Column(sqlalchemy.Text, nullable=True)
    tg_id = Column(sqlalchemy.Text, nullable=False)
    first_problem = Column(sqlalchemy.Text, nullable=False)
    second_problem = Column(sqlalchemy.Text, nullable=False)
    selected_timeslots = Column(sqlalchemy.JSON, nullable=False)
    programming_language = Column(sqlalchemy.Text, nullable=False)
    english_choice = Column(sqlalchemy.Boolean, nullable=False)

    __table_args__ = (
        sqlalchemy.UniqueConstraint('week_number', 'tg_id', name='One_record_per_user_per_week'),
    )


engine = create_engine(DATABASE_URL)

# todo: these are essentially feature flags, but are not persisted across restarts. Need a nicer way to work with
#  feature flags.
leetcode_status_on = True
sre_notification_on = True
