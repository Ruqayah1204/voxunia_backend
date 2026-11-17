from pydantic import BaseModel

class DashboardStatResponse(BaseModel):
    total_group_count: int = 0
    total_session_count: int = 0
    total_attendee_count: int = 0
    total_question_count: int = 0

    class Config:
        from_attributes = True 