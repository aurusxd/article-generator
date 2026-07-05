
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base



class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100),nullable=False)

    description: Mapped[str] = mapped_column(Text,nullable=False)

    posts_per_day: Mapped[int] = mapped_column(Integer,nullable=False)

    is_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=func.now())


