import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.question import AnswerChoice


class QuizAnswerCreate(BaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: AnswerChoice
    time_spent_seconds: int | None = None


class QuizAnswerUpdate(BaseModel):
    user_answer: AnswerChoice | None = None
    is_correct: bool | None = None
    time_spent_seconds: int | None = None


class QuizAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: AnswerChoice
    is_correct: bool
    time_spent_seconds: int | None
    answered_at: datetime


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    user_answer: AnswerChoice
    time_spent_seconds: int | None = None


class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: AnswerChoice
    explanation: str | None
    answered_count: int
    correct_count: int
