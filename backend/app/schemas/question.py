import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import (
    AnswerChoice,
    Difficulty,
    QuestionSource,
    QuestionStatus,
)


class QuestionCreate(BaseModel):
    bank_id: uuid.UUID
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: AnswerChoice
    explanation: str | None = None
    difficulty: Difficulty = Difficulty.medium
    source: QuestionSource = QuestionSource.manual
    tags: list[str] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    content: str | None = None
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: AnswerChoice | None = None
    explanation: str | None = None
    difficulty: Difficulty | None = None
    status: QuestionStatus | None = None
    tags: list[str] | None = None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bank_id: uuid.UUID
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: AnswerChoice
    explanation: str | None
    difficulty: Difficulty
    source: QuestionSource
    status: QuestionStatus
    ai_model: str | None
    tags: list[str]
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
