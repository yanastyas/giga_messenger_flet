# src/db.py
"""
Модуль подключения к PostgreSQL (Yandex Cloud).
Использует SSL-сертификат для безопасного подключения.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()


def get_connection():
    """
    Возвращает новое подключение к PostgreSQL.
    Использует verify-full и корневой сертификат Yandex Cloud.
    """
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


def execute_query(query, params=None, fetch=False):
    """
    Универсальная функция выполнения SQL-запроса.

    :param query: SQL-запрос
    :param params: параметры (tuple или dict)
    :param fetch: True — вернуть результат SELECT
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                return [dict(row) for row in result]
            conn.commit()
            return cur.rowcount
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def test_connection():
    """Проверка подключения к базе данных."""
    print("🔍 Проверка подключения к PostgreSQL...")
    print(f"   Хост: {os.getenv('DB_HOST')}")
    print(f"   Порт: {os.getenv('DB_PORT')}")
    print(f"   База: {os.getenv('DB_NAME')}")
    print(f"   Пользователь: {os.getenv('DB_USER')}")
    print(f"   SSL-сертификат: {os.path.expanduser('~/.postgresql/root.crt')}")
    print()
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
        conn.close()
        print("✅ Подключение к PostgreSQL успешно!")
        print(f"   Версия сервера: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


if __name__ == "__main__":
    test_connection()