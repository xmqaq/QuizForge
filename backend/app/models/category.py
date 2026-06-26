import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Industry(str, enum.Enum):
    it = "it"
    medical = "medical"
    finance = "finance"
    education = "education"
    construction = "construction"
    language = "language"
    other = "other"


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True)
    parent_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    industry = Column(Enum(Industry), nullable=False, default=Industry.other)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    banks = relationship("QuestionBank", back_populates="category")
