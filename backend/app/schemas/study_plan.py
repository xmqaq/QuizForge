import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StudyPlanCreate(BaseModel):
    bank_id: uuid.UUID
    target_date: date
    daily_new_questions: int = 10
    daily_review_questions: int = 5


class StudyPlanUpdate(BaseModel):
    target_date: date | None = None
    daily_new_questions: int | None = None
    daily_review_questions: int | None = None
    is_active: bool | None = None


class StudyPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    bank_id: uuid.UUID
    target_date: date
    daily_new_questions: int
    daily_review_questions: int
    is_active: bool
    created_at: datetime
