from typing import Any

from pydantic import BaseModel, Field


class AudioTranscriptionChunkResponse(BaseModel):
    sessionId: str
    chunkIndex: int
    text: str = ''
    durationMs: int | None = None
    mimeType: str | None = None


class AudioTranscriptionFinalizeChunk(BaseModel):
    chunkIndex: int = Field(ge=0)
    text: str = ''


class AudioTranscriptionFinalizeRequest(BaseModel):
    sessionId: str = Field(min_length=1, max_length=128)
    chunks: list[AudioTranscriptionFinalizeChunk] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioTranscriptionFinalizeResponse(BaseModel):
    sessionId: str
    text: str = ''
    chunkCount: int = 0
