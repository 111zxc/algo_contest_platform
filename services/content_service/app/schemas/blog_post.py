from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BlogPostBase(BaseModel):
    title: str
    description: str


class BlogPostCreate(BlogPostBase):
    pass


class BlogPostRead(BlogPostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
