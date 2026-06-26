import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class WrongQuestion(Base):
    __tablename__ = "wrong_question"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question"),)

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("user.id"), nullable=False)
    question_id = Column(Uuid, ForeignKey("question.id"), nullable=False)
    wrong_count = Column(Integer, default=1, nullable=False)
    last_wrong_at = Column(DateTime, default=func.now(), nullable=False)
    is_mastered = Column(Boolean, default=False, nullable=False)
    mastered_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="wrong_questions")
    question = relationship("Question", back_populates="wrong_records")
