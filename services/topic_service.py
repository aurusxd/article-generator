from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database.models.topic import Topic
from services.logger import log
from utils.depends import AsyncSession, provider


class TopicService:
    @provider.inject_session
    async def create_topic(
        self,
        name: str,
        description: str,
        session: AsyncSession,
    ) -> Topic | None:
        try:
            existing_topic = await session.scalar(
                select(Topic).where(Topic.name == name)
            )

            if existing_topic:
                log.warning(f"Топик с именем '{name}' уже существует")
                return None

            new_topic = Topic(
                name=name,
                description=description,
                posts_per_day=0,
                is_enabled=False,
                created_at=datetime.now(timezone.utc),
            )

            session.add(new_topic)
            await session.commit()
            await session.refresh(new_topic)

            log.info(f"Топик создан: {new_topic.name}")
            return new_topic

        except SQLAlchemyError:
            log.exception("Ошибка при создании топика")
            await session.rollback()
            return None

    @provider.inject_session
    async def get_topic_by_name(
        self,
        name: str,
        session: AsyncSession,
    ) -> Topic | None:
        try:
            topic = await session.scalar(
                select(Topic).where(Topic.name == name)
            )

            if topic:
                log.info(f"Топик получен: {topic.name}")
            else:
                log.info(f"Топик не найден: {name}")

            return topic

        except SQLAlchemyError:
            log.exception("Ошибка при получении топика")
            return None


    @provider.inject_session
    async def get_all_topics(
        self,
        session: AsyncSession,
    ) -> list[Topic]:
        try:
            result = await session.scalars(
                select(Topic).order_by(Topic.created_at.desc())
            )

            topics = result.all()

            log.info(f"Получено топиков: {len(topics)}")
            return topics

        except SQLAlchemyError:
            log.exception("Ошибка при получении списка топиков")
            return []

    @provider.inject_session
    async def get_enabled_topics(
        self,
        session: AsyncSession,
    ) -> list[Topic]:
        try:
            result = await session.scalars(
                select(Topic)
                .where(Topic.is_enabled)
                .order_by(Topic.created_at.desc())
            )

            topics = result.all()

            log.info(f"Получено активных топиков: {len(topics)}")
            return topics

        except SQLAlchemyError:
            log.exception("Ошибка при получении активных топиков")
            return []
    
    @provider.inject_session 
    async def update_topic(
        self,
        session: AsyncSession,
        topic_id: int,
        name: str | None = None,
        description: str | None = None,
        posts_per_day: int | None = None,
        is_enabled: bool | None = None,
    ) -> Topic | None:
        try:
            topic = await session.scalar(
                select(Topic).where(Topic.id == topic_id)
            )
            if not topic:
                log.warning(f"Топик с id={topic_id} не найден")
                return None

            if name is not None:
                topic.name = name

            if description is not None:
                topic.description = description

            if posts_per_day is not None:
                topic.posts_per_day = posts_per_day

            if is_enabled is not None:
                topic.is_enabled = is_enabled

            await session.commit()
            await session.refresh(topic)

            log.info(f"Топик обновлен: id={topic.id}")
            return topic

        except SQLAlchemyError:
            log.exception("Ошибка при обновлении топика")
            await session.rollback()
            return None

    
    @provider.inject_session
    async def get_topic_by_id(
        self, topic_id: int, session: AsyncSession
    ) -> Topic | None:
        try:
            topic = await session.scalar(
                select(Topic).where(Topic.id == topic_id)
            )

            log.info("Топик получен")
            return topic

        except SQLAlchemyError:
            log.exception("Топик не был получен")
            return None


    @provider.inject_session
    async def delete_topic(
        self,
        topic_id: int,
        session: AsyncSession,
    ) -> bool:
        try:
            topic = await session.scalar(
                select(Topic).where(Topic.id == topic_id)
            )

            if topic is None:
                log.warning(f"Топик с id={topic_id} не найден")
                return False

            await session.delete(topic)
            await session.commit()

            log.info(f"Топик с id={topic_id} удален")

            return True

        except SQLAlchemyError:
            log.exception("Ошибка при удалении топика")
            await session.rollback()
            return False
        



topic_service = TopicService()