import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AnswerChoice(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionSource(str, enum.Enum):
    ai_generated = "ai_generated"
    manual = "manual"
    imported = "imported"


class QuestionStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class Question(Base):
    __tablename__ = "question"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    bank_id = Column(Uuid, ForeignKey("question_bank.id"), nullable=False)
    content = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(Enum(AnswerChoice), nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(Enum(Difficulty), default=Difficulty.medium, nullable=False)
    source = Column(Enum(QuestionSource), default=QuestionSource.ai_generated, nullable=False)
    status = Column(Enum(QuestionStatus), default=QuestionStatus.pending_review, nullable=False)
    ai_model = Column(String(100), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    created_by = Column(Uuid, ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    bank = relationship("QuestionBank", back_populates="questions")
    creator = relationship("User")
    answers = relationship("QuizAnswer", back_populates="question")
    wrong_records = relationship("WrongQuestion", back_populates="question")
