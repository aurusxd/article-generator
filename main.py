import asyncio

from services.logger import log
from telegram.bot import bot, dp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def main():
    try:
        log.info("🚀 Запуск бота")
        await dp.start_polling(bot, timeout=60)
    except Exception:  # noqa: BLE001
        log.exception("Бот не запущен, ошибка: ")





if __name__ == "__main__":
    asyncio.run(main())

