from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class BlogPostBase(BaseModel):
    title: str
    description: str

class BlogPostCreate(BlogPostBase):
    ...

class BlogPostRead(BlogPostBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
