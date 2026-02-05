from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.tag import TagRead


class PostBase(BaseModel):
    title: str
    content: str
    language: str | None = None
    status: str | None = None


class PostCreate(PostBase):
    problem_id: UUID


class PostRead(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    problem_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[TagRead]
    created_by: str


class PostReadExtended(PostRead):
    author_display_name: str | None = None
    reaction_balance: int | None = 0


class PostReadWithReaction(PostReadExtended):
    user_reaction: str | None = None
