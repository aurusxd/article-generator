from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.telegram_autopost import TelegramPostService
from config import TELEGRAM_CHANNEL_ID, config
from services.logger import log
from services.deepseek_service import ask_agent
from services.topic_service import topic_service
from services.publication_log_service import publication_log_service
from telegram.bot import bot
from utils.publish_times import generate_publish_times, is_time_to_publish
from services.dzen_posting import save_dzen_article_from_text

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

            for topic in topics:
                if not topic.is_enabled:
                    continue

                publish_times = generate_publish_times(
                    posts_per_day=topic.posts_per_day,
                    start_hour=8,
                    end_hour=23
                )
                for times in publish_times:
                    if not is_time_to_publish(times):
                        continue

                    already_published = await publication_log_service.was_published_today_at(
                        topic_id=topic.id,
                        planned_time=times,
                        platform="telegram"
                    )
                    if already_published:
                        continue

                    article, image_path = await ask_agent(
                        topic.name,
                        topic.description,
                        topic.with_photo,
                        return_image_path=True
                    )

                    if not article:
                        log.warning(f"Article was not generated. Topic: {topic.name}")
                        await publication_log_service.create_log(
                            topic_id=topic.id,
                            platform="telegram",
                            status="error",
                            planned_time=times,
                            error="article_not_generated",
                        )
                        continue
                    
                    suc = await save_dzen_article_from_text(article,image_path)
                    success = await self.telegram_post_service.publish_article(
                        text=article,
                        with_photo=topic.with_photo,
                        image_path=image_path
                    )
                    
                    await publication_log_service.create_log(
                        topic_id=topic.id,
                        platform="telegram",
                        status="success" if success else "error",
                        planned_time=times
                    )
                    if suc:
                        log.success("dzen yes")
                    else:
                        log.exception("Dzen no")

                    if success:
                        log.info(f"Автопостинг выполнен. Тема: {topic.name}")
                    else:
                        log.warning(f"Автопостинг не выполнен. Тема: {topic.name}")

        except Exception:
            log.exception("Ошибка автопостинга")


scheduler_service = SchedulerService()
