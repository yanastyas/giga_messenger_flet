# src/client/encryption.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config


class AESEncryption:
    """Класс для шифрования/дешифрования сообщений AES"""

    def __init__(self):
        self.backend = default_backend()
        password = config.ENCRYPTION_KEY  # Исправлено: config.ENCRYPTION_KEY
        self.salt = config.SALT
        self.iterations = 100000

        # Генерация ключа из пароля
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.iterations,
            backend=self.backend
        )
        self.key = kdf.derive(password.encode())

    def encrypt(self, message):
        """Шифрование сообщения"""
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CFB(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()

        # Шифруем сообщение
        if isinstance(message, str):
            message = message.encode('utf-8')

        encrypted = encryptor.update(message) + encryptor.finalize()

        # Возвращаем IV + зашифрованные данные в base64
        result = base64.b64encode(iv + encrypted).decode('utf-8')
        return result

    def decrypt(self, encrypted_message):
        """Дешифрование сообщения"""
        try:
            data = base64.b64decode(encrypted_message)
            iv = data[:16]
            encrypted = data[16:]

            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CFB(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted) + decryptor.finalize()

            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Ошибка дешифрования: {e}")
            return encrypted_message  # Возвращаем как есть в случае ошибки


# Эмодзи и реакции
EMOJIS = {
    '😊': '😊', '❤️': '❤️', '👍': '👍', '😂': '😂', '😮': '😮',
    '😢': '😢', '🔥': '🔥', '🎉': '🎉', '⭐': '⭐', '💯': '💯'
}


class ReactionManager:
    """Управление реакциями на сообщения"""

    def __init__(self):
        self.reactions = {}  # message_id: {user: reaction}

    def add_reaction(self, message_id, user, reaction):
        """Добавить реакцию на сообщение"""
        if message_id not in self.reactions:
            self.reactions[message_id] = {}
        self.reactions[message_id][user] = reaction

    def get_reactions(self, message_id):
        """Получить все реакции на сообщение"""
        return self.reactions.get(message_id, {})

    def remove_reaction(self, message_id, user):
        """Удалить реакцию пользователя"""
        if message_id in self.reactions and user in self.reactions[message_id]:
            del self.reactions[message_id][user]
            if not self.reactions[message_id]:
                del self.reactions[message_id]

    def get_reaction_counts(self, message_id):
        """Получить количество каждой реакции"""
        reactions = self.get_reactions(message_id)
        counts = {}
        for reaction in reactions.values():
            counts[reaction] = counts.get(reaction, 0) + 1
        return counts