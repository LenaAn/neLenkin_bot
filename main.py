import logging
from telegram.ext import (filters, ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler,
                          CallbackQueryHandler)

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

    echo_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('echo', admin_commands.start_echo)],
        states={
            admin_commands.ECHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands.echo_message)]
        },
        fallbacks=[CommandHandler('cancel_echo', admin_commands.cancel_echo)],
    )

    # todo: make sure it doesn't mess up with multiple admins
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('broadcast', admin_commands.start_broadcast)],
        states={
            admin_commands.BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands.broadcast)]
        },
        fallbacks=[CommandHandler('cancel_broadcast', admin_commands.cancel_broadcast)],
    )

    leetcode_broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('leetcode_broadcast', admin_commands.start_leetcode_broadcast)],
        states={
            admin_commands.BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands.leetcode_broadcast)]
        },
        fallbacks=[CommandHandler('cancel_broadcast', admin_commands.cancel_broadcast)],
    )

    sre_broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('sre_broadcast', admin_commands.start_sre_broadcast)],
        states={
            admin_commands.BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands.sre_broadcast)]
        },
        fallbacks=[CommandHandler('cancel_broadcast', admin_commands.cancel_broadcast)],
    )

    application.add_handler(echo_conv_handler)
    application.add_handler(broadcast_conv_handler)
    application.add_handler(leetcode_broadcast_conv_handler)
    application.add_handler(sre_broadcast_conv_handler)

    application.add_handler(CommandHandler('start', menu.start))
    application.add_handler(CommandHandler('help', menu.command_help))
    application.add_handler(CommandHandler('get_users', admin_commands.get_users_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, menu.private_message))

    application.add_handler(CallbackQueryHandler(handlers.button_click))

    application.add_error_handler(handlers.error_handler)

    application.post_init = notifications.register_notifications

    application.run_polling()
