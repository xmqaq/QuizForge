import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.quiz_session import QuizMode, SessionStatus


class QuizSessionCreate(BaseModel):
    bank_id: uuid.UUID
    mode: QuizMode = QuizMode.random
    total_questions: int | None = None
    time_limit_seconds: int | None = None


class QuizSessionUpdate(BaseModel):
    answered_count: int | None = None
    correct_count: int | None = None
    finished_at: datetime | None = None
    status: SessionStatus | None = None


class QuizSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    bank_id: uuid.UUID
    mode: QuizMode
    total_questions: int | None
    answered_count: int
    correct_count: int
    time_limit_seconds: int | None
    started_at: datetime
    finished_at: datetime | None
    status: SessionStatus
