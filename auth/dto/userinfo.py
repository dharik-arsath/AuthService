from pydantic import BaseModel, EmailStr, Field, SecretStr


class   UserCreate(BaseModel):
    full_name: str = Field(min_length=3)
    username: EmailStr
    phone_number: str = Field(min_length=10, max_length=10, pattern="[0-9]{10}")
    # alternate_phone_number: Optional[str] = Field(default=None)


class UserInfo(UserCreate):
    user_id: int = Field(alias="id", default=None)

    class Config:
        from_attributes = True


class UserPrivate(UserCreate):
    password: SecretStr = Field(min_length=6)


class AuthCredentials(BaseModel):
    username: EmailStr
    password: SecretStr = Field(min_length=1)
