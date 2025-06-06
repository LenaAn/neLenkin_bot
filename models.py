from sqlalchemy import Column, BigInteger, String, JSON, create_engine
from sqlalchemy.orm import declarative_base

from settings import DATABASE_URL

Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(String, nullable=False)
    tg_username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    date_joined = Column(JSON, nullable=True)
    date_membership_started = Column(JSON, nullable=True)

    def __repr__(self):
        return (f"User(telegram_id={self.tg_id}, username={self.tg_username}, first_name={self.first_name}, "
                f"last_name={self.last_name})")


class Enrollment(Base):
    __tablename__ = 'Enrollments'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    course_id = Column(BigInteger, nullable=False)
    tg_id = Column(String, nullable=False)

    def __repr__(self):
        return f"Enrollment(user_id={self.user_id}, course_id={self.course_id}, tg_id={self.tg_id}"


engine = create_engine(DATABASE_URL)
