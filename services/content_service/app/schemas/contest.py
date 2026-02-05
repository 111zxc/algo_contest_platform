from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContestBase(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True


class ContestCreate(ContestBase):
    pass


class ContestRead(ContestBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None


class ContestJoin(BaseModel):
    username: str
