import os

from dotenv import load_dotenv


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'nelenkin_club'
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

CLUB_GROUP_CHAT_ID = int(os.getenv('CLUB_GROUP_CHAT_ID'))
LEETCODE_MOCKS_THREAD_ID = int(os.getenv('LEETCODE_MOCKS_THREAD_ID'))
