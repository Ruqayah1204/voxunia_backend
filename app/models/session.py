import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SessionStatus(str, enum.Enum):
    upcoming = "upcoming"
    live = "live"
    ended = "ended"

class SessionVisibility(str, enum.Enum):
    public = "public"
    private = "private"


class Session(Base):
    """A meetup session. Belongs to a group and has many attendees and questions."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    title = Column(String, nullable=False)
    join_code = Column(String(12), unique=True, index=True, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.upcoming, nullable=False)
    visibility = Column(Enum(SessionVisibility), default=SessionVisibility.private, nullable=False)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates="sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")
