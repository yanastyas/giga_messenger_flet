# src/config.py
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

class AppConfig:
    # Сервер
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT = 8888
    FILE_TRANSFER_PORT = 8889

    # Безопасность
    ENCRYPTION_KEY = "GigaMessenger2024SecretKey!!"
    SALT = b'giga_salt_2024'

    # Ограничения
    MAX_MESSAGE_LENGTH = 5000
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # UI
    APP_TITLE = "GigaMessenger"
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 700

    # Пути
    DATABASE_PATH = DATABASE_DIR / "giga_messenger.db"
    TEMP_DIR = BASE_DIR / "temp"

config = AppConfig()
config.TEMP_DIR.mkdir(exist_ok=True)