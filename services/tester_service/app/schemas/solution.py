from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SolutionStatus(str, Enum):
    PENDING = "pending"
    TLE = "TLE"
    WA = "WA"
    RE = "RE"
    AC = "AC"


class SolutionCreate(BaseModel):
    problem_id: str
    code: str
    language: str


class SolutionRead(BaseModel):
    id: UUID
    created_by: str
    problem_id: str
    code: str
    language: str
    status: SolutionStatus
    time_used: Optional[float]
    memory_used: Optional[int]
    faster_than: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
