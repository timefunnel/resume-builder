from __future__ import generator_stop

from app.domain.models.user import User
from app.infrastructure.persistence.mysql.session_repository import _parse_mysql_config, _safe_text


class MySqlUserRepository:
    def __init__(self, datasource_url: str, username: str = "", password: str = "") -> None:
        self._config = _parse_mysql_config(datasource_url, username, password)

    def _connect(self):
        import pymysql

        return pymysql.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.username,
            password=self._config.password,
            database=self._config.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def create_user(self, *, email: str, password_hash: str, nickname: str | None = None) -> User:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, nickname, status)
                    VALUES (%s, %s, %s, 'active')
                    """,
                    (_safe_text(email).lower(), password_hash, _safe_text(nickname) or None),
                )
                user_id = int(cursor.lastrowid)
            connection.commit()
            return User(id=user_id, email=_safe_text(email).lower(), nickname=_safe_text(nickname) or None, status="active")
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def find_password_record_by_email(self, email: str) -> dict | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, password_hash, nickname, status FROM users WHERE email = %s LIMIT 1",
                    (_safe_text(email).lower(),),
                )
                return cursor.fetchone()
        finally:
            connection.close()

    def find_by_id(self, user_id: int) -> User | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, nickname, status FROM users WHERE id = %s LIMIT 1",
                    (int(user_id),),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return User(
                    id=int(row["id"]),
                    email=_safe_text(row.get("email")).lower(),
                    nickname=_safe_text(row.get("nickname")) or None,
                    status=_safe_text(row.get("status")) or "active",
                )
        finally:
            connection.close()
