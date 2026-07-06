from services.logger import log
from telegram.bot import bot


async def telegram_publish_task(text: str, chat_id: int):
    while True:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        log.info("Опубликовано:", text)

