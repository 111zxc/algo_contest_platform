from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CommentBase(BaseModel):
    content: str
    parent_comment_id: UUID | None = None


class CommentCreate(CommentBase):
    post_id: UUID


class CommentRead(CommentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: str

    class Config:
        orm_mode = True
