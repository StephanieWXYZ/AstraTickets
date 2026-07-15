from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import UserRole


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        full_name = value.strip()
        if not full_name:
            raise ValueError("Full name cannot be blank")
        return full_name


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
