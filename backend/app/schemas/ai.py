import uuid

from pydantic import BaseModel, Field

from app.models.question import Difficulty


class GenerateRequest(BaseModel):
    bank_id: uuid.UUID
    topic: str = Field(examples=["SQL注入攻击原理与防御"])
    difficulty: Difficulty = Difficulty.medium
    count: int = Field(default=10, ge=1, le=100)
    auto_approve: bool = False


class GenerateResponse(BaseModel):
    task_id: str
    message: str = "任务已提交"


class GenerateFromFileResponse(BaseModel):
    task_id: str
    file_task_id: str


class SuggestTopicsRequest(BaseModel):
    bank_title: str = Field(..., min_length=1, max_length=100, description="题库标题")


class SuggestTopicsResponse(BaseModel):
    topics: list[str]
