from uuid import UUID

from pydantic import BaseModel


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: UUID

    class Config:
        orm_mode = True
        from_attributes = True
