from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.tag import TagRead


class PostBase(BaseModel):
    content: str
    language: str | None = None
    status: str | None = None


class PostCreate(PostBase):
    problem_id: UUID


class PostRead(PostBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[TagRead]
    created_by: str

    class Config:
        orm_mode = True
