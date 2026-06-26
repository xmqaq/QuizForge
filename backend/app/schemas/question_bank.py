import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.question_bank import BankStatus


class QuestionBankCreate(BaseModel):
    title: str
    description: str | None = None
    category_id: int | None = None
    is_public: bool = True
    status: BankStatus = BankStatus.draft


class QuestionBankUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category_id: int | None = None
    is_public: bool | None = None
    status: BankStatus | None = None


class QuestionBankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    category_id: int | None
    created_by: uuid.UUID | None
    is_public: bool
    status: BankStatus
    question_count: int
    created_at: datetime
    updated_at: datetime
