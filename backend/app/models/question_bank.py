import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class BankStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String(32), nullable=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    created_by = Column(Uuid, ForeignKey("user.id"), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(BankStatus), default=BankStatus.draft, nullable=False)
    question_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="banks")
    creator = relationship("User", back_populates="banks")
    questions = relationship("Question", back_populates="bank", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="bank", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="bank", cascade="all, delete-orphan")
