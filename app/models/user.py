import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class UserRole(str, enum.Enum):
    organizer = 'organizer'
    admin = 'admin'

class User(Base):
    """For Admin/Organisers.
        Attendee are NOT users - seperate model
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.organizer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
