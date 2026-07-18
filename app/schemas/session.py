import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.session import SessionStatus, SessionVisibility


class SessionCreate(BaseModel):
    title: str
    visibility: SessionVisibility = SessionVisibility.private
    starts_at: datetime | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    title: str
    join_code: str
    status: SessionStatus
    visibility: SessionVisibility
    starts_at: datetime | None
    ends_at: datetime | None

    class Config:
        from_attributes = True


class SessionPreview(BaseModel):
    session_id: uuid.UUID
    title: str
    status: SessionStatus
    live_attendee_count: int


class AttendeeJoinRequest(BaseModel):
    display_name: str | None = None


class AttendeeJoinResponse(BaseModel):
    attendee_token: str
    session_id: uuid.UUID
    display_name: str | None