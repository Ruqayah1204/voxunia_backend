import secrets
import string
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.group import Group
from app.models.session import Session as SessionModel, SessionStatus
from app.models.user import User
from app.schemas.session import (
    AttendeeJoinRequest,
    AttendeeJoinResponse,
    SessionCreate,
    SessionPreview,
    SessionResponse,
)

router = APIRouter(tags=["Sessions"])

# Helper function to generate a unique join code for a session
def generate_join_code(db: DBSession) -> str:
    alphabet = string.ascii_uppercase + string. digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(settings.session_join_code_length))
        if not db.query(SessionModel).filter(SessionModel.join_code == code).first():
            return code

# API endpoint to create a new session for a specific group
@router.post("/groups/{group_id}/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    group_id: uuid.UUID,
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id, Group.organizer_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    session_obj = SessionModel(
        group_id=group.id,
        title=payload.title,
        join_code=generate_join_code(db),
        visibility=payload.visibility,
        starts_at=payload.starts_at,
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj


# API endpoint to retrieve all sessions for a specific group
@router.get("/groups/{group_id}/sessions", response_model=list[SessionResponse])
def get_sessions_for_group(
    group_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id, Group.organizer_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    sessions = db.query(SessionModel).filter(SessionModel.group_id == group.id).all()
    return sessions

# API endpoint to preview a session using its join code
@router.get("/sessions/preview/{join_code}", response_model=SessionPreview)
def preview_session(join_code: str, db: DBSession = Depends(get_db)):
    session_obj = db.query(SessionModel).filter(SessionModel.join_code == join_code).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.status == SessionStatus.ended:
        raise HTTPException(status_code=410, detail="This session has ended")
    
    live_count = db.query(Attendee).filter(Attendee.session_id == session_obj.id).count() # counts the number of attendees in the session

    return SessionPreview(
        session_id=session_obj.id,
        title=session_obj.title,
        status=session_obj.status,
        live_attendee_count=live_count,
    )

@router.post("/sessions/{session_id}/join", response_model=AttendeeJoinResponse)
def join_session(
    session_id: uuid.UUID,
    payload: AttendeeJoinRequest,
    db: DBSession = Depends(get_db),
):
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    attendee = Attendee(
        session_id=session_obj.id,
        token=secrets.token_urlsafe(24),  # generates a secure random token for the attendee
        display_name=payload.display_name,
    )
    db.add(attendee)
    db.commit()
    db.refresh(attendee)
    
    return AttendeeJoinResponse(
        attendee_token=attendee.token,
        session_id=session_obj.id,
        display_name=attendee.display_name,
    )


@router.patch("/sessions/{session_id}/start", response_model=SessionResponse)
def start_session(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session_obj = (
        db.query(SessionModel)
        .join(Group)
        .filter(SessionModel.id == session_id, Group.organizer_id == current_user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.status != SessionStatus.upcoming:
        raise HTTPException(status_code=400, detail="Only an upcoming session can be started")

    session_obj.status = SessionStatus.live
    db.commit()
    db.refresh(session_obj)
    return session_obj

@router.patch("/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_obj = (
        db.query(SessionModel)
        .join(Group)
        .filter(SessionModel.id == session_id, Group.organizer_id == current_user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_obj.status = SessionStatus.ended
    session_obj.ends_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session_obj)
    return session_obj
