import logging
from telegram.ext import (filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
                          PicklePersistence)

from handlers import admin_commands, handlers, menu, leetcode_mock_handlers
import notifications
import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

if __name__ == '__main__':
    persistence = PicklePersistence(filepath="nelenkin_bot_pickle")
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).persistence(persistence).build()

    # conversation handlers
    application.add_handler(admin_commands.echo_conv_handler)
    application.add_handler(admin_commands.broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_broadcast_conv_handler)
    application.add_handler(admin_commands.sre_broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_new_topic_broadcast)
    application.add_handler(leetcode_mock_handlers.leetcode_register_handler)

    application.add_handler(CommandHandler('cancel_leetcode_register', leetcode_mock_handlers.cancel_leetcode_register))

    application.add_handler(CommandHandler('start', menu.start))
    application.add_handler(CommandHandler('help', menu.command_help))
    application.add_handler(CommandHandler('get_users', admin_commands.get_users_handler))
    application.add_handler(CommandHandler('get_sre_users', admin_commands.get_sre_users_handler))
    application.add_handler(CommandHandler('leetcode_on', admin_commands.leetcode_on))
    application.add_handler(CommandHandler('leetcode_off', admin_commands.leetcode_off))
    application.add_handler(MessageHandler(~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(handlers.button_click))

    application.add_error_handler(handlers.error_handler)

    application.post_init = notifications.register_notifications

    application.run_polling()
