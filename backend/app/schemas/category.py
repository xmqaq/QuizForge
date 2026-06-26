from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.category import Industry


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: int | None = None
    industry: Industry = Industry.other
    icon: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    parent_id: int | None = None
    industry: Industry | None = None
    icon: str | None = None
    sort_order: int | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None
    industry: Industry
    icon: str | None
    sort_order: int
    created_at: datetime
