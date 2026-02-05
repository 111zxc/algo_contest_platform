from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.tag import TagRead


class DifficultyEnum(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class TestCase(BaseModel):
    input_data: str
    output_data: str

    def to_dict(self):
        return {"input_data": self.input_data, "output_data": self.output_data}


class ProblemBase(BaseModel):
    title: str
    description: str
    difficulty: DifficultyEnum
    test_cases: Optional[list[TestCase]] = None
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None
    contest_id: Optional[UUID] = None


class ProblemCreate(ProblemBase):
    pass


class ProblemRead(ProblemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID  # если в БД у тебя str, лучше сделать str; я оставил как было
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[TagRead]


class ProblemReadExtended(ProblemRead):
    author_display_name: str | None = None
    reaction_balance: int | None = 0


class ProblemReadWithReaction(ProblemReadExtended):
    user_reaction: str | None = None
