# src/client/socket_client.py
import socket
import json
import threading
import hashlib
import time
from datetime import datetime
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import config


class SocketClient:
    """Клиент для работы с сервером мессенджера"""

    def __init__(self, host=None, port=None):
        self.host = host or config.SERVER_HOST
        self.port = port or config.SERVER_PORT
        self.socket = None
        self.username = None
        self.connected = False
        self.callback = None
        self.receive_thread = None
        self.is_running = False
        self.buffer = ""

    def connect(self, username, password, action='login'):
        """
        Подключение к серверу

        Args:
            username: Имя пользователя
            password: Пароль
            action: 'login' или 'register'

        Returns:
            bool: Успешно ли подключение
        """
        try:
            print(f"🔌 Подключение к {self.host}:{self.port}")

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))

            # Отправляем данные авторизации
            auth_data = {
                'action': action,
                'username': username,
                'password': hashlib.sha256(password.encode()).hexdigest()
            }
            self.socket.send((json.dumps(auth_data) + '\n').encode('utf-8'))

            # Получаем ответ
            self.socket.settimeout(5)
            response = self._receive_message()

            if response and response.get('success'):
                self.username = username
                self.connected = True
                self.is_running = True
                self.socket.settimeout(None)
                print(f"✅ Подключено как {username}")
                return True
            else:
                error_msg = response.get('message', 'Неизвестная ошибка')
                print(f"❌ Ошибка: {error_msg}")
                return False

        except socket.timeout:
            print("❌ Таймаут подключения")
            return False
        except ConnectionRefusedError:
            print("❌ Сервер не найден. Проверьте IP и порт.")
            return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def _receive_message(self, timeout=None):
        """Получить одно сообщение от сервера"""
        try:
            if timeout:
                self.socket.settimeout(timeout)

            buffer = ""
            while '\n' not in buffer:
                chunk = self.socket.recv(4096).decode('utf-8')
                if not chunk:
                    return None
                buffer += chunk

            line, self.buffer = buffer.split('\n', 1)
            return json.loads(line.strip())

        except socket.timeout:
            return None
        except Exception as e:
            print(f"Ошибка приема: {e}")
            return None

    def start_receiving(self, callback):
        """
        Запустить поток приема сообщений

        Args:
            callback: Функция для обработки полученных сообщений
        """
        self.callback = callback
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        print("📨 Поток приема запущен")

    def _receive_loop(self):
        """Основной цикл приема сообщений"""
        buffer = ""
        while self.is_running and self.connected:
            try:
                data = self.socket.recv(65536).decode('utf-8')
                if not data:
                    print("Соединение закрыто сервером")
                    break

                buffer += data

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            if self.callback:
                                self.callback(message)
                        except json.JSONDecodeError as e:
                            print(f"Ошибка парсинга JSON: {e}")
                            continue

            except socket.error as e:
                print(f"Ошибка сокета: {e}")
                break
            except Exception as e:
                print(f"Ошибка приема: {e}")
                break

        self.connected = False
        self.is_running = False
        print("📨 Поток приема остановлен")

    def send_message(self, message, target='all'):
        """
        Отправить сообщение

        Args:
            message: Текст сообщения
            target: Получатель ('all' или имя пользователя)
        """
        if not self.connected:
            print("❌ Не подключено к серверу")
            return False

        msg_data = {
            'type': 'message',
            'message': message,
            'target': target,
            'timestamp': datetime.now().timestamp()
        }

        try:
            self.socket.send((json.dumps(msg_data) + '\n').encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.connected = False
            return False

    def send_typing(self, is_typing, target='all'):
        """Отправить статус печатает"""
        if not self.connected:
            return

        typing_data = {
            'type': 'typing',
            'is_typing': is_typing,
            'target': target
        }

        try:
            self.socket.send((json.dumps(typing_data) + '\n').encode('utf-8'))
        except:
            pass

    def send_status(self, status='online'):
        """Отправить статус пользователя"""
        if not self.connected:
            return

        status_data = {
            'type': 'status_update',
            'status': status
        }

        try:
            self.socket.send((json.dumps(status_data) + '\n').encode('utf-8'))
        except:
            pass

    def send_file(self, file_data, target):
        """Отправить файл"""
        if not self.connected:
            return False

        file_info = {
            'type': 'file',
            'target': target,
            **file_data
        }

        try:
            self.socket.send((json.dumps(file_info) + '\n').encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки файла: {e}")
            return False

    def disconnect(self):
        """Отключиться от сервера"""
        print("🔌 Отключение...")
        self.is_running = False
        self.connected = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        if self.receive_thread:
            try:
                self.receive_thread.join(timeout=1)
            except:
                pass

        print("✅ Отключено")

    def is_connected(self):
        """Проверить подключение"""
        return self.connected and self.socket is not None

    def get_username(self):
        """Получить имя пользователя"""
        return self.username