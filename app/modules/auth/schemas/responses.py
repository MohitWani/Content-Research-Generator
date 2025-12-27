from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    access_token: str = Field(..., description='JWT access token')
    refresh_token: str = Field(..., description='JWT refresh token')
    token_type: str = Field(default='bearer', description='Token type')
    expires_in: int = Field(..., description='Access token expiration time in seconds')
    user_id: str = Field(..., description='User ID')


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description='New JWT access token')
    token_type: str = Field(default='bearer', description='Token type')
    expires_in: int = Field(..., description='Access token expiration time in seconds')
