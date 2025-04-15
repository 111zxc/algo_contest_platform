from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    display_name: str | None = None
    first_name: str
    last_name: str


class UserRegistration(UserBase):
    password: str


class UserCreate(UserBase):
    keycloak_id: str


class UserRead(UserBase):
    keycloak_id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
        from_attributes = True


class UserReadExtended(UserRead):
    rating: int | None = None
