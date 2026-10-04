# src/app.py
import flet as ft
import socket
import json
import threading
import hashlib
from datetime import datetime

from src.config import config
from src.screens.login_screen import LoginScreen


class GigaMessengerApp:
    def __init__(self):
        self.client_socket = None
        self.username = None
        self.receive_thread = None
        self.connected = False
        self.users_status = {}
        self.message_counter = 0
        self.processed_messages = set()
        self.chat_screen = None
        self.login_screen = None
        self.page = None
        self.messages_list = None
        self.message_input = None
        self.online_label = None
        self.main_column = None

    def run(self, page: ft.Page):
        self.page = page
        page.title = config.APP_TITLE
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.bgcolor = "#0f0f1a"
        page.window.width = config.WINDOW_WIDTH
        page.window.height = config.WINDOW_HEIGHT
        page.window.resizable = False
        self.show_login()

    def show_login(self):
        self.login_screen = LoginScreen(self)
        self.page.controls.clear()
        self.page.add(self.login_screen.build())
        self.page.update()

    def show_chat(self):
        print("Показываем экран чата")

        # Очищаем страницу при переходе на чат
        self.page.controls.clear()

        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        self.online_label = ft.Text("🟢 Онлайн: 0", color="#9E9E9E", size=14)

        top_row = ft.Row(
            controls=[
                ft.TextButton("Выйти", on_click=lambda e: self.logout()),
                ft.Text(f"💬 {self.username}", size=18,
                        weight=ft.FontWeight.BOLD, color="white"),
                self.online_label,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        top_bar = ft.Container(
            content=top_row,
            bgcolor="#0D47A1",
            height=60,
            padding=10,
        )

        # ===== ОБЛАСТЬ СООБЩЕНИЙ — используем ListView =====
        self.messages_list = ft.ListView(
            spacing=8,
            padding=10,
            expand=True,
            auto_scroll=True,
        )

        messages_container = ft.Container(
            content=self.messages_list,
            expand=True,
            bgcolor="#0f0f1a",
        )

        # ===== ПАНЕЛЬ ВВОДА =====
        self.message_input = ft.TextField(
            hint_text="Введите сообщение...",
            expand=True,
            border_radius=10,
            text_style=ft.TextStyle(color="white"),
            bgcolor="#1a1a2e",
            border_color="#424242",
            focused_border_color="#2196F3",
            on_submit=self.send_message_handler,
        )

        send_btn = ft.Button(
            "📤",
            style=ft.ButtonStyle(
                color="white",
                bgcolor="#2196F3",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.send_message_handler,
        )

        input_row = ft.Row(
            controls=[self.message_input, send_btn],
            spacing=5,
        )

        input_container = ft.Container(
            content=input_row,
            padding=10,
            bgcolor="#1a1a2e",
        )

        # ===== СОБИРАЕМ ВСЁ В COLUMN =====
        self.main_column = ft.Column(
            controls=[
                top_bar,
                messages_container,
                input_container,
            ],
            expand=True,
            spacing=0,
        )

        # ===== ДОБАВЛЯЕМ НА СТРАНИЦУ =====
        self.page.add(self.main_column)
        self.page.update()

        # ===== ПРИВЕТСТВИЕ =====
        self.add_system_message("Добро пожаловать в чат!")

    def send_message_handler(self, e):
        text = self.message_input.value
        if text and text.strip():
            # Только отправляем на сервер.
            # Локально НЕ добавляем — сервер вернёт его обратно,
            # и оно добавится через process_message.
            self.send_message(text)
            self.message_input.value = ""
            self.message_input.update()

    def _safe_update(self, callback):
        """Безопасно выполняет обновление UI из любого потока."""
        try:
            callback()
        except Exception as e:
            print(f"❌ Ошибка обновления UI: {e}")

    def add_my_message(self, text, time):
        print(f"add_my_message: {text}")
        if self.messages_list is None:
            return

        bubble = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(text, size=14, color="white"),
                    ft.Text(time, size=10, color="#B0BEC5"),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor="#1E88E5",
            border_radius=10,
            padding=ft.padding.all(10),
            margin=ft.margin.only(left=50),
            width=250,
        )
        container = ft.Row(
            controls=[ft.Container(expand=True), bubble],
            alignment=ft.MainAxisAlignment.END,
        )

        def _do():
            self.messages_list.controls.append(container)
            self.page.update()
            print(f"Сообщений в списке: {len(self.messages_list.controls)}")

        self._safe_update(_do)

    def add_other_message(self, username, text, time):
        print(f"add_other_message: {username} - {text}")
        if self.messages_list is None:
            return

        bubble = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(username, size=12,
                            weight=ft.FontWeight.BOLD, color="#64B5F6"),
                    ft.Text(text, size=14, color="white"),
                    ft.Text(time, size=10, color="#B0BEC5"),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor="#2C2C3E",
            border_radius=10,
            padding=ft.padding.all(10),
            margin=ft.margin.only(right=50),
            width=250,
        )
        container = ft.Row(
            controls=[bubble, ft.Container(expand=True)],
            alignment=ft.MainAxisAlignment.START,
        )

        def _do():
            self.messages_list.controls.append(container)
            self.page.update()
            print(f"Сообщений в списке: {len(self.messages_list.controls)}")

        self._safe_update(_do)

    def add_system_message(self, text):
        print(f"add_system_message: {text}")
        if self.messages_list is None:
            return

        msg = ft.Row(
            controls=[
                ft.Text(
                    f"📢 {text}",
                    size=12,
                    color="#9E9E9E",
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        def _do():
            self.messages_list.controls.append(msg)
            self.page.update()

        self._safe_update(_do)

    def connect_to_server(self, username, password, server_ip, action='login'):
        try:
            print(f"Подключение к {server_ip}:{config.SERVER_PORT}")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((server_ip, config.SERVER_PORT))

            auth_data = json.dumps({
                'action': action,
                'username': username,
                'password': hashlib.sha256(password.encode()).hexdigest()
            })
            self.client_socket.send((auth_data + '\n').encode())

            self.client_socket.settimeout(5)
            buffer = ""
            while True:
                try:
                    chunk = self.client_socket.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk
                    if '\n' in buffer:
                        break
                except socket.timeout:
                    break

            lines = buffer.split('\n')
            first_line = lines[0].strip()
            if not first_line:
                self.client_socket.close()
                return False

            try:
                response = json.loads(first_line)
            except json.JSONDecodeError:
                self.client_socket.close()
                return False

            if response.get('success'):
                self.username = username
                self.connected = True
                self.client_socket.settimeout(None)
                self.start_receiving()
                return True
            else:
                self.client_socket.close()
                return False

        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def start_receiving(self):
        def receive():
            buffer = ""
            while self.connected:
                try:
                    data = self.client_socket.recv(65536).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            try:
                                message = json.loads(line)
                                self.process_message(message)
                            except json.JSONDecodeError:
                                continue
                except:
                    break
            self.connected = False

        self.receive_thread = threading.Thread(target=receive, daemon=True)
        self.receive_thread.start()

    def send_message(self, text, target='all'):
        if not self.connected:
            return
        self.message_counter += 1
        message_id = f"{self.username}_{self.message_counter}_{datetime.now().timestamp()}"
        message = {
            'type': 'message',
            'message': text,
            'target': target,
            'id': message_id,
            'timestamp': datetime.now().timestamp()
        }
        try:
            self.client_socket.send((json.dumps(message) + '\n').encode('utf-8'))
            print(f"Сообщение отправлено: {text}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def send_typing_status(self, is_typing, target='all'):
        if self.connected:
            typing_msg = {
                'type': 'typing',
                'is_typing': is_typing,
                'target': target,
                'username': self.username
            }
            try:
                self.client_socket.send((json.dumps(typing_msg) + '\n').encode())
            except:
                pass

    def process_message(self, message):
        msg_type = message.get('type')
        print(f"Получено сообщение типа: {msg_type}")

        # Дедупликация по id
        if 'id' in message:
            msg_key = message['id']
            if msg_key in self.processed_messages:
                print(f"Сообщение уже обработано: {msg_key}")
                return
            self.processed_messages.add(msg_key)
            if len(self.processed_messages) > 1000:
                self.processed_messages.clear()

        if msg_type == 'message':
            username = message.get('username', '')
            print(f"Обработка сообщения от {username}")

            if self.messages_list is not None:
                if username == self.username:
                    print("Это свое сообщение - показываем")
                    self.add_my_message(
                        message.get('message', ''),
                        message.get('time', datetime.now().strftime("%H:%M"))
                    )
                else:
                    print(f"Это чужое сообщение от {username}")
                    self.add_other_message(
                        username,
                        message.get('message', ''),
                        message.get('time', datetime.now().strftime("%H:%M"))
                    )
            else:
                print("ОШИБКА: messages_list is None!")

        elif msg_type == 'history_message':
            # ⭐ Сообщение из истории (загружено из БД)
            username = message.get('username', '')
            if self.messages_list is not None:
                time_str = datetime.fromtimestamp(
                    message.get('timestamp', 0)
                ).strftime("%H:%M")
                if username == self.username:
                    self.add_my_message(message.get('message', ''), time_str)
                else:
                    self.add_other_message(username, message.get('message', ''), time_str)

        elif msg_type == 'system':
            if self.messages_list is not None:
                self.add_system_message(message.get('message', ''))

        elif msg_type == 'typing':
            if message.get('is_typing') and message.get('username') != self.username:
                pass

        elif msg_type == 'status_list':
            self.users_status = message.get('users', {})
            if self.online_label:
                online = sum(1 for s in self.users_status.values() if s == 'online')
                self.online_label.value = f"🟢 Онлайн: {online}"
                try:
                    self.online_label.update()
                except:
                    pass

    def logout(self):
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.username = None
        self.show_login()

    def get_username(self):
        return self.username