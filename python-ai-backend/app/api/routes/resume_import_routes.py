# author: jf
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.deps.auth import get_current_user
from app.api.schemas.resume_import import ResumeImportAiResponse
from app.application.use_cases.resume_import_ai import import_resume_with_ai

router = APIRouter(prefix='/api/resumes', tags=['resume-import'])


@router.post('/import-ai', response_model=ResumeImportAiResponse)
async def import_resume_ai_route(file: UploadFile = File(...), current_user=Depends(get_current_user)) -> ResumeImportAiResponse:
    file_name = file.filename or 'resume.bin'
    content_type = file.content_type or 'application/octet-stream'
    data = await file.read()
    result = await run_in_threadpool(import_resume_with_ai, file_name, content_type, data)
    return ResumeImportAiResponse(**result)
