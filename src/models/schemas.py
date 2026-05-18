"""Pydantic request/response schemas for HITL service."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CheckTriggerResponse(BaseModel):
    should_prompt: bool
    event_id: str | None = None
    message: str | None = None


class RespondRequest(BaseModel):
    event_id: str
    conversation_id: str
    feature_key: str
    pair_count: int
    user_response: str = Field(..., description="accepted | rejected")


class RespondResponse(BaseModel):
    event_id: str
    status: str
    responded_at: datetime | None = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class EventListItem(BaseModel):
    id: str
    conversation_id: str
    feature_key: str
    pair_count: int
    status: str
    user_response: str | None
    created_at: datetime
    responded_at: datetime | None

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: list[EventListItem]
    total: int
