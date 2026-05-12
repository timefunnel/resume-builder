from app.bootstrap.container import build_resume_repository, resolve_settings


def get_current_resume(user_id: int) -> dict:
    repository = build_resume_repository(resolve_settings())
    return repository.get_current(user_id) or {
        'id': None,
        'title': '我的简历',
        'content': {},
        'updatedAt': None,
    }


def save_current_resume(user_id: int, title: str, content: dict) -> dict:
    repository = build_resume_repository(resolve_settings())
    return repository.save_current(user_id=user_id, title=title, content=content)
