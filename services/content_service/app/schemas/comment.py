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
    post_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: str

    class Config:
        orm_mode = True
        from_attributes = True


class CommentReadExtended(CommentRead):
    author_display_name: str | None = None
    reaction_balance: int | None = 0


class CommentReadWithReaction(CommentReadExtended):
    user_reaction: str | None = None
