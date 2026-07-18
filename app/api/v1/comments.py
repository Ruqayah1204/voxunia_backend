import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.attendee_deps import get_current_attendee_optional
from app.core.deps import get_current_user_optional
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.user import User
from app.models.comment import Comment
from app.models.session import Session as SessionModel, SessionStatus
from app.models.question import Question
from app.schemas.comment import CommentCreate, CommentResponse
from app.api.v1.questions import _check_session_is_live

from app.websocket.manager import manager


router = APIRouter(tags=["Comments"])

def _comment_to_response(comment: Comment) -> CommentResponse:
    if comment.author_user_id:
        return CommentResponse(
            id=comment.id,
            question_id=comment.question_id,
            body=comment.body,
            author_name=comment.author_user.name,
            author_type="organizer",
            created_at=comment.created_at,
        )
    return CommentResponse(
        id=comment.id,
        question_id=comment.question_id,
        body=comment.body,
        author_name=comment.author_attendee.display_name or "Anonymous",
        author_type="attendee",
        created_at=comment.created_at,
    )

@router.post("/questions/{question_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    question_id: uuid.UUID,
    payload: CommentCreate,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    current_attendee: Attendee | None = Depends(get_current_attendee_optional),
):
    if current_user is None and current_attendee is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    _check_session_is_live(db, question.session_id)

    comment = Comment(
        question_id=question_id,
        body=payload.body,
        author_user_id=current_user.id if current_user else None,
        author_attendee_id=current_attendee.id if current_attendee else None,
        
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    response = _comment_to_response(comment)
    await manager.broadcast(
        str(question.session_id),
        {"type": "new_comment", "question_id": str(question_id), "comment": response.model_dump(mode="json")},
    )
    return response
