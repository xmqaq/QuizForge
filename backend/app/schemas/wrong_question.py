import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WrongQuestionCreate(BaseModel):
    user_id: uuid.UUID
    question_id: uuid.UUID


class WrongQuestionUpdate(BaseModel):
    wrong_count: int | None = None
    is_mastered: bool | None = None
    mastered_at: datetime | None = None


class WrongQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    question_id: uuid.UUID
    wrong_count: int
    last_wrong_at: datetime
    is_mastered: bool
    mastered_at: datetime | None
