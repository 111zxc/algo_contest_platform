from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

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
    test_cases: Optional[List[TestCase]] = None
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None


class ProblemCreate(ProblemBase):
    pass


class ProblemRead(ProblemBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: list[TagRead]

    class Config:
        orm_mode = True

class ProblemReadExtended(ProblemRead):
    author_display_name: str | None = None
