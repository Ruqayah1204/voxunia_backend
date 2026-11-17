from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.group import Group
from app.models.question import Question
from app.models.session import Session as SessionModel, SessionStatus
from app.models.user import User
from app.schemas.dashboard import DashboardStatsResponse


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group_ids = select(Group.id).where(Group.organizer_id == current_user.id)
    session_ids = select(SessionModel.id).where(SessionModel.group_id.in_(group_ids))

    total_group_count = db.query(Group).filter(Group.organizer_id == current_user.id).count()

    total_session_count = (
        db.query(SessionModel)
        .filter(
            SessionModel.group_id.in_(group_ids),
            SessionModel.status != SessionStatus.upcoming
        )
        .count()
    )

    total_attendee_count = db.query(Attendee).filter(Attendee.session_id.in_(session_ids)).count()
    total_question_count = db.query(Question).filter(Question.session_id.in_(session_ids)).count()

    return DashboardStatsResponse(
        total_group_count=total_group_count,
        total_session_count=total_session_count,
        total_attendee_count=total_attendee_count,
        total_question_count=total_question_count
    )