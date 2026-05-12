from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=100)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        safe = (value or '').strip().lower()
        if '@' not in safe or '.' not in safe.split('@')[-1]:
            raise ValueError('invalid email')
        return safe


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        safe = (value or '').strip().lower()
        if '@' not in safe or '.' not in safe.split('@')[-1]:
            raise ValueError('invalid email')
        return safe


class UserProfileResponse(BaseModel):
    id: int
    email: str
    nickname: str | None = None
    status: str = 'active'
