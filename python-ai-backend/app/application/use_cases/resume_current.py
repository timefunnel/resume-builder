from fastapi import HTTPException

from app.bootstrap.container import build_resume_repository, resolve_settings


def list_resumes(user_id: int) -> list[dict]:
    repository = build_resume_repository(resolve_settings())
    return repository.list_by_user_id(user_id)


def create_resume(user_id: int, title: str, content: dict) -> dict:
    repository = build_resume_repository(resolve_settings())
    return repository.create(user_id=user_id, title=title, content=content)


def get_resume(user_id: int, resume_id: int) -> dict:
    repository = build_resume_repository(resolve_settings())
    result = repository.get_by_id(user_id=user_id, resume_id=resume_id)
    if not result:
        raise HTTPException(status_code=404, detail='Resume not found')
    return result


def update_resume(user_id: int, resume_id: int, title: str, content: dict) -> dict:
    repository = build_resume_repository(resolve_settings())
    result = repository.update(user_id=user_id, resume_id=resume_id, title=title, content=content)
    if not result:
        raise HTTPException(status_code=404, detail='Resume not found')
    return result


def delete_resume(user_id: int, resume_id: int) -> None:
    repository = build_resume_repository(resolve_settings())
    deleted = repository.soft_delete(user_id=user_id, resume_id=resume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Resume not found')


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
