# author: jf
from typing import Any, Protocol


class InterviewSessionRepository(Protocol):
    def get(self, user_id: int, session_id: str) -> dict[str, Any] | None: ...

    def save(self, user_id: int, session_id: str, session: dict[str, Any]) -> None: ...

    def list(self, user_id: int, limit: int) -> list[dict[str, Any]]: ...
