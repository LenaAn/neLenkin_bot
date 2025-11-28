import os
import logging
import models
import datetime
from sqlalchemy.orm import Session

leetcode_pairs_logger = logging.getLogger(__name__)
leetcode_pairs_logger.setLevel(logging.DEBUG)


class Pair:
    def __init__(self, first: models.User, second: models.User):
        # todo: add if both agreed to English and common timeslots
        self.first: models.User = first
        self.second: models.User = second

    def __repr__(self):
        return f"{self.first.tg_username} - {self.second.tg_username}"


class GenerateLeetcodeMocks:
    def __init__(self, week_number):
        self.week_number = datetime.date.today().isocalendar().week if week_number is None else week_number
        self.sign_ups: list[models.MockSignUp] = []  # load only for this week
        self.users: list[models.User] = []  # load only those who enrolled this week
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
            mocks_signups = session.query(models.MockSignUp) \
                .filter(models.MockSignUp.week_number == self.week_number).all()
            leetcode_pairs_logger.info(f"got mock signups for week {self.week_number}: {mocks_signups}")
            self.sign_ups = mocks_signups
            leetcode_pairs_logger.info(f"self.sign_ups for week {self.week_number}: {self.sign_ups}")

    def load_users_for_signed_up_users(self):
        tg_ids = [signup.tg_id for signup in self.sign_ups]
        with (Session(models.engine) as session):
            users = session.query(models.User) \
                .filter(models.User.tg_id.in_(tg_ids)).all()
            leetcode_pairs_logger.info(f"got Users for signed up users: {users}")
            self.users = users
            leetcode_pairs_logger.info(f"self.users for week {self.week_number}: {self.users}")

    def generate_input(self) -> tuple[int, set]:
        users_to_timeslots = {}
        for sign_up in self.sign_ups:
            sign_up_user: models.User = list(filter(lambda x: x.tg_id == sign_up.tg_id, self.users))[0]
            users_to_timeslots[sign_up_user.id] = set(sign_up.selected_timeslots)

        user_ids = list(users_to_timeslots.keys())
        hypothetical_number_of_users = max(user_ids) + 1

        graph = set()
        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                if len(users_to_timeslots[user_ids[i]].intersection(users_to_timeslots[user_ids[j]])) > 0:
                    graph.add((user_ids[i], user_ids[j]))
        leetcode_pairs_logger.info(f"len(graph) = {len(graph)}")

        with open('leetcode_pairs/edges_to_delete.txt', 'r') as f:
            for line in f.readlines():
                (first, second) = [int(item) for item in line.split()]
                leetcode_pairs_logger.info(f"to remove: ({first}, {second})")
                if (first, second) in graph:
                    graph.remove((first, second))

        leetcode_pairs_logger.info(f"after deletion len(graph) = {len(graph)}")
        return hypothetical_number_of_users, graph

    def parse_output(self, ans: str):
        table_id_to_user = {}
        for user in self.users:
            table_id_to_user[user.id] = user
        leetcode_pairs_logger.info(f"table_id_to_user = {table_id_to_user}")

        lines = ans.strip().splitlines()
        pairs_count = int(lines[0])  # first line

        for line in lines[1:]:
            pair = [int(x) for x in line.split()]
            self.pairs.append(Pair(table_id_to_user[pair[0]], table_id_to_user[pair[1]]))
        leetcode_pairs_logger.info(f"pairs: {self.pairs}")

        ids_used = []
        for pair in self.pairs:
            ids_used.append(pair.first.id)
            ids_used.append(pair.second.id)
        leetcode_pairs_logger.info(f"ids_used flatten: {ids_used}")

        without_pair = []
        user_ids = [user.id for user in self.users]
        for user in user_ids:
            if user not in ids_used:
                without_pair.append(user)

        self.without_pairs = [table_id_to_user[x] for x in without_pair]

    def calculate_pairs(self):
        if len(self.sign_ups) == 0:
            leetcode_pairs_logger.info(f"no signups this week number {self.week_number}, skipping calculating pairs")
            return
        hypothetical_number_of_users, graph = self.generate_input()

        with open('leetcode_pairs/graph_for_week_n', 'w') as f:
            f.write(f"{hypothetical_number_of_users} {len(graph)}\n")
            for (first, second) in graph:
                f.write(f"{first} {second}\n")

        ans = os.popen("leetcode_pairs/a.out < leetcode_pairs/graph_for_week_n").read()
        leetcode_pairs_logger.info(f"ans from Blossom algo: \n{ans}")

        self.parse_output(ans)

        # write this week's pairs, so we don't repeat pairs next week
        with open('leetcode_pairs/edges_to_delete.txt', 'a') as f:
            for pair in self.pairs:
                f.write(f"{pair.first.id} {pair.second.id}\n")

    @classmethod
    def build(cls, week_number=None):
        obj = cls(week_number)
        obj.load_sign_ups()
        obj.load_users_for_signed_up_users()
        obj.calculate_pairs()
        return obj
