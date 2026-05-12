from typing import Any

from pydantic import BaseModel, Field


class ResumeSaveRequest(BaseModel):
    title: str = Field(default='我的简历', max_length=255)
    content: dict[str, Any] = Field(default_factory=dict)


class ResumeResponse(BaseModel):
    id: int | None = None
    title: str = '我的简历'
    content: dict[str, Any] = Field(default_factory=dict)
    updatedAt: str | None = None
