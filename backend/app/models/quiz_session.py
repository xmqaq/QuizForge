import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class QuizMode(str, enum.Enum):
    sequential = "sequential"
    random = "random"
    wrong_only = "wrong_only"
    simulation = "simulation"


class SessionStatus(str, enum.Enum):
    active = "active"
    finished = "finished"
    abandoned = "abandoned"


class QuizSession(Base):
    __tablename__ = "quiz_session"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("user.id"), nullable=False)
    bank_id = Column(Uuid, ForeignKey("question_bank.id"), nullable=False)
    mode = Column(Enum(QuizMode), default=QuizMode.random, nullable=False)
    total_questions = Column(Integer, nullable=True)
    answered_count = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    time_limit_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.active, nullable=False)

    user = relationship("User", back_populates="sessions")
    bank = relationship("QuestionBank", back_populates="sessions")
    answers = relationship("QuizAnswer", back_populates="session", cascade="all, delete-orphan")
