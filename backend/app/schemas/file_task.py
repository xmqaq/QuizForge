import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.file_task import FileTaskStatus, FileType


class FileTaskCreate(BaseModel):
    original_filename: str
    file_path: str
    file_type: FileType


class FileTaskUpdate(BaseModel):
    status: FileTaskStatus | None = None
    parsed_content: str | None = None
    questions_generated: int | None = None
    error_message: str | None = None


class FileTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    file_path: str
    file_type: FileType
    status: FileTaskStatus
    questions_generated: int
    error_message: str | None
    created_at: datetime
