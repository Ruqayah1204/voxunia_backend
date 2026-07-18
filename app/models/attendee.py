import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Attendee(Base):
    """
        NOT a user account. Created when someone joins a session via code/QR.
        `token` is stored client-side to identify this attendee within THIS session only.
    """

    __tablename__ = "attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True) #null = "Anonymous"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
