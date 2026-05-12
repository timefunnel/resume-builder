from typing import Any

from pydantic import BaseModel, Field


class ResumeImportAiResponse(BaseModel):
    title: str = Field(default='导入的简历', max_length=255)
    content: dict[str, Any] = Field(default_factory=dict)
    extractedText: str = ''
