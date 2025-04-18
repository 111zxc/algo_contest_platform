from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ContestBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class ContestCreate(ContestBase):
    pass

class ContestRead(ContestBase):
    id: UUID
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class ContestJoin(BaseModel):
        user_keycloak_id: str