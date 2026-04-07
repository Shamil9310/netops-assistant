from pydantic import BaseModel, Field


class CurrentUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    is_active: bool


class ErrorResponse(BaseModel):
    detail: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=128)


class LoginResponse(BaseModel):
    message: str
    user: CurrentUserResponse
