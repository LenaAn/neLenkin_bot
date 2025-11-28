import datetime
from telegram.ext import ContextTypes
from leetcode_pairs import generate_graph


async def send_leetcode_pairs_to_group(context: ContextTypes.DEFAULT_TYPE, pairs: list[list[int]]):
    # todo: fill it
    pass


async def unicast_leetcode_partner(context: ContextTypes.DEFAULT_TYPE, pairs: list[list[int]]):
    # todo: fill it
    pass


async def leetcode_notifications(context: ContextTypes.DEFAULT_TYPE):
    pairs = []
    # todo: use the function
    # pairs: list[list[int]] = generate_graph.generate_pairs()
    await send_leetcode_pairs_to_group(context, pairs)
    await unicast_leetcode_partner(context, pairs)


async def register_leetcode_pairs_notification(app):
    cet_winter_time = datetime.timezone(datetime.timedelta(hours=1))

    app.job_queue.run_daily(
        callback=leetcode_notifications,
        time=datetime.time(hour=9, minute=3, tzinfo=cet_winter_time),
        days=(5,),  # 0 = Sunday, ..., 4 = Friday
        name=f"leetcode_notification",
    )
