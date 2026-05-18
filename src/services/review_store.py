"""DB CRUD helpers for HitlFeatureRegistry and HitlEvent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from db.models import HitlEvent, HitlFeatureRegistry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_feature(db: AsyncSession, feature_key: str) -> HitlFeatureRegistry | None:
    result = await db.execute(
        select(HitlFeatureRegistry).where(HitlFeatureRegistry.feature_key == feature_key)
    )
    return result.scalar_one_or_none()


async def already_shown(db: AsyncSession, conversation_id: str, pair_count: int) -> bool:
    """Check if popup was already shown at this exact pair_count for this conversation."""
    result = await db.execute(
        select(HitlEvent).where(
            HitlEvent.conversation_id == conversation_id,
            HitlEvent.pair_count == pair_count,
            HitlEvent.feature_key == "chat_compression",
        )
    )
    return result.scalar_one_or_none() is not None


async def create_event(
    db: AsyncSession, conversation_id: str, pair_count: int, feature_key: str = "chat_compression", event_metadata: dict | None = None
) -> HitlEvent:
    event = HitlEvent(
        conversation_id=conversation_id,
        feature_key=feature_key,
        pair_count=pair_count,
        status="shown",
        event_metadata=event_metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def update_event_response(
    db: AsyncSession, event_id: str, user_response: str
) -> HitlEvent | None:
    result = await db.execute(select(HitlEvent).where(HitlEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        return None
    event.status = user_response
    event.user_response = user_response
    event.responded_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(event)
    return event


async def expire_old_events(db: AsyncSession, sla_seconds: int) -> int:
    """Mark old shown events as expired if SLA exceeded.
    
    Returns:
        Number of events expired
    """
    cutoff = datetime.now(UTC) - timedelta(seconds=sla_seconds)
    result = await db.execute(
        select(HitlEvent).where(
            HitlEvent.status == "shown",
            HitlEvent.created_at < cutoff,
        )
    )
    events = result.scalars().all()
    count = 0
    for event in events:
        event.status = "expired"
        event.responded_at = datetime.now(UTC)
        count += 1
    if count > 0:
        await db.commit()
    return count


async def list_events(
    db: AsyncSession,
    conversation_id: str | None = None,
    feature_key: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[HitlEvent]:
    """List events with optional filters."""
    query = select(HitlEvent).order_by(HitlEvent.created_at.desc())
    
    if conversation_id:
        query = query.where(HitlEvent.conversation_id == conversation_id)
    if feature_key:
        query = query.where(HitlEvent.feature_key == feature_key)
    if status:
        query = query.where(HitlEvent.status == status)
    
    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
