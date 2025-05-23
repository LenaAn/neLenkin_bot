import logging
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler

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

    application.add_handler(CommandHandler('start', menu.start))
    application.add_handler(CommandHandler('help', menu.command_help))
    application.add_handler(CommandHandler('get_users', admin_commands.get_users_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(handlers.button_click))

    application.post_init = notifications.register_leetcode_notifications
    application.run_polling()
