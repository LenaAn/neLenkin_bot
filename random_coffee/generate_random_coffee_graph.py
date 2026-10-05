import os
import logging
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import tuple_

import constants
import models


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Pair:
    def __init__(self, first: models.User, second: models.User):
        self.first: models.User = first
        self.second: models.User = second

    def __repr__(self):
        return f"{self.first.tg_username} - {self.second.tg_username}"


class GenerateRandomCoffeePairs:
    def __init__(self):
        # today we calculate for sign ups that happened last week
        self.week_number = (datetime.date.today() - datetime.timedelta(weeks=1)).isocalendar().week
        self.year = (datetime.date.today() - datetime.timedelta(weeks=1)).isocalendar().year
        self.sign_ups: list[models.RandomCoffeeSignUp] = []  # load only for last week sign ups
        self.users: list[models.User] = []  # load only those who signed up last week
        self.pairs: list[Pair] = []
        self.without_pairs: list[models.User] = []  # usually empty or just one element, but may be more if there are
        # people who were already matched together

    def __repr__(self):
        ans: str = ""
        for pair in self.pairs:
            ans += f"{pair.first.tg_username} - {pair.second.tg_username}\n"
        if len(self.without_pairs) > 0:
            ans += "Without pairs:\n"
            ans += ", ".join([user.tg_username for user in self.without_pairs])

        return ans

    def load_sign_ups(self):
        with (Session(models.engine) as session):
            coffee_signups = session.query(models.RandomCoffeeSignUp) \
                .filter((models.RandomCoffeeSignUp.week_number == self.week_number) &
                        (models.RandomCoffeeSignUp.year == self.year)).all()
            logger.info(f"got random coffee signups for week {self.week_number} {self.year}: {coffee_signups}")
            self.sign_ups = coffee_signups
            logger.info(f"self.sign_ups for week {self.week_number} {self.year}: {self.sign_ups}")

    def load_users_for_signed_up_users(self):
        tg_ids = [signup.tg_id for signup in self.sign_ups]
        with (Session(models.engine) as session):
            users = session.query(models.User) \
                .filter(models.User.tg_id.in_(tg_ids)).all()
            logger.debug(f"got Users for random coffee signed up users: {users}")
            self.users = users
            logger.debug(f"self.users for random coffee week {self.week_number} {self.year}: {self.users}")

    def generate_input(self) -> tuple[int, set]:
        user_ids = [user.id for user in self.users]
        hypothetical_number_of_users = max(user_ids) + 1
        graph = set()
        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                graph.add((user_ids[i], user_ids[j]))
        logger.debug(f"len(graph) = {len(graph)}")

        # deleting edges from pair that already matched in the last 12 weeks
        today = datetime.date.today()
        weeks = []
        for i in range(12):
            iso = (today - datetime.timedelta(weeks=i)).isocalendar()
            weeks.append((iso.year, iso.week))

        with Session(models.engine) as session:
            matched_pairs = (
                session.query(models.PairsMatched).filter(
                    models.PairsMatched.course_id == constants.random_coffee_course_id,
                    tuple_(models.PairsMatched.year, models.PairsMatched.week_number).in_(weeks),
                ).all()
            )
        for pair in matched_pairs:
            edge = (int(pair.first_tg_id), int(pair.second_tg_id))
            reverse_edge = (edge[1], edge[0])
            logger.info(f"to remove: {edge}")

            if edge in graph:
                graph.remove(edge)
            elif reverse_edge in graph:
                graph.remove(reverse_edge)

        logger.info(f"after deletion len(graph) = {len(graph)}")
        return hypothetical_number_of_users, graph

    def parse_output(self, ans: str):
        table_id_to_user = {}
        for user in self.users:
            table_id_to_user[user.id] = user
        logger.info(f"table_id_to_user = {table_id_to_user}")

        lines = ans.strip().splitlines()
        pairs_count = int(lines[0])  # first line

        for line in lines[1:]:
            pair = [int(x) for x in line.split()]
            self.pairs.append(Pair(table_id_to_user[pair[0]], table_id_to_user[pair[1]]))
        logger.debug(f"coffee pairs: {self.pairs}")

        ids_used = []
        for pair in self.pairs:
            ids_used.append(pair.first.id)
            ids_used.append(pair.second.id)
        logger.debug(f"coffee flatten: {ids_used}")

        without_pair = []
        user_ids = [user.id for user in self.users]
        for user in user_ids:
            if user not in ids_used:
                without_pair.append(user)

        self.without_pairs = [table_id_to_user[x] for x in without_pair]

    def calculate_pairs(self):
        if len(self.sign_ups) == 0:
            logger.info(f"no coffee signups this week number {self.week_number} {self.year}, "
                                       f"skipping calculating pairs")
            return
        hypothetical_number_of_users, graph = self.generate_input()

        with open('random_coffee/coffee_graph_for_week_n', 'w') as f:
            f.write(f"{hypothetical_number_of_users} {len(graph)}\n")
            for (first, second) in graph:
                f.write(f"{first} {second}\n")

        ans = os.popen("random_coffee/a.out < random_coffee/coffee_graph_for_week_n").read()
        logger.debug(f"ans from Blossom algo: \n{ans}")
        self.parse_output(ans)

        # write this week's pairs, so we don't repeat pairs next week
        # record not today's week and year, but week and year of sign up (last week)
        with Session(models.engine) as session:
            for pair in self.pairs:
                session.add(
                    models.PairsMatched(
                        course_id=constants.random_coffee_course_id,
                        first_tg_id=str(pair.first.id),
                        second_tg_id=str(pair.second.id),
                        week_number=self.week_number,
                        year=self.year,
                    )
                )
            session.commit()

    @classmethod
    def build(cls, week_number=None, year=None):
        obj = cls(week_number, year)
        obj.load_sign_ups()
        obj.load_users_for_signed_up_users()
        obj.calculate_pairs()
        return obj
