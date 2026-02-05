from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TargetType(str, Enum):
    post = "post"
    comment = "comment"
    problem = "problem"


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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    created_by: str


class ReactionListResponse(BaseModel):
    balance: int
    reactions: list[ReactionRead]
