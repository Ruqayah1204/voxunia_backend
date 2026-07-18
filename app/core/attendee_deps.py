"""
    This module provides dependencies related to the 
    Attendee model, including a function to retrieve the 
    current attendee based on a provided token.
"""


from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db
from app.models.attendee import Attendee


def get_current_attendee(
        x_attendee_token: str = Header(..., description="Token returned from POST /sessions/{id}/join"),
        db: DBSession = Depends(get_db),
) -> Attendee:
    attendee = db.query(Attendee).filter(Attendee.token == x_attendee_token).first()
    if not attendee:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired attendee session"
        )
    return attendee


def get_current_attendee_optional(
    x_attendee_token: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
) -> Attendee | None:
    if not x_attendee_token:
        return None
    return db.query(Attendee).filter(Attendee.token == x_attendee_token).first()