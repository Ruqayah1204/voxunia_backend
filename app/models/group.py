import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Column, DateTime, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Group(Base):
    """A persistent meetup community. Hosts many sessions over time."""

    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)
    cover_image_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    virtual_link = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("Session", back_populates="group", cascade="all, delete-orphan")
