# app_config.py (в корне проекта)
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
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
    MAX_IMAGE_SIZE = (1920, 1080)

    # Аудио
    SAMPLE_RATE = 16000
    AUDIO_CHUNK = 1024
    MAX_RECORDING_SEC = 60

    # UI
    THEME = "dark"
    MESSAGES_PER_PAGE = 50

    # Пути
    DATABASE_PATH = DATABASE_DIR / "giga_messenger.db"
    TEMP_DIR = BASE_DIR / "temp"
    DOWNLOADS_DIR = Path.home() / "Downloads" / "GigaMessenger"

config = AppConfig()
config.TEMP_DIR.mkdir(exist_ok=True)
config.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)