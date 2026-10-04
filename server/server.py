# server/server.py
import socket
import threading
import json
from datetime import datetime
from pathlib import Path
import sys

# Добавляем путь к корню проекта
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Импортируем конфиг
from app_config import config

# ⭐ Новый менеджер на PostgreSQL
from server.db_pg import UserManagerPG


class ChatServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}          # username: socket
        self.user_status = {}      # username: 'online'/'away'/'offline'
        self.user_manager = UserManagerPG()   # ← PostgreSQL

    def start(self):
        self.server.bind((config.SERVER_HOST, config.SERVER_PORT))
        self.server.listen(100)
        print(f"🚀 Сервер запущен на {config.SERVER_HOST}:{config.SERVER_PORT}")
        print("📦 База данных: PostgreSQL (Yandex Cloud)")

        while True:
            client, address = self.server.accept()
            print(f"📱 Подключение от {address}")
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def broadcast_status(self):
        """Отправить всем статусы пользователей"""
        status_msg = {
            'type': 'status_list',
            'users': self.user_status.copy()
        }
        for client in self.clients.values():
            try:
                client.send((json.dumps(status_msg) + '\n').encode())
            except:
                pass

    def broadcast(self, message, exclude=None):
        """Отправить сообщение всем (кроме exclude)"""
        for user, client in self.clients.items():
            if user != exclude:
                try:
                    client.send((json.dumps(message) + '\n').encode('utf-8'))
                except:
                    pass

    def handle_client(self, client):
        username = None
        buffer = ""
        try:
            # ===== АВТОРИЗАЦИЯ =====
            while '\n' not in buffer:
                chunk = client.recv(4096).decode('utf-8')
                if not chunk:
                    break
                buffer += chunk

            if not buffer:
                client.close()
                return

            line, buffer = buffer.split('\n', 1)
            auth_data = json.loads(line.strip())

            if auth_data['action'] == 'register':
                if self.user_manager.register_user(auth_data['username'], auth_data['password']):
                    username = auth_data['username']
                    response = {'type': 'auth', 'success': True, 'message': 'Регистрация успешна!'}
                else:
                    response = {'type': 'auth', 'success': False, 'message': 'Пользователь уже существует!'}
                    client.send((json.dumps(response) + '\n').encode())
                    client.close()
                    return

            elif auth_data['action'] == 'login':
                if self.user_manager.authenticate(auth_data['username'], auth_data['password']):
                    username = auth_data['username']
                    response = {'type': 'auth', 'success': True, 'message': 'Вход выполнен!'}
                else:
                    response = {'type': 'auth', 'success': False, 'message': 'Неверное имя или пароль!'}
                    client.send((json.dumps(response) + '\n').encode())
                    client.close()
                    return
            else:
                response = {'type': 'auth', 'success': False, 'message': 'Неизвестное действие!'}
                client.send((json.dumps(response) + '\n').encode())
                client.close()
                return

            # Отправляем ответ
            client.send((json.dumps(response) + '\n').encode())

            # ===== ЗАГРУЖАЕМ ИСТОРИЮ ЧАТА ИЗ БД =====
            try:
                history = self.user_manager.get_all_messages(limit=100)
                for msg in reversed(history):
                    history_data = {
                        'type': 'history_message',
                        'username': msg['sender_username'],
                        'message': msg['text'],
                        'timestamp': msg['timestamp']
                    }
                    try:
                        client.send((json.dumps(history_data) + '\n').encode('utf-8'))
                    except:
                        pass
                print(f"📜 Отправлено {len(history)} сообщений из истории для {username}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки истории: {e}")

            # Регистрируем клиента
            self.clients[username] = client
            self.user_status[username] = 'online'
            try:
                self.user_manager.update_last_seen(username)
            except Exception as e:
                print(f"⚠️ Не удалось обновить last_seen: {e}")

            # ===== ОФФЛАЙН-СООБЩЕНИЯ =====
            try:
                offline_msgs = self.user_manager.get_offline_messages(username)
                for msg in offline_msgs:
                    offline_data = {
                        'type': 'offline_message',
                        'from_user': msg['from_user'],
                        'message': msg['message'],
                        'timestamp': str(msg['timestamp']) if msg['timestamp'] else ''
                    }
                    try:
                        client.send((json.dumps(offline_data) + '\n').encode())
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Ошибка загрузки оффлайн-сообщений: {e}")

            # Оповещаем всех
            join_msg = {
                'type': 'system',
                'message': f"✨ {username} присоединился к чату!",
                'time': datetime.now().strftime("%H:%M")
            }
            self.broadcast(join_msg)
            self.broadcast_status()

            # ===== ОСНОВНОЙ ЦИКЛ =====
            while True:
                data = client.recv(65536).decode('utf-8')
                if not data:
                    break

                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            self.process_message(username, message, client)
                        except json.JSONDecodeError as e:
                            print(f"Ошибка парсинга JSON: {e}")
                            continue

        except ConnectionResetError:
            print(f"Соединение сброшено: {username}")
        except Exception as e:
            print(f"Ошибка в handle_client: {e}")
        finally:
            if username:
                if username in self.clients:
                    del self.clients[username]
                self.user_status[username] = 'offline'
                leave_msg = {
                    'type': 'system',
                    'message': f"👋 {username} покинул чат",
                    'time': datetime.now().strftime("%H:%M")
                }
                self.broadcast(leave_msg)
                self.broadcast_status()
                print(f"👋 {username} отключен")

            try:
                client.close()
            except:
                pass

    def process_message(self, username, message, client):
        """Обработка сообщений от клиента"""
        msg_type = message.get('type')

        if msg_type == 'message':
            target = message.get('target', 'all')
            text = message['message']

            # ⭐ СОХРАНЯЕМ В БД
            try:
                if target == 'all':
                    self.user_manager.save_message(username, None, text)
                else:
                    self.user_manager.save_message(username, target, text)
            except Exception as e:
                print(f"⚠️ Ошибка сохранения в БД: {e}")

            msg_data = {
                'type': 'message',
                'username': username,
                'message': text,
                'time': datetime.now().strftime("%H:%M"),
                'id': message.get('id', f"{username}_{datetime.now().timestamp()}")
            }

            if target == 'all':
                self.broadcast(msg_data)
            else:
                if target in self.clients:
                    try:
                        self.clients[target].send((json.dumps(msg_data) + '\n').encode('utf-8'))
                        msg_data['is_private'] = True
                        client.send((json.dumps(msg_data) + '\n').encode('utf-8'))
                    except:
                        pass
                else:
                    # Пользователь оффлайн — сохраняем
                    try:
                        self.user_manager.save_offline_message(target, username, text)
                    except Exception as e:
                        print(f"⚠️ Ошибка сохранения оффлайн-сообщения: {e}")

                    response = {
                        'type': 'system',
                        'message': f"💾 Сообщение для {target} сохранено (пользователь оффлайн)",
                        'time': datetime.now().strftime("%H:%M")
                    }
                    try:
                        client.send((json.dumps(response) + '\n').encode('utf-8'))
                    except:
                        pass

        elif msg_type == 'typing':
            typing_data = {
                'type': 'typing',
                'username': username,
                'is_typing': message['is_typing']
            }
            target = message.get('target', 'all')
            if target == 'all':
                self.broadcast(typing_data)
            elif target in self.clients:
                try:
                    self.clients[target].send((json.dumps(typing_data) + '\n').encode('utf-8'))
                except:
                    pass

        elif msg_type == 'file':
            target = message.get('target', 'all')
            file_data = {
                'type': 'file',
                'username': username,
                'filename': message['filename'],
                'data': message['data'],
                'file_type': message['file_type'],
                'time': datetime.now().strftime("%H:%M")
            }
            if target == 'all':
                self.broadcast(file_data)
            elif target in self.clients:
                try:
                    self.clients[target].send((json.dumps(file_data) + '\n').encode('utf-8'))
                except:
                    pass

        elif msg_type == 'status_update':
            self.user_status[username] = message['status']
            self.broadcast_status()


if __name__ == '__main__':
    server = ChatServer()
    server.start()