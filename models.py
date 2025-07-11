import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Date, Integer, JSON, PrimaryKeyConstraint, Text
from sqlalchemy import String, create_engine
from sqlalchemy.orm import Mapped, mapped_column
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

class ContributionType(Base):
    __tablename__ = 'Contribution_type'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Contribution_type_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contribution_type_name: Mapped[str] = mapped_column(Text)
    contribution_type_description: Mapped[Optional[str]] = mapped_column(Text)


class Contributions(Base):
    __tablename__ = 'Contributions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Contributions_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    course_id: Mapped[int] = mapped_column(Integer)
    contribution_type_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime.date] = mapped_column(Date)


class Course(Base):
    __tablename__ = 'Course'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Course_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    date_start: Mapped[Optional[datetime.date]] = mapped_column(Date)
    date_end: Mapped[Optional[datetime.date]] = mapped_column(Date)


class MembershipGranted(Base):
    __tablename__ = 'Membership_granted'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Membership_granted_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    date_granted: Mapped[datetime.date] = mapped_column(Date)
    days_granted: Mapped[int] = mapped_column(Integer)
    reason_id: Mapped[int] = mapped_column(Integer)
    contribution_id: Mapped[Optional[int]] = mapped_column(Integer)


engine = create_engine(DATABASE_URL)
