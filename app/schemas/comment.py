import uuid
from datetime import datetime

from pydantic import BaseModel

class CommentCreate(BaseModel):
    body: str

class CommentResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    # author_user_id: uuid.UUID | None
    # author_attendee_id: uuid.UUID | None
    author_name: str
    author_type: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True
