from pydantic import BaseModel, SecretStr, Field, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    alternate_phone_number: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True


class UserInfo(UserCreate):
    user_id: int = Field(alias="id", default=None)

    class Config:
        orm_mode = True


class UserPrivate(UserCreate):
    password: SecretStr


class AuthCredentials(BaseModel):
    username: str
    password: SecretStr


class UserAuthData(BaseModel):
    user_id: int
    password: SecretStr
