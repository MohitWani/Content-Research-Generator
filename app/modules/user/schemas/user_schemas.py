from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description='User email address')
    first_name: str = Field(..., description='User first name')
    last_name: str = Field(..., description='User last name')
    password: str = Field(..., description='User password')


class UserResponse(BaseModel):
    id: str = Field(..., description='User ID')
    email: str = Field(..., description='User email')
    first_name: str = Field(..., description='User first name')
    last_name: str = Field(..., description='User last name')
    created_at: datetime | None = Field(None, description='User creation timestamp')
    updated_at: datetime | None = Field(None, description='User update timestamp')

    model_config = ConfigDict(from_attributes=True)
