import logging
from telegram.ext import (filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
                          PicklePersistence)

from handlers import admin_commands, button_handlers, menu, leetcode_mock_handlers, patreon_handlers
import notifications
from patreon import fetch_patrons
import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(app):
    await notifications.register_notifications(app)
    fetch_patrons.load_patrons()


if __name__ == '__main__':
    persistence = PicklePersistence(filepath="nelenkin_bot_pickle")
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).persistence(persistence).build()

    # conversation handlers
    application.add_handler(admin_commands.echo_conv_handler)
    application.add_handler(admin_commands.broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_broadcast_conv_handler)
    application.add_handler(admin_commands.sre_broadcast_conv_handler)
    application.add_handler(admin_commands.ddia_broadcast_conv_handler)
    application.add_handler(admin_commands.grind_broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_new_topic_broadcast)
    application.add_handler(leetcode_mock_handlers.leetcode_register_handler)
    application.add_handler(patreon_handlers.connect_patreon_handler)

    application.add_handler(CommandHandler('cancel_leetcode_register', leetcode_mock_handlers.cancel_leetcode_register))

    application.add_handler(CommandHandler('start', menu.start))
    application.add_handler(CommandHandler('help', menu.command_help))
    application.add_handler(CommandHandler('get_users', admin_commands.get_users_handler))
    application.add_handler(CommandHandler('get_patrons', admin_commands.get_patrons_handler))
    application.add_handler(CommandHandler('get_patron_counts', admin_commands.get_patron_counts_handler))
    application.add_handler(CommandHandler('get_sre_users', admin_commands.get_sre_users_handler))
    application.add_handler(CommandHandler('get_ddia_users', admin_commands.get_ddia_users_handler))
    application.add_handler(CommandHandler('get_grind_users', admin_commands.get_grind_users_handler))
    application.add_handler(CommandHandler('add_days', admin_commands.add_days_handler))
    application.add_handler(CommandHandler('leetcode_on', admin_commands.leetcode_on))
    application.add_handler(CommandHandler('leetcode_off', admin_commands.leetcode_off))
    application.add_handler(CommandHandler('sre_notification_on', admin_commands.sre_notification_on))
    application.add_handler(CommandHandler('sre_notification_off', admin_commands.sre_notification_off))
    application.add_handler(CommandHandler('codecrafters_notification_on', admin_commands.codecrafters_notification_on))
    application.add_handler(CommandHandler('codecrafters_notification_off', admin_commands.codecrafters_notification_off))
    application.add_handler(CommandHandler('pro_courses_on', admin_commands.pro_courses_on))
    application.add_handler(CommandHandler('pro_courses_off', admin_commands.pro_courses_off))
    application.add_handler(MessageHandler(~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(button_handlers.button_click))

    application.add_error_handler(button_handlers.error_handler)

    application.post_init = post_init

    application.run_polling()
