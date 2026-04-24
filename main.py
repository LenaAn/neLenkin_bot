import logging
from telegram.ext import (filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
                          PicklePersistence)

from courses import course_handlers
from handlers import admin_commands, button_handlers, menu, leetcode_mock_handlers
from users import intro_handler, email_contact_handler, location_handler
from notifications import notifications
from membership import boosty_handlers, fetch_patrons, fetch_boosty_patrons, membership, patreon_handlers
from monitoring import calculate_metrics_and_report
import settings
from leetcode_pairs import leetcode_notifications

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(app):
    await notifications.register_notifications(app)
    await leetcode_notifications.register_leetcode_pairs_notification(application)
    await fetch_patrons.load_patrons(app.bot)
    await fetch_boosty_patrons.init()
    await fetch_boosty_patrons.load_boosty_patrons(app.bot)
    await calculate_metrics_and_report.calculate_metrics_and_report(app.bot)


async def post_shutdown(_unused_arg):
    await fetch_boosty_patrons.close()


if __name__ == '__main__':
    persistence = PicklePersistence(filepath="nelenkin_bot_pickle")
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).persistence(persistence).build()

    # conversation handlers
    application.add_handler(admin_commands.echo_conv_handler)
    application.add_handler(admin_commands.broadcast_conv_handler)
    application.add_handler(admin_commands.basic_members_broadcast_conv_handler)
    application.add_handler(admin_commands.course_broadcast_conv_handler)
    application.add_handler(admin_commands.course_get_users_conv_handler)
    application.add_handler(admin_commands.leetcode_new_topic_broadcast)
    application.add_handler(leetcode_mock_handlers.leetcode_register_handler)
    application.add_handler(intro_handler.intro_conv_handler)
    application.add_handler(patreon_handlers.connect_patreon_handler)
    application.add_handler(boosty_handlers.connect_boosty_handler)

    application.add_handler(
        CommandHandler('cancel_leetcode_register', leetcode_mock_handlers.cancel_leetcode_register,
                       filters.ChatType.PRIVATE))

    application.add_handler(
        CommandHandler('start', menu.start, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('help', menu.command_help, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('membership', membership.handle_membership, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('courses', course_handlers.handle_active_courses, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('set_email', email_contact_handler.set_email_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('add_location', location_handler.add_location_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('get_users', admin_commands.get_users_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('get_patrons', admin_commands.get_patrons_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('add_days', admin_commands.add_days_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('get_status', admin_commands.get_status_handler, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('leetcode_on', admin_commands.leetcode_on, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('leetcode_off', admin_commands.leetcode_off, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('aoc_notification_on', admin_commands.aoc_notification_on,
                       filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('aoc_notification_off', admin_commands.aoc_notification_off,
                       filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('pro_courses_on', admin_commands.pro_courses_on, filters.ChatType.PRIVATE))
    application.add_handler(
        CommandHandler('pro_courses_off', admin_commands.pro_courses_off, filters.ChatType.PRIVATE))
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(button_handlers.button_click))

    application.add_error_handler(button_handlers.error_handler)

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    application.run_polling()
