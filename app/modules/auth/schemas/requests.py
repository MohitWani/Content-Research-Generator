from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description='Email for authentication')
    password: str = Field(..., description='Password for authentication')


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ..., description='Refresh token to exchange for new access token'
    )
