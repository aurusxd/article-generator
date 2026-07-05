import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TIMER_INTERVAL = int(os.getenv("TIMER_INTERVAL", 3600))
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", 0)
CURRENT_TOPIC=""