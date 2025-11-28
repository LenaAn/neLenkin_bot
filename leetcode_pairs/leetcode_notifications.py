import datetime
from telegram.ext import ContextTypes
from leetcode_pairs import generate_graph
import settings


async def send_leetcode_pairs_to_group(context: ContextTypes.DEFAULT_TYPE,
                                       generate_graph_obj: generate_graph.GenerateLeetcodeMocks):
    # todo: change it
    await context.bot.send_message(
        chat_id=settings.CLUB_GROUP_CHAT_ID,
        message_thread_id=settings.LEETCODE_MOCKS_THREAD_ID,
        text="hi! i'll be sending leetcode mock pairs",
        parse_mode="HTML",
    )


async def unicast_leetcode_partner(context: ContextTypes.DEFAULT_TYPE,
                                   generate_graph_obj: generate_graph.GenerateLeetcodeMocks):
    # todo: fill it
    pass


async def leetcode_notifications(context: ContextTypes.DEFAULT_TYPE):
    generate_graph_obj = generate_graph.GenerateLeetcodeMocks.build(
        week_number=datetime.date.today().isocalendar().week)

    await send_leetcode_pairs_to_group(context, generate_graph_obj)
    await unicast_leetcode_partner(context, generate_graph_obj)


async def register_leetcode_pairs_notification(app):
    cet_winter_time = datetime.timezone(datetime.timedelta(hours=1))

    app.job_queue.run_daily(
        callback=leetcode_notifications,
        time=datetime.time(hour=9, minute=3, tzinfo=cet_winter_time),
        days=(5,),  # 0 = Sunday, ..., 4 = Friday
        name=f"leetcode_notification",
    )
