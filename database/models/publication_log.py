

from datetime import datetime, time

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class PublicationLog(Base):
    __tablename__ = "publication_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    platform: Mapped[str]  # telegram / dzen
    status: Mapped[str]    # success / error
    error: Mapped[str | None]
    planned_time: Mapped[time]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=func.now())