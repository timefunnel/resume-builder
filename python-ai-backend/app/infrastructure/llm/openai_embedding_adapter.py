# author: jf
import json
import urllib.error
import urllib.request

from app.domain.exceptions.rag_exceptions import EmbeddingError


def _normalize_embedding_url(base_url: str | None) -> str:
    raw = (base_url or '').strip().rstrip('/')
    if not raw:
        return 'https://api.openai.com/v1/embeddings'
    if raw.endswith('/v1/embeddings'):
        return raw
    if raw.endswith('/embeddings'):
        return raw
    if raw.endswith('/v1'):
        return f'{raw}/embeddings'
    return f'{raw}/v1/embeddings'


class OpenAIEmbeddingAdapter:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.api_key = (api_key or '').strip()
        self.model_name = (model_name or '').strip() or 'text-embedding-3-small'
        self.base_url = (base_url or '').strip() or None
        self.endpoint = _normalize_embedding_url(base_url)
        self.timeout_seconds = self._normalize_timeout(timeout_seconds)
        self.provider_name = 'openai'

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        safe_texts = [text.strip() for text in texts if (text or '').strip()]
        if not safe_texts:
            _log_embedding('跳过调用，输入为空')
            return []
        if not self.api_key:
            raise EmbeddingError('OPENAI_API_KEY 未配置，无法生成 Embedding')

        payload = {
            'model': self.model_name,
            'input': safe_texts,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        _log_embedding(
            '开始调用 Embedding 接口',
            provider=self.provider_name,
            model=self.model_name,
            endpoint=self.endpoint,
            timeout_seconds=self.timeout_seconds,
            batch_size=len(safe_texts),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            raise EmbeddingError(
                f'OpenAI Embedding 调用失败（provider=openai, model={self.model_name}, timeout={self.timeout_seconds}s）：HTTP {exc.code}: {detail[:300]}'
            ) from exc
        except urllib.error.URLError as exc:
            raise EmbeddingError(
                f'OpenAI Embedding 调用失败（provider=openai, model={self.model_name}, timeout={self.timeout_seconds}s）：{exc.reason}'
            ) from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise EmbeddingError('Embedding 接口返回了非法 JSON') from exc
        data = parsed.get('data') if isinstance(parsed, dict) else None
        if not isinstance(data, list):
            raise EmbeddingError('Embedding 接口返回结构异常：缺少 data 列表')
        vectors: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict):
                raise EmbeddingError('Embedding 接口返回结构异常：data 项不是对象')
            embedding = item.get('embedding')
            if not isinstance(embedding, list) or not embedding:
                raise EmbeddingError('Embedding 接口返回结构异常：embedding 缺失')
            vectors.append(self._normalize_vector(embedding))
        if len(vectors) != len(safe_texts):
            raise EmbeddingError('Embedding 返回数量与输入数量不一致')
        return vectors

    @staticmethod
    def _normalize_timeout(raw_timeout: float) -> float:
        try:
            normalized = float(raw_timeout)
        except (TypeError, ValueError):
            return 45.0
        return max(1.0, normalized)

    @staticmethod
    def _normalize_vector(raw_vector: list[float]) -> list[float]:
        if not isinstance(raw_vector, list) or not raw_vector:
            raise EmbeddingError('Embedding 向量为空或格式非法')
        try:
            return [float(value) for value in raw_vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingError('Embedding 向量包含无法转换为 float 的值') from exc


def _log_embedding(message: str, **extra: object) -> None:
    parts = [f'[知识库上传][EmbeddingAdapter] {message}']
    for key, value in extra.items():
        parts.append(f'{key}={value}')
    print(' '.join(parts), flush=True)
