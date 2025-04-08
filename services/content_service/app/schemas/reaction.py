from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class TargetType(str, Enum):
    post = "post"
    comment = "comment"


class ReactionType(str, Enum):
    plus = "plus"
    minus = "minus"


class ReactionBase(BaseModel):
    target_id: UUID
    target_type: TargetType
    reaction_type: ReactionType


class ReactionCreate(ReactionBase):
    pass


class ReactionRead(ReactionBase):
    id: UUID
    created_at: datetime
    created_by: str

    class Config:
        orm_mode = True


class ReactionListResponse(BaseModel):
    balance: int
    reactions: list[ReactionRead]
