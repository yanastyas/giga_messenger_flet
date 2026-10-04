# server/db_pg.py
"""
Модуль для работы с PostgreSQL (Yandex Cloud).
Заменяет sqlite3 из UserManager.
"""
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Подключение к PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 6432)),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="verify-full",
        sslrootcert=os.path.expanduser("~/.postgresql/root.crt"),
        connect_timeout=10,
    )


class UserManagerPG:
    """Менеджер пользователей и сообщений через PostgreSQL."""

    def __init__(self):
        self.conn = get_connection()
        self.conn.autocommit = True
        self._ensure_tables()

    def _ensure_tables(self):
        """Создаём таблицы, если их ещё нет."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    display_name VARCHAR(100),
                    avatar_url TEXT,
                    role VARCHAR(50) DEFAULT 'member',
                    status VARCHAR(20) DEFAULT 'active',
                    block_until BIGINT DEFAULT 0,
                    created_at BIGINT NOT NULL,
                    last_seen BIGINT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    sender_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    sender_username VARCHAR(100) NOT NULL,
                    receiver_username VARCHAR(100),
                    text TEXT,
                    media_url TEXT,
                    media_type VARCHAR(20),
                    timestamp BIGINT NOT NULL,
                    type VARCHAR(20) DEFAULT 'text'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS offline_messages (
                    id BIGSERIAL PRIMARY KEY,
                    to_user VARCHAR(100) NOT NULL,
                    from_user VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp BIGINT NOT NULL
                )
            """)

    # ===== Пользователи =====

    def register_user(self, username, password):
        """Регистрация нового пользователя."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, created_at, last_seen)
                    VALUES (%s, %s, %s, %s)
                """, (username, password_hash, int(datetime.now().timestamp()),
                      int(datetime.now().timestamp())))
            return True
        except psycopg2.IntegrityError:
            return False

    def authenticate(self, username, password):
        """Проверка логина и пароля."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE username = %s AND password_hash = %s",
                (username, password_hash)
            )
            return cur.fetchone() is not None

    def update_last_seen(self, username):
        """Обновить время последнего входа."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_seen = %s WHERE username = %s",
                (int(datetime.now().timestamp()), username)
            )

    def get_user_by_username(self, username):
        """Получить данные пользователя."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cur.fetchone()

    # ===== Сообщения =====

    def save_message(self, sender_username, receiver_username, text):
        """Сохранить сообщение в БД."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (sender_username, receiver_username, text, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (sender_username, receiver_username, text,
                  int(datetime.now().timestamp())))

    def get_chat_history(self, user1, user2, limit=100):
        """Получить историю чата между двумя пользователями."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT sender_username, text, timestamp
                FROM messages
                WHERE (sender_username = %s AND receiver_username = %s)
                   OR (sender_username = %s AND receiver_username = %s)
                ORDER BY timestamp DESC
                LIMIT %s
            """, (user1, user2, user2, user1, limit))
            return [dict(row) for row in cur.fetchall()]

    def get_all_messages(self, limit=200):
        """Получить последние сообщения общего чата."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT sender_username, text, timestamp
                FROM messages
                WHERE receiver_username IS NULL OR receiver_username = 'all'
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    # ===== Оффлайн-сообщения =====

    def save_offline_message(self, to_user, from_user, message):
        """Сохранить оффлайн-сообщение."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO offline_messages (to_user, from_user, message, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (to_user, from_user, message, int(datetime.now().timestamp())))

    def get_offline_messages(self, username):
        """Получить и удалить оффлайн-сообщения."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT from_user, message, timestamp
                FROM offline_messages
                WHERE to_user = %s
                ORDER BY timestamp
            """, (username,))
            messages = [dict(row) for row in cur.fetchall()]
            cur.execute("DELETE FROM offline_messages WHERE to_user = %s", (username,))
            return messages

    def close(self):
        """Закрыть соединение."""
        if self.conn:
            self.conn.close()