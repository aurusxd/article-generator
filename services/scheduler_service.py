import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.telegram_autopost import TelegramPostService
from config import TELEGRAM_CHANNEL_ID, config
from services.logger import log
from services.deepseek_service import ask_agent
from services.topic_service import topic_service
from telegram.bot import bot

telegram_post_service = TelegramPostService(
    bot=bot,
    channel_id=TELEGRAM_CHANNEL_ID,
)

class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(
            timezone=config.scheduler.SCHEDULER_TIMEZONE
        )

        self.telegram_post_service = TelegramPostService(
            bot=bot,
            channel_id=TELEGRAM_CHANNEL_ID,
        )

        self.job_id = "autopost-job"
        self.isActive = False

    def start(self) -> None:
        if not config.scheduler.SCHEDULER_ENABLED:
            log.info("Scheduler disabled by config")
            return

        self.isActive=True
        if self.scheduler.running:
            log.info("Scheduler already running")
            return

        self.scheduler.add_job(
            self.start_posting,
            trigger="interval",
            seconds=config.scheduler.SCHEDULER_INTERVAL_SECONDS,
            id=self.job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        self.scheduler.start()

        log.info(
            f"Scheduler started. Interval: "
            f"{config.scheduler.SCHEDULER_INTERVAL_SECONDS} seconds"
        )

    async def shutdown(self) -> None:
        self.isActive=False
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            log.info("Scheduler stopped")

    async def start_posting(self) -> None:
        try:
            topics = await topic_service.get_all_topics()

            enabled_topics = [
                topic for topic in topics
                if topic.is_enabled and topic.posts_per_day > 0
            ]

            if not enabled_topics:
                log.info("Нет активных тематик для автопостинга")
                return

            topic = random.choice(enabled_topics)

            article = await ask_agent(
                topic.name,
                topic.description,
            )

            if not article:
                log.warning("ИИ не сгенерировал статью")
                return

            success = await self.telegram_post_service.publish_article(
                text=article,
            )

            if success:
                log.info(f"Автопостинг выполнен. Тема: {topic.name}")
            else:
                log.warning(f"Автопостинг не выполнен. Тема: {topic.name}")

        except Exception:
            log.exception("Ошибка автопостинга")


scheduler_service = SchedulerService()