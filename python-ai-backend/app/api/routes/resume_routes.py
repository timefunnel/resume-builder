from fastapi import APIRouter, Depends, Response, status

from app.api.deps.auth import get_current_user
from app.api.schemas.resume import ResumeCreateRequest, ResumeResponse, ResumeSaveRequest, ResumeSummaryResponse
from app.application.use_cases.resume_current import (
    create_resume,
    delete_resume,
    get_current_resume,
    get_resume,
    list_resumes,
    save_current_resume,
    update_resume,
)

router = APIRouter(prefix='/api/resumes', tags=['resumes'])


@router.get('', response_model=list[ResumeSummaryResponse])
def list_resumes_route(current_user=Depends(get_current_user)) -> list[ResumeSummaryResponse]:
    return [ResumeSummaryResponse(**item) for item in list_resumes(current_user.id)]


@router.post('', response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume_route(request: ResumeCreateRequest, current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**create_resume(current_user.id, request.title, request.content))


@router.get('/current', response_model=ResumeResponse)
def get_current_resume_route(current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**get_current_resume(current_user.id))


@router.put('/current', response_model=ResumeResponse)
def save_current_resume_route(request: ResumeSaveRequest, current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**save_current_resume(current_user.id, request.title, request.content))


@router.get('/{resume_id}', response_model=ResumeResponse)
def get_resume_route(resume_id: int, current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**get_resume(current_user.id, resume_id))


@router.put('/{resume_id}', response_model=ResumeResponse)
def update_resume_route(resume_id: int, request: ResumeSaveRequest, current_user=Depends(get_current_user)) -> ResumeResponse:
    return ResumeResponse(**update_resume(current_user.id, resume_id, request.title, request.content))


@router.delete('/{resume_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_resume_route(resume_id: int, current_user=Depends(get_current_user)) -> Response:
    delete_resume(current_user.id, resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
