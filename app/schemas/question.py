import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.question import QuestionStatus


class QuestionCreate(BaseModel):
    body: str


class QuestionResponse(BaseModel):
    id: uuid.UUID
    body: str
    vote_score: int
    status: QuestionStatus
    display_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    value: int  # +1 or -1


class QuestionModerationRequest(BaseModel):
    status: QuestionStatus