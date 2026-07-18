import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.group import Group
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


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
    return group


@router.get("", response_model=list[GroupResponse])
def group_list(db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Group).filter(Group.organizer_id == current_user.id).all()


@router.get("/{group_id}", response_model=GroupResponse)
def get_single_group(group_id: uuid.UUID, db: DBSession = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group
