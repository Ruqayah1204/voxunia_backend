import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class QuestionStatus(str, enum.Enum):
    visible = "visible"
    hidden = "hidden"
    answered = "answered"


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("attendees.id"), nullable=False)
    body = Column(Text, nullable=False)
    vote_score = Column(Integer, default=0, nullable=False)
    status = Column(Enum(QuestionStatus), default=QuestionStatus.visible, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Relationships - this is where we define how the Question model relates to other models in the database. Each question belongs to a session and an attendee, and can have many votes and comments associated with it.
    session = relationship("Session", back_populates="questions")
    attendee = relationship("Attendee")
    votes = relationship("Vote", back_populates="question", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="question", cascade="all, delete-orphan")