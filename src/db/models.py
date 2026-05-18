"""SQLAlchemy ORM models for HITL service."""

from __future__ import annotations

import uuid
from datetime import datetime

from config import settings
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_SCHEMA = settings.db_schema


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class HitlFeatureRegistry(Base):
    __tablename__ = "hitl_feature_registry"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    feature_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_service: Mapped[str] = mapped_column(String(50), nullable=False)
    consumer_service: Mapped[str] = mapped_column(String(50), nullable=False)
    executor_service: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    accepted_action: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HitlEvent(Base):
    __tablename__ = "hitl_events"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    pair_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="shown")
    # shown | accepted | rejected | expired
    user_response: Mapped[str | None] = mapped_column(String(20))
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
