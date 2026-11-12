import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.group import Group
from app.models.session import Session as SessionModel
from app.models.attendee import Attendee
from app.models.question import Question
from app.models.vote import Vote
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse

router = APIRouter(prefix="/groups", tags=["Groups"])

def _to_group_response(db: DBSession, group: Group) -> GroupResponse:
    session_ids = select(SessionModel.id).where(SessionModel.group_id == group.id)

    total_session_count = db.query(SessionModel).filter(SessionModel.group_id == group.id).count()
    total_attendee_count = db.query(Attendee).filter(Attendee.session_id.in_(session_ids)).count()
    total_question_count = db.query(Question).filter(Question.session_id.in_(session_ids)).count()
    total_vote_count = (
        db.query(Vote)
        .join(Question, Vote.question_id == Question.id)
        .filter(Question.session_id.in_(session_ids))
        .count()
    )

    return GroupResponse.model_validate(group).model_copy(
        update={
            "total_session_count": total_session_count,
            "total_attendee_count": total_attendee_count,
            "total_question_count": total_question_count,
            "total_vote_count": total_vote_count
        }
    )


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") 

@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    payload: GroupCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = slugify(payload.name)
    if db.query(Group).filter(Group.slug == slug).first():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    group = Group(
        organizer_id=current_user.id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        tags=payload.tags,
        cover_image_url=payload.cover_image_url,
        location=payload.location,
        virtual_link=payload.virtual_link
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return _to_group_response(db, group)


@router.get("", response_model=list[GroupResponse])
def group_list(db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    groups = db.query(Group).filter(Group.organizer_id == current_user.id).all()
    return [_to_group_response(db, group) for group in groups]


@router.get("/{group_id}", response_model=GroupResponse)
def get_single_group(group_id: uuid.UUID, db: DBSession = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    
    return _to_group_response(db, group)
