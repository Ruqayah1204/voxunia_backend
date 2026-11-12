import uuid
from datetime import datetime

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = []
    cover_image_url: str | None = None
    location: str | None = None
    virtual_link: str | None = None


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    tags: list[str]
    cover_image_url: str | None
    location: str | None
    virtual_link: str | None
    created_at: datetime

    total_session_count: int = 0
    total_attendee_count: int = 0
    total_question_count: int = 0
    total_vote_count: int = 0

    class Config:
        from_attributes = True