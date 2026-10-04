# src/init_db.py
"""
Создание таблиц в PostgreSQL для GigaMessenger.
Запускать один раз: python -m src.init_db
"""
import sys
import os

# Добавляем корень проекта в путь, чтобы импорт src.db работал
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import execute_query


TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'member',
    status VARCHAR(20) DEFAULT 'active',
    block_until BIGINT DEFAULT 0,
    created_at BIGINT NOT NULL
    last_seen BIGINT
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    sender_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    text TEXT,
    media_url TEXT,
    media_type VARCHAR(20),
    timestamp BIGINT NOT NULL,
    type VARCHAR(20) DEFAULT 'text'
);

CREATE TABLE IF NOT EXISTS info_posts (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    timestamp BIGINT NOT NULL,
    updated_at BIGINT
);

CREATE TABLE IF NOT EXISTS appeals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounting_requests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    note TEXT,
    created_at BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_info_posts_timestamp ON info_posts(timestamp DESC);
"""


def init_db():
    print("🔨 Создание таблиц...")
    try:
        for statement in TABLES_SQL.split(";"):
            stmt = statement.strip()
            if stmt:
                execute_query(stmt)
        print("✅ Все таблицы созданы!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    init_db()