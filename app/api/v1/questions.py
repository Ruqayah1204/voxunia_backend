import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.attendee_deps import get_current_attendee
from app.core.attendee_deps import get_current_attendee_optional
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.attendee import Attendee
from app.models.user import User
from app.models.group import Group
from app.models.question import Question, QuestionStatus
from app.models.vote import Vote
from app.schemas.question import QuestionCreate, QuestionResponse, VoteRequest, QuestionModerationRequest
from app.models.session import Session as SessionModel, SessionStatus
from app.websocket.manager import manager

router = APIRouter(tags=["Questions"])

def _to_response(q: Question, my_vote: int | None = None) -> QuestionResponse:
    return QuestionResponse(
        id=q.id,
        body=q.body,
        vote_score=q.vote_score,
        status=q.status,
        display_name=q.attendee.display_name if q.attendee else None,
        created_at=q.created_at,
        my_vote=my_vote
    )

def _check_session_is_live(db: DBSession, session_id: uuid.UUID) -> None:
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.status == SessionStatus.upcoming:
        raise HTTPException(status_code=400, detail="This session hasn't started yet")
    if session_obj.status == SessionStatus.ended:
        raise HTTPException(status_code=400, detail="This session has ended")


@router.post("/sessions/{session_id}/questions", response_model=QuestionResponse, status_code=201)
async def post_question(
    session_id: uuid.UUID,
    payload: QuestionCreate,
    db: DBSession = Depends(get_db),
    attendee: Attendee = Depends(get_current_attendee),
):
    if attendee.session_id != session_id:
        raise HTTPException(status_code=403, detail="Attendee token does not match this session")
    
    _check_session_is_live(db, session_id)
    
    question = Question(
        session_id=session_id,
        attendee_id=attendee.id,
        body=payload.body,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    response = _to_response(question)
    await manager.broadcast(
        str(session_id),
        {"type": "new_question", "question": response.model_dump(mode="json")},
    )
    return response

@router.get("/sessions/{session_id}/questions", response_model=list[QuestionResponse])
def get_questions_list(
    session_id: uuid.UUID,
    db: DBSession = Depends(get_db),
    attendee: Attendee | None = Depends(get_current_attendee_optional)
):
    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id, Question.status != QuestionStatus.hidden)
        .order_by(Question.vote_score.desc(), Question.created_at.asc())
        .all()
    )

    my_votes = {}
    if attendee:
        votes = db.query(Vote).filter(
            Vote.attendee_id == attendee.id,
            Vote.question_id.in_([q.id for q in questions]),
        ).all()

        my_votes = {v.question_id: v.value for v in votes}
    


    return [_to_response(q, my_vote=my_votes.get(q.id)) for q in questions]


@router.post("/questions/{question_id}/vote", response_model=QuestionResponse)
async def vote_question(
    question_id: uuid.UUID,
    payload: VoteRequest,
    db: DBSession = Depends(get_db),
    attendee: Attendee = Depends(get_current_attendee),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    _check_session_is_live(db, question.session_id)
    
    if payload.value not in (1, -1):
        raise HTTPException(status_code=400, detail="Vote value must be 1 or -1")
    
    existing_vote = (
        db.query(Vote)
        .filter(Vote.question_id == question_id, Vote.attendee_id == attendee.id)
        .first()
    )

    if existing_vote:
        if existing_vote.value == payload.value:
            question.vote_score -= existing_vote.value
            db.delete(existing_vote)
            new_my_vote = None
        else:
            question.vote_score += payload.value - existing_vote.value
            existing_vote.value = payload.value
            new_my_vote = payload.value
    else:
        db.add(Vote(question_id=question_id, attendee_id=attendee.id, value=payload.value))
        question.vote_score += payload.value
        new_my_vote = payload.value

    db.commit()
    db.refresh(question)
    response = _to_response(question, my_vote=new_my_vote)
    await manager.broadcast(
        str(question.session_id),
        {"type": "vote_update", "question_id": str(question.id), "vote_score": question.vote_score},
    )
    return response


@router.patch('/questions/{question_id}', response_model=QuestionResponse)
def edit_question(
    question_id: uuid.UUID,
    payload:QuestionModerationRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = (
        db.query(Question)
        .join(SessionModel, Question.session_id == SessionModel.id)
        .join(Group, SessionModel.group_id == Group.id)
        .filter(Question.id == question_id, Group.organizer_id == current_user.id)
        .first()
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.status = payload.status
    
    db.commit()
    db.refresh(question)
    return _to_response(question)
    

