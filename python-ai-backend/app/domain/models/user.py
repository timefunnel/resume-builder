from dataclasses import dataclass


@dataclass(slots=True)
class User:
    id: int
    email: str
    nickname: str | None = None
    status: str = "active"
