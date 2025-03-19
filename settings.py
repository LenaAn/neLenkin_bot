import os

from dotenv import load_dotenv


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_BOT_WEBHOOK_URL = os.getenv('TELEGRAM_BOT_WEBHOOK_URL')
TELEGRAM_BOT_WEBHOOK_HOST = "0.0.0.0"
TELEGRAM_BOT_WEBHOOK_PORT = 8816

DEBUG = (os.getenv("DEBUG") != "false")
