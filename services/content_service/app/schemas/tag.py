from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
