"""HITL Chat Compression routes."""

from __future__ import annotations

import structlog
from deps import get_db, verify_token
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from models.schemas import (
    CheckTriggerResponse,
    EventListResponse,
    RespondRequest,
    RespondResponse,
    EventListItem,
)
from services import review_store
from services.sensitive_detector import detect_sensitive_data, mask_sensitive_data
from services.complexity_analyzer import analyze_query_complexity, suggest_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(dependencies=[Depends(verify_token)])

_TRIGGER_THRESHOLDS = [10, 20]
_HARD_LIMIT = 30
_FEATURE_KEY = "chat_compression"
_POPUP_MESSAGE = "Your conversation is getting long. Compress old messages to keep responses fast?"


# ── GET /hitl/features/chat_compression/check ────────────────────────────────


@router.get(
    "/hitl/features/chat_compression/check",
    response_model=CheckTriggerResponse,
)
async def check_trigger(
    conversation_id: str = Query(...),
    pair_count: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Chat service calls this after every completed assistant response."""
    feature = await review_store.get_feature(db, _FEATURE_KEY)
    if not feature or not feature.enabled:
        return CheckTriggerResponse(should_prompt=False)

    if pair_count not in _TRIGGER_THRESHOLDS:
        return CheckTriggerResponse(should_prompt=False)

    already = await review_store.already_shown(db, conversation_id, pair_count)
    if already:
        return CheckTriggerResponse(should_prompt=False)

    event = await review_store.create_event(db, conversation_id, pair_count)
    logger.info("hitl_trigger_fired", conversation_id=conversation_id, pair_count=pair_count)

    return CheckTriggerResponse(
        should_prompt=True,
        event_id=event.id,
        message=_POPUP_MESSAGE,
    )


# ── POST /hitl/events/respond ─────────────────────────────────────────────────


@router.post("/hitl/events/respond", response_model=RespondResponse)
async def respond(
    body: RespondRequest,
    db: AsyncSession = Depends(get_db),
):
    """Chat service calls this after user accepts or rejects the compression popup."""
    if body.user_response not in ("accepted", "rejected"):
        raise HTTPException(status_code=422, detail="user_response must be accepted or rejected")

    event = await review_store.update_event_response(db, body.event_id, body.user_response)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    logger.info(
        "hitl_user_responded",
        event_id=body.event_id,
        conversation_id=body.conversation_id,
        response=body.user_response,
    )

    return RespondResponse(
        event_id=event.id,
        status=event.status,
        responded_at=event.responded_at,
    )


# ── GET /hitl/events ──────────────────────────────────────────────────────────


@router.get("/hitl/events", response_model=EventListResponse)
async def list_events(
    conversation_id: str | None = Query(None),
    feature_key: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List HITL events with optional filters."""
    events = await review_store.list_events(
        db,
        conversation_id=conversation_id,
        feature_key=feature_key,
        status=status,
        limit=limit,
    )
    return EventListResponse(
        events=[EventListItem.model_validate(e) for e in events],
        total=len(events),
    )


# ── POST /hitl/features/sensitive_data/check ──────────────────────────────────


@router.post("/hitl/features/sensitive_data/check", response_model=CheckTriggerResponse)
async def check_sensitive_data(
    conversation_id: str = Body(...),
    message: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Check if message contains sensitive data."""
    feature = await review_store.get_feature(db, "sensitive_data_detection")
    if not feature or not feature.enabled:
        return CheckTriggerResponse(should_prompt=False)

    detected = detect_sensitive_data(message)
    
    if not detected:
        return CheckTriggerResponse(should_prompt=False)

    event = await review_store.create_event(
        db,
        conversation_id,
        0,
        feature_key="sensitive_data_detection",
        event_metadata={"detected_types": list(detected.keys()), "message_preview": message[:100]},
    )
    
    logger.info(
        "sensitive_data_detected",
        conversation_id=conversation_id,
        types=list(detected.keys()),
    )

    return CheckTriggerResponse(
        should_prompt=True,
        event_id=event.id,
        message=f"⚠️ Detected sensitive data: {', '.join(detected.keys())}. Mask and continue?",
    )


# ── POST /hitl/features/model_switch/check ────────────────────────────────────


@router.post("/hitl/features/model_switch/check", response_model=CheckTriggerResponse)
async def check_model_switch(
    conversation_id: str = Body(...),
    query: str = Body(...),
    current_model: str = Body("gpt-3.5-turbo"),
    db: AsyncSession = Depends(get_db),
):
    """Check if query complexity requires model switch."""
    feature = await review_store.get_feature(db, "model_switch_recommendation")
    if not feature or not feature.enabled:
        return CheckTriggerResponse(should_prompt=False)

    analysis = analyze_query_complexity(query)
    
    if not analysis["is_complex"]:
        return CheckTriggerResponse(should_prompt=False)

    suggested = suggest_model(analysis["complexity_score"], current_model)
    
    if suggested == current_model:
        return CheckTriggerResponse(should_prompt=False)

    event = await review_store.create_event(
        db,
        conversation_id,
        0,
        feature_key="model_switch_recommendation",
        event_metadata={
            "complexity_score": analysis["complexity_score"],
            "current_model": current_model,
            "suggested_model": suggested,
            "reasons": analysis["reasons"],
        },
    )
    
    logger.info(
        "model_switch_recommended",
        conversation_id=conversation_id,
        score=analysis["complexity_score"],
        suggested=suggested,
    )

    return CheckTriggerResponse(
        should_prompt=True,
        event_id=event.id,
        message=f"🚀 Complex query detected. Switch to {suggested} for better results?",
    )
