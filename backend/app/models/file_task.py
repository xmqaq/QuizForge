import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class FileType(str, enum.Enum):
    pdf = "pdf"
    word = "word"
    txt = "txt"
    markdown = "markdown"


class FileTaskStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class FileTask(Base):
    __tablename__ = "file_task"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("user.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    status = Column(Enum(FileTaskStatus), default=FileTaskStatus.pending, nullable=False)
    parsed_content = Column(Text, nullable=True)
    questions_generated = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
