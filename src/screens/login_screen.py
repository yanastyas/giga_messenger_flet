# src/screens/login_screen.py
import flet as ft
from src.config import config


class LoginScreen:
    def __init__(self, app):
        self.app = app
        self.username_input = None
        self.password_input = None
        self.server_input = None
        self.status_label = None
        self.is_connecting = False

    def build(self):
        return ft.Container(
            expand=True,
            bgcolor="#0D47A1",
            content=ft.Column(
                controls=[
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            ft.Text("💬 GigaMessenger", size=45, weight=ft.FontWeight.BOLD, color="#FFFFFF")
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Text("Безопасный мессенджер", size=16, color="#9E9E9E"),
                    ft.Container(height=30),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._build_text_field("Имя пользователя"),
                                self._build_text_field("Пароль", password=True),
                                self._build_text_field("IP сервера", value=config.SERVER_HOST),
                            ],
                            spacing=15,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=10
                    ),
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Button(
                                    "Вход",
                                    width=300,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        bgcolor="#2196F3",
                                        color="#FFFFFF"
                                    ),
                                    on_click=self.on_login
                                ),
                                ft.OutlinedButton(
                                    "Регистрация",
                                    width=300,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        color="#FFFFFF"
                                    ),
                                    on_click=self.on_register
                                ),
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=10
                    ),
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Column(
                            controls=[self._build_status_label()],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=10
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            )
        )

    def _build_text_field(self, hint, password=False, value=""):
        field = ft.TextField(
            hint_text=hint,
            border_color="#2196F3",
            focused_border_color="#64B5F6",
            width=300,
            height=50,
            password=password,
            can_reveal_password=password,
            value=value,
            text_style=ft.TextStyle(color="#FFFFFF")
        )
        if hint == "Имя пользователя":
            self.username_input = field
        elif hint == "Пароль":
            self.password_input = field
        elif hint == "IP сервера":
            self.server_input = field
        return field

    def _build_status_label(self):
        self.status_label = ft.Text("", color="#EF5350", size=14)
        return self.status_label

    def on_login(self, e):
        if not self.is_connecting:
            self.is_connecting = True
            self._authenticate('login')

    def on_register(self, e):
        if not self.is_connecting:
            self.is_connecting = True
            self._authenticate('register')

    def _authenticate(self, action):
        username = self.username_input.value.strip()
        password = self.password_input.value.strip()
        server_ip = self.server_input.value.strip() or config.SERVER_HOST

        if not username or not password:
            self.status_label.value = "❌ Заполните все поля!"
            self.status_label.color = "#EF5350"
            self.status_label.update()
            self.is_connecting = False
            return

        if self.app.connect_to_server(username, password, server_ip, action):
            self.app.show_chat()
        else:
            self.status_label.value = "❌ Ошибка подключения!"
            self.status_label.color = "#EF5350"
            self.status_label.update()
            self.is_connecting = False