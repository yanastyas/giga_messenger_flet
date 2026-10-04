# src/client/file_handler.py
import os
import base64
import io
import sys
from pathlib import Path
from PIL import Image

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config


class FileTransfer:
    """Класс для передачи файлов и изображений"""

    def __init__(self, callback=None):
        self.callback = callback
        self.file_port = config.FILE_TRANSFER_PORT
        self.downloads_dir = config.DOWNLOADS_DIR

        # Создаем папку для загрузок
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def send_file(self, file_path, target_user, host='127.0.0.1'):
        """Отправить файл"""
        if not os.path.exists(file_path):
            print(f"Файл не найден: {file_path}")
            return False

        # Определяем тип файла
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            file_type = 'image'
            data = self.compress_image(file_path)
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            file_type = 'audio'
            with open(file_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            file_type = 'video'
            with open(file_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
        else:
            file_type = 'file'
            with open(file_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')

        file_info = {
            'type': 'file_transfer',
            'file_type': file_type,
            'filename': os.path.basename(file_path),
            'data': data,
            'target': target_user,
            'size': os.path.getsize(file_path)
        }

        # Отправляем через callback
        if self.callback:
            self.callback(file_info)
            return True

        return False

    def compress_image(self, image_path, max_size=(800, 800)):
        """Сжать изображение"""
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Сохраняем в буфер
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)

                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Ошибка сжатия изображения: {e}")
            # Если не удалось сжать, отправляем как есть
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')

    def receive_file(self, file_data):
        """Получить файл и сохранить"""
        try:
            filename = file_data['filename']
            data = base64.b64decode(file_data['data'])

            # Сохраняем в папку Downloads
            save_path = self.downloads_dir / filename

            # Если файл с таким именем существует, добавляем суффикс
            counter = 1
            while save_path.exists():
                name, ext = os.path.splitext(filename)
                new_name = f"{name}_{counter}{ext}"
                save_path = self.downloads_dir / new_name
                counter += 1

            with open(save_path, 'wb') as f:
                f.write(data)

            print(f"✅ Файл сохранен: {save_path}")
            return str(save_path)

        except Exception as e:
            print(f"❌ Ошибка сохранения файла: {e}")
            return None

    def get_file_preview(self, file_path):
        """Получить превью файла (для изображений)"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            try:
                with Image.open(file_path) as img:
                    # Создаем превью 200x200
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    return base64.b64encode(buffer.getvalue()).decode('utf-8')
            except:
                return None
        return None

    def get_file_icon(self, file_path):
        """Получить иконку для файла по расширению"""
        ext = os.path.splitext(file_path)[1].lower()

        icons = {
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.pdf': '📄', '.doc': '📄', '.docx': '📄',
            '.txt': '📝', '.zip': '📦', '.rar': '📦'
        }

        return icons.get(ext, '📎')

    def get_file_size_str(self, size_bytes):
        """Получить строковое представление размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"