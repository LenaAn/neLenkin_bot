import os

# Several application modules parse these settings while they are imported.
for _name in (
    "ADMIN_CHAT_ID",
    "CLUB_GROUP_CHAT_ID",
    "AOC_TOPIC_ID",
    "LEETCODE_MOCKS_THREAD_ID",
    "RANDOM_COFFEE_THREAD_ID",
):
    os.environ.setdefault(_name, "999999999")
