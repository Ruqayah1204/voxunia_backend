import secrets
import string
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from app.core.config import settings
from app.core.deps import get_current_user, get_current_user_optional
from app.core.attendee_deps import get_current_attendee_optional
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.group import Group
from app.models.question import Question
from app.models.vote import Vote
from app.models.session import Session as SessionModel, SessionStatus
from app.models.user import User
from app.schemas.session import (
    AttendeeJoinRequest,
    AttendeeJoinResponse,
    SessionCreate,
    SessionPreview,
    SessionResponse,
    SessionDetailResponse,
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


# API endpoint to get single session details by session ID
@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_single_session(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    current_attendee: Attendee | None = Depends(get_current_attendee_optional),
):
    if current_user is None and current_attendee is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Organizer must own the group this session belongs to
    if current_user is not None:
        group = db.query(Group).filter(Group.id == session_obj.group_id).first()
        if not group or group.organizer_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")

    # Attendee's token must belong to THIS session specifically
    if current_attendee is not None and current_attendee.session_id != session_id:
        raise HTTPException(status_code=403, detail="Attendee token does not match this session")

    attendee_count = db.query(Attendee).filter(Attendee.session_id == session_id).count()
    question_count = db.query(Question).filter(Question.session_id == session_id).count()
    vote_count = (
        db.query(func.count(Vote.id))
        .join(Question, Vote.question_id == Question.id)
        .filter(Question.session_id == session_id)
        .scalar()
    ) or 0

    return SessionDetailResponse(
        id=session_obj.id,
        group_id=session_obj.group_id,
        title=session_obj.title,
        join_code=session_obj.join_code,
        status=session_obj.status,
        visibility=session_obj.visibility,
        starts_at=session_obj.starts_at,
        ends_at=session_obj.ends_at,
        live_attendee_count=attendee_count,
        total_question_count=question_count,
        total_vote_count=vote_count
    )

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
        starts_at=session_obj.starts_at
    )


# API to join a session using its ID and an optional display name
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

# API endpoint to start a session, changing its status to "live"
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
    if session_obj.status == SessionStatus.ended:
        raise HTTPException(status_code=400, detail="This session has already ended")

    session_obj.status = SessionStatus.live
    session_obj.starts_at = datetime.now(timezone.utc)

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
