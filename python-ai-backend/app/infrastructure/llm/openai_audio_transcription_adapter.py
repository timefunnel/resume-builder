import json
import mimetypes
import os
import uuid
import urllib.error
import urllib.request
from pathlib import Path


def _normalize_audio_transcription_url(base_url: str | None) -> str:
    raw = (base_url or '').strip().rstrip('/')
    if not raw:
        return 'https://api.openai.com/v1/audio/transcriptions'
    if raw.endswith('/v1/audio/transcriptions'):
        return raw
    if raw.endswith('/audio/transcriptions'):
        return raw
    if raw.endswith('/v1'):
        return f'{raw}/audio/transcriptions'
    return f'{raw}/v1/audio/transcriptions'


class OpenAIAudioTranscriptionAdapter:
    def __init__(self, api_key: str, model_name: str, base_url: str | None = None, timeout_seconds: float = 60.0) -> None:
        self.api_key = (api_key or '').strip()
        self.model_name = (model_name or '').strip() or 'FunAudioLLM/SenseVoiceSmall'
        self.endpoint = _normalize_audio_transcription_url(base_url)
        self.timeout_seconds = max(3.0, float(timeout_seconds or 60.0))

    def transcribe_file(self, file_path: str, mime_type: str | None = None, language: str = 'zh') -> str:
        if not self.api_key:
            raise RuntimeError('OPENAI_API_KEY is missing for audio transcription')
        path = Path(file_path)
        if not path.exists():
            raise RuntimeError(f'audio file not found: {file_path}')
        filename = path.name
        content_type = mime_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        file_bytes = path.read_bytes()
        boundary = f'----OpenClawFormBoundary{uuid.uuid4().hex}'
        body = self._build_multipart_body(boundary, filename, file_bytes, content_type, language)
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': f'multipart/form-data; boundary={boundary}',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'Audio transcription HTTP {exc.code}: {detail[:300]}') from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f'Audio transcription connection failed: {exc.reason}') from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError('Audio transcription returned invalid JSON') from exc
        text = parsed.get('text') if isinstance(parsed, dict) else ''
        return str(text or '').strip()

    def _build_multipart_body(self, boundary: str, filename: str, file_bytes: bytes, content_type: str, language: str) -> bytes:
        lines: list[bytes] = []

        def add_field(name: str, value: str) -> None:
            lines.extend([
                f'--{boundary}'.encode(),
                f'Content-Disposition: form-data; name="{name}"'.encode(),
                b'',
                value.encode('utf-8'),
            ])

        add_field('model', self.model_name)
        if language:
            add_field('language', language)

        lines.extend([
            f'--{boundary}'.encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
            f'Content-Type: {content_type}'.encode(),
            b'',
            file_bytes,
            f'--{boundary}--'.encode(),
            b'',
        ])
        return b'\r\n'.join(lines)
