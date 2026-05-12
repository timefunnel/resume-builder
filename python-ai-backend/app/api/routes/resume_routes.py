from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user
from app.api.schemas.resume import ResumeResponse, ResumeSaveRequest
from app.application.use_cases.resume_current import get_current_resume, save_current_resume

router = APIRouter(prefix='/api/resumes', tags=['resumes'])


@router.get('/current', response_model=ResumeResponse)
def get_current_resume_route(current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**get_current_resume(current_user.id))


@router.put('/current', response_model=ResumeResponse)
def save_current_resume_route(request: ResumeSaveRequest, current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**save_current_resume(current_user.id, request.title, request.content))
