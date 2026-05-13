from __future__ import annotations

import json
from datetime import datetime, timezone

from app.infrastructure.persistence.mysql.session_repository import _parse_mysql_config, _safe_text


def _format_iso_datetime(value):
    if not isinstance(value, datetime):
        return None
    safe_value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return safe_value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class MySqlResumeRepository:
    def __init__(self, datasource_url: str, username: str = '', password: str = '') -> None:
        self._config = _parse_mysql_config(datasource_url, username, password)

    def _connect(self):
        import pymysql
        return pymysql.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.username,
            password=self._config.password,
            database=self._config.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def _row_to_detail(self, row: dict | None) -> dict | None:
        if not row:
            return None
        return {
            'id': int(row['id']),
            'title': _safe_text(row.get('title')) or '我的简历',
            'content': json.loads(row.get('content_json') or '{}'),
            'updatedAt': _format_iso_datetime(row.get('updated_at')),
        }

    def list_by_user_id(self, user_id: int) -> list[dict]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM resumes
                    WHERE user_id = %s AND is_deleted = 0
                    ORDER BY created_at DESC, id DESC
                    """,
                    (int(user_id),),
                )
                rows = cursor.fetchall()
                return [
                    {
                        'id': int(row['id']),
                        'title': _safe_text(row.get('title')) or '我的简历',
                        'updatedAt': _format_iso_datetime(row.get('updated_at')),
                    }
                    for row in rows
                ]
        finally:
            connection.close()

    def get_by_id(self, user_id: int, resume_id: int) -> dict | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, content_json, updated_at
                    FROM resumes
                    WHERE user_id = %s AND id = %s AND is_deleted = 0
                    LIMIT 1
                    """,
                    (int(user_id), int(resume_id)),
                )
                return self._row_to_detail(cursor.fetchone())
        finally:
            connection.close()

    def create(self, user_id: int, title: str, content: dict) -> dict:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO resumes (user_id, title, content_json, is_deleted) VALUES (%s, %s, %s, 0)",
                    (int(user_id), _safe_text(title) or '新的简历', json.dumps(content, ensure_ascii=False)),
                )
                resume_id = int(cursor.lastrowid)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.get_by_id(user_id, resume_id) or {'id': resume_id, 'title': _safe_text(title) or '新的简历', 'content': content, 'updatedAt': None}

    def update(self, user_id: int, resume_id: int, title: str, content: dict) -> dict | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE resumes SET title=%s, content_json=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND id=%s AND is_deleted=0",
                    (_safe_text(title) or '我的简历', json.dumps(content, ensure_ascii=False), int(user_id), int(resume_id)),
                )
                affected = cursor.rowcount
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        if not affected:
            return None
        return self.get_by_id(user_id, resume_id)

    def soft_delete(self, user_id: int, resume_id: int) -> bool:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE resumes SET is_deleted=1, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND id=%s AND is_deleted=0",
                    (int(user_id), int(resume_id)),
                )
                affected = cursor.rowcount
            connection.commit()
            return affected > 0
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_current(self, user_id: int) -> dict | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, content_json, updated_at
                    FROM resumes
                    WHERE user_id = %s AND is_deleted = 0
                    ORDER BY updated_at DESC, id DESC
                    LIMIT 1
                    """,
                    (int(user_id),),
                )
                return self._row_to_detail(cursor.fetchone())
        finally:
            connection.close()

    def save_current(self, user_id: int, title: str, content: dict) -> dict:
        current = self.get_current(user_id)
        if current:
            updated = self.update(user_id=user_id, resume_id=int(current['id']), title=title, content=content)
            if updated:
                return updated
        return self.create(user_id=user_id, title=title, content=content)
