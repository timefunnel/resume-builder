# author: jf
import json
from pathlib import Path

from app.bootstrap.container import build_chat_client, build_file_parser, build_image_markdown_ocr_client, resolve_settings
from app.domain.exceptions.rag_exceptions import FileParseError, UnsupportedFileTypeError
from app.domain.exceptions.resume_import_exceptions import ResumeImportError
from app.infrastructure.llm.openai_chat_adapter import OpenAIChatAdapter

_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
_DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx'}
_MAX_IMPORT_TEXT_CHARS = 6000


def _extract_text(file_name: str, content_type: str, file_bytes: bytes) -> str:
    extension = Path(file_name).suffix.lower()
    settings = resolve_settings()
    if extension in _IMAGE_EXTENSIONS:
        ocr = build_image_markdown_ocr_client(settings)
        return ocr.extract_markdown(image_bytes=file_bytes, file_name=file_name, content_type=content_type).strip()
    if extension in _DOCUMENT_EXTENSIONS:
        parser = build_file_parser(settings)
        extracted = parser.parse(file_bytes=file_bytes, file_name=file_name, content_type=content_type)
        return extracted.content.strip()
    raise UnsupportedFileTypeError(f'暂不支持的简历文件类型: {extension or content_type}')


def _normalize_import_text(text: str) -> str:
    safe = (text or '').strip()
    if len(safe) <= _MAX_IMPORT_TEXT_CHARS:
        return safe
    return safe[:_MAX_IMPORT_TEXT_CHARS].rstrip() + '\n\n[内容过长，以下部分已截断]'


def _build_prompt(extracted_text: str) -> str:
    return f"""
你是一个简历结构化助手。请根据下面的简历原文，提取信息并输出严格 JSON。

输出要求：
1. 只输出 JSON，不要输出解释、Markdown、代码块。
2. JSON 顶层结构必须是：
{{
  "title": "字符串",
  "content": {{
    "modules": [{{"key":"basicInfo","label":"基本信息","icon":"👤","visible":true}}, {{"key":"education","label":"教育经历","icon":"🎓","visible":true}}, {{"key":"skills","label":"专业技能","icon":"⚡","visible":true}}, {{"key":"workExperience","label":"工作经历","icon":"💼","visible":true}}, {{"key":"projectExperience","label":"项目经历","icon":"📁","visible":true}}, {{"key":"awards","label":"荣誉奖项","icon":"🏆","visible":false}}, {{"key":"selfIntro","label":"个人简介","icon":"📝","visible":false}}],
    "selectedTemplateKey": "default",
    "basicInfo": {{"name":"","phone":"","email":"","age":"","gender":"","location":"","jobTitle":"","educationLevel":"","avatar":"","workYears":"","currentStatus":"","expectedLocation":"","expectedSalary":"","website":"","wechat":"","currentCity":"","github":"","blog":""}},
    "educationList": [],
    "skills": "",
    "workList": [],
    "projectList": [],
    "awardList": [],
    "selfIntro": ""
  }}
}}
3. educationList 项目字段：id, school, college, major, degree, startDate, endDate, gpa, description, type, location。
4. workList 项目字段：id, company, department, position, startDate, endDate, location, description。
5. projectList 项目字段：id, name, role, startDate, endDate, link, introduction, mainWork。
6. awardList 项目字段：id, name, date, description。
7. 如果某字段缺失，填空字符串或空数组，不要省略字段。
8. id 用任意稳定字符串即可，例如 item_1、item_2。
9. title 优先取姓名 + “简历”，如果拿不到姓名，就用“导入的简历”。
10. description / introduction / mainWork 等富文本字段，输出纯文本即可。

简历原文如下：
---
{extracted_text}
---
""".strip()


def _build_import_chat_client():
    settings = resolve_settings()
    base_client = build_chat_client(settings)
    return OpenAIChatAdapter(
        model_name='gpt-5.4-mini',
        base_url=getattr(base_client, 'base_url', settings.openai_base_url),
        api_key=getattr(base_client, 'api_key', settings.openai_api_key),
        timeout_seconds=max(getattr(base_client, 'timeout_seconds', settings.openai_chat_timeout_seconds), 60.0),
    )


def import_resume_with_ai(file_name: str, content_type: str, file_bytes: bytes) -> dict:
    _log_import('import_started', file_name=file_name, content_type=content_type, size_bytes=len(file_bytes))
    if not file_bytes:
        raise FileParseError('上传文件不能为空')
    _log_import('extract_started', file_name=file_name)
    extracted_text = _extract_text(file_name=file_name, content_type=content_type, file_bytes=file_bytes)
    _log_import('extract_finished', file_name=file_name, extracted_chars=len(extracted_text))
    if not extracted_text:
        raise ResumeImportError('未能从简历中提取有效文本')
    normalized_text = _normalize_import_text(extracted_text)
    _log_import('normalize_finished', file_name=file_name, normalized_chars=len(normalized_text))
    client = _build_import_chat_client()
    _log_import('llm_started', file_name=file_name, model='gpt-5.4-mini')
    raw = client.chat(_build_prompt(normalized_text), system_prompt='你是严格输出 JSON 的简历结构化助手。')
    _log_import('llm_finished', file_name=file_name, response_chars=len(raw))
    try:
        payload = json.loads(raw)
        _log_import('json_parse_finished', file_name=file_name)
    except json.JSONDecodeError as exc:
        raise ResumeImportError(f'AI 返回了非 JSON 内容: {raw[:300]}') from exc
    if not isinstance(payload, dict) or not isinstance(payload.get('content'), dict):
        raise ResumeImportError('AI 返回的简历结构不合法')
    title = str(payload.get('title') or '导入的简历').strip() or '导入的简历'
    _log_import('import_finished', file_name=file_name, title=title)
    return {
        'title': title,
        'content': payload['content'],
        'extractedText': normalized_text,
    }


def _log_import(message: str, **extra: object) -> None:
    parts = [f"[resume-import][AI] {message}"]
    for key, value in extra.items():
        parts.append(f"{key}={value}")
    print(' '.join(parts), flush=True)
