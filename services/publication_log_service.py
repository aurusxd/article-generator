from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database.models.publication_log import PublicationLog
from services.logger import log
from utils.depends import AsyncSession, provider


class PublicationLogService:
    @provider.inject_session
    async def create_log(
        self,
        topic_id: int,
        platform: str,
        status: str,
        session: AsyncSession,
        error: str | None = None,
        planned_time: time | None = None,
    ) -> PublicationLog | None:
        try:
            new_log = PublicationLog(
                topic_id=topic_id,
                platform=platform,
                status=status,
                error=error,
                planned_time=planned_time,
                created_at=datetime.now(timezone.utc),
            )

            session.add(new_log)
            await session.commit()
            await session.refresh(new_log)

            log.info(f"Лог публикации создан: topic_id={topic_id}, status={status}")
            return new_log

        except SQLAlchemyError:
            log.exception("Ошибка при создании лога публикации")
            await session.rollback()
            return None

    @provider.inject_session
    async def get_today_success_count(
        self,
        topic_id: int,
        platform: str,
        session: AsyncSession,
    ) -> int:
        try:
            now = datetime.now(timezone.utc)
            start_of_day = datetime.combine(
                now.date(),
                time.min,
                tzinfo=timezone.utc,
            )

            count = await session.scalar(
                select(func.count(PublicationLog.id))
                .where(PublicationLog.topic_id == topic_id)
                .where(PublicationLog.platform == platform)
                .where(PublicationLog.status == "success")
                .where(PublicationLog.created_at >= start_of_day)
            )

            return count or 0

        except SQLAlchemyError:
            log.exception("Ошибка при подсчете публикаций за сегодня")
            return 0

    @provider.inject_session
    async def was_published_today_at(
        self,
        topic_id: int,
        platform: str,
        planned_time: time,
        session: AsyncSession,
    ) -> bool:
        try:
            now = datetime.now(timezone.utc)
            start_of_day = datetime.combine(
                now.date(),
                time.min,
                tzinfo=timezone.utc,
            )

            existing_log = await session.scalar(
                select(PublicationLog)
                .where(PublicationLog.topic_id == topic_id)
                .where(PublicationLog.platform == platform)
                .where(PublicationLog.status == "success")
                .where(PublicationLog.planned_time == planned_time)
                .where(PublicationLog.created_at >= start_of_day)
            )

            return existing_log is not None

        except SQLAlchemyError:
            log.exception("Ошибка при проверке публикации по слоту")
            return True

    @provider.inject_session
    async def get_last_logs(
        self,
        session: AsyncSession,
        limit: int = 10,
    ) -> list[PublicationLog]:
        try:
            result = await session.scalars(
                select(PublicationLog)
                .order_by(PublicationLog.created_at.desc())
                .limit(limit)
            )

            return list(result.all())

        except SQLAlchemyError:
            log.exception("Ошибка при получении последних логов публикаций")
            return []

    @provider.inject_session
    async def get_topic_logs(
        self,
        topic_id: int,
        session: AsyncSession,
        limit: int = 10,
    ) -> list[PublicationLog]:
        try:
            result = await session.scalars(
                select(PublicationLog)
                .where(PublicationLog.topic_id == topic_id)
                .order_by(PublicationLog.created_at.desc())
                .limit(limit)
            )

            return list(result.all())

        except SQLAlchemyError:
            log.exception("Ошибка при получении логов тематики")
            return []


publication_log_service = PublicationLogService()