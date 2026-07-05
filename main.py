import asyncio

from services.scheduler_service import scheduler_service
from services.logger import log
from telegram.bot import bot, dp
from telegram.handlers.topic import router as topics_router
from telegram.handlers.create_topic import router as create_topic_router
from telegram.keyboards.callback import router as default_router
from telegram.handlers.generate_article import router as generate_article_router
async def main():
    try:
        log.info("🚀 Запуск бота")
        dp.include_router(topics_router)
        dp.include_router(create_topic_router)
        dp.include_router(default_router)
        dp.include_router(generate_article_router)

        scheduler_service.start()

        await dp.start_polling(bot, timeout=60)
    except Exception:  # noqa: BLE001
        log.exception("Бот не запущен, ошибка: ")
    finally:
        scheduler_service.shutdown()





if __name__ == "__main__":
    asyncio.run(main())

