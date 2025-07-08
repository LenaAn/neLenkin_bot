import logging
from telegram.ext import (filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler)

from handlers import admin_commands, handlers, menu
import notifications
import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


if __name__ == '__main__':
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    application.add_handler(admin_commands.echo_conv_handler)
    application.add_handler(admin_commands.broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_broadcast_conv_handler)
    application.add_handler(admin_commands.sre_broadcast_conv_handler)
    application.add_handler(admin_commands.leetcode_new_topic_broadcast)

    application.add_handler(CommandHandler('start', menu.start))
    application.add_handler(CommandHandler('help', menu.command_help))
    application.add_handler(CommandHandler('get_users', admin_commands.get_users_handler))
    application.add_handler(CommandHandler('get_sre_users', admin_commands.get_sre_users_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(handlers.button_click))

    application.add_error_handler(handlers.error_handler)

    application.post_init = notifications.register_notifications

    application.run_polling()
