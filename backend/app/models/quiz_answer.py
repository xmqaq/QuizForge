import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.question import AnswerChoice


class QuizAnswer(Base):
    __tablename__ = "quiz_answer"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("quiz_session.id"), nullable=False)
    question_id = Column(Uuid, ForeignKey("question.id"), nullable=False)
    user_answer = Column(Enum(AnswerChoice), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    answered_at = Column(DateTime, default=func.now(), nullable=False)

    session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")
