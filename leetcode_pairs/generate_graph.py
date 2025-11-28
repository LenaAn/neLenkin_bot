import logging
import models
import datetime
from sqlalchemy.orm import Session


class Pair:
    def __init__(self, first: models.User, second: models.User, english: bool, common_timeslots: list[str]):
        self.first: models.User = first
        self.second: models.User = second
        self.english: bool = english
        self.common_timeslots: list[str] = common_timeslots


class GenerateLeetcodeMocks:
    def __init__(self, week_number):
        self.week_number = datetime.date.today().isocalendar().week if week_number is None else week_number
        self.sign_ups = list[models.MockSignUp]  # load only for this week
        self.users: list[models.User] = []  # load only those who enrolled this week
        self.pairs: list[Pair]
        self.without_pairs = list[models.User]  # usually empty list or just one element, but may be more if there are
        # people who were already matched together

    def load_sign_ups(self):
        with (Session(models.engine) as session):
            mocks_signups = session.query(models.MockSignUp)\
                .filter(models.MockSignUp.week_number == self.week_number).all()
            logging.info(f"got mock signups for week {self.week_number}: {mocks_signups}")
            self.sign_ups = mocks_signups
            logging.info(f"self.sign_ups for week {self.week_number}: {self.sign_ups}")

    def load_users(self):
        # todo: load users
        pass

    def calculate_pairs(self):
        # todo: actually invoke the logic
        pass

    @classmethod
    def build(cls, week_number=None):
        obj = cls(week_number)
        obj.load_sign_ups()
        obj.load_users()
        obj.calculate_pairs()
        return obj
