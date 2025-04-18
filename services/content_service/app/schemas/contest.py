from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ContestBase(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True


class ContestCreate(ContestBase):
    pass


class ContestRead(ContestBase):
    id: UUID
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
        from_attributes = True


class ContestJoin(BaseModel):
    username: str
