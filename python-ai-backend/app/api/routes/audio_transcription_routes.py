import os
import tempfile
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps.auth import get_current_user
from app.api.schemas.audio_transcription import (
    AudioTranscriptionChunkResponse,
    AudioTranscriptionFinalizeRequest,
    AudioTranscriptionFinalizeResponse,
)
from app.bootstrap.container import build_chat_client, resolve_settings
from app.infrastructure.llm.openai_audio_transcription_adapter import OpenAIAudioTranscriptionAdapter

router = APIRouter(prefix='/api/ai/audio/transcriptions', tags=['ai-audio-transcriptions'])


def _build_audio_transcriber() -> OpenAIAudioTranscriptionAdapter:
    settings = resolve_settings()
    return OpenAIAudioTranscriptionAdapter(
        api_key=settings.openai_audio_transcription_api_key,
        model_name=settings.openai_audio_transcription_model,
        base_url=settings.openai_audio_transcription_base_url,
        timeout_seconds=settings.openai_audio_transcription_timeout_seconds,
    )


@router.post('/chunk', response_model=AudioTranscriptionChunkResponse)
async def transcribe_chunk_route(
    sessionId: str = Form(...),
    chunkIndex: int = Form(...),
    durationMs: int | None = Form(default=None),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
) -> AudioTranscriptionChunkResponse:
    suffix = os.path.splitext(file.filename or '')[1] or '.webm'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp_path = temp.name
        content = await file.read()
        temp.write(content)
    try:
        transcriber = _build_audio_transcriber()
        text = transcriber.transcribe_file(temp_path, mime_type=file.content_type, language='zh')
        return AudioTranscriptionChunkResponse(
            sessionId=sessionId,
            chunkIndex=max(0, int(chunkIndex)),
            text=text,
            durationMs=durationMs,
            mimeType=file.content_type,
        )
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@router.post('/finalize', response_model=AudioTranscriptionFinalizeResponse)
def finalize_transcription_route(
    request: AudioTranscriptionFinalizeRequest,
    current_user=Depends(get_current_user),
) -> AudioTranscriptionFinalizeResponse:
    ordered = sorted(request.chunks, key=lambda item: item.chunkIndex)
    merged_text = '\n'.join(item.text.strip() for item in ordered if item.text.strip()).strip()
    if not merged_text:
        return AudioTranscriptionFinalizeResponse(sessionId=request.sessionId, text='', chunkCount=len(ordered))

    chat_client = build_chat_client()
    prompt = (
        '请整理下面的中文语音转写文本。要求：\n'
        '1. 保留原意，不要扩写，不要总结。\n'
        '2. 只做去重、断句、补标点、明显错别字修正。\n'
        '3. 删除重复片段和明显分片重叠。\n'
        '4. 输出纯文本。\n\n'
        f'原始转写：\n{merged_text}'
    )
    original_model = getattr(chat_client, 'model_name', '')
    if hasattr(chat_client, 'model_name'):
        chat_client.model_name = os.getenv('OPENAI_AUDIO_FINALIZE_MODEL', 'gpt-5.4-mini')
    try:
        normalized_text = chat_client.chat(prompt, system_prompt='你是语音转写整理助手。')
    finally:
        if hasattr(chat_client, 'model_name'):
            chat_client.model_name = original_model

    return AudioTranscriptionFinalizeResponse(
        sessionId=request.sessionId,
        text=(normalized_text or merged_text).strip(),
        chunkCount=len(ordered),
    )
