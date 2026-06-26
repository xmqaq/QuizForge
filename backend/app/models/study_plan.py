import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plan"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("user.id"), nullable=False)
    bank_id = Column(Uuid, ForeignKey("question_bank.id"), nullable=False)
    target_date = Column(Date, nullable=False)
    daily_new_questions = Column(Integer, default=10, nullable=False)
    daily_review_questions = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="study_plans")
    bank = relationship("QuestionBank")
