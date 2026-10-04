# src/screens/chat_screen.py
import flet as ft
from datetime import datetime
import threading


class ChatScreen:
    def __init__(self, app):
        self.app = app
        self.message_input = None
        self.messages_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.typing_label = None
        self.online_label = None
        self.is_typing = False
        self.typing_timer = None
        self._built = False  # защита от повторного билда

    def build(self):
        # Если уже строили — просто возвращаем, чтобы не терять сообщения
        if self._built:
            return

        page = self.app.page

        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        self.online_label = ft.Text("🟢 Онлайн: 0", color="#9E9E9E", size=14)

        top_row = ft.Row(
            controls=[
                ft.TextButton("Выйти", on_click=self.on_logout),
                ft.Text(f"💬 {self.app.get_username()}", size=18, weight=ft.FontWeight.BOLD, color="white"),
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

        # ===== ОБЛАСТЬ СООБЩЕНИЙ =====
        self.messages_list = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,          # ⭐ ДОБАВЛЕНО
            auto_scroll=True,     # ⭐ ДОБАВЛЕНО (для авто-прокрутки)
        )
        messages_container = ft.Container(
            content=self.messages_list,
            expand=True,
            padding=10,
            bgcolor="#0f0f1a",
            alignment=ft.alignment.top_left,   # ⭐ ДОБАВЛЕНО
        )

        # ===== СТАТУС ПЕЧАТАЕТ =====
        self.typing_label = ft.Text("", color="#9E9E9E", size=12, italic=True)
        typing_container = ft.Container(
            content=self.typing_label,
            padding=(15, 0, 0, 5),
            bgcolor="#0f0f1a",
            height=30,
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
            on_submit=self.send_message,
        )

        send_btn = ft.Button(
            "📤",
            style=ft.ButtonStyle(
                color="white",
                bgcolor="#2196F3",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.send_message,
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

        # ===== СОБИРАЕМ ВСЁ =====
        main_column = ft.Column(
            controls=[
                top_bar,
                messages_container,
                typing_container,
                input_container,
            ],
            expand=True,
            spacing=0,
        )

        # ⭐ ВАЖНО: НЕ очищаем всю страницу, просто добавляем колонку
        page.add(main_column)
        page.update()

        self._built = True
        return main_column

    def add_message(self, username, text, time, is_own=False):
        """Добавить сообщение в чат"""
        if is_own:
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
                padding=(12, 8, 12, 8),
                margin=(50, 0, 0, 0),
                width=250,
            )
            container = ft.Row(
                controls=[ft.Container(expand=True), bubble],
                alignment=ft.MainAxisAlignment.END,
            )
        else:
            bubble = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(username, size=12, weight=ft.FontWeight.BOLD, color="#64B5F6"),
                        ft.Text(text, size=14, color="white"),
                        ft.Text(time, size=10, color="#B0BEC5"),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor="#2C2C3E",
                border_radius=10,
                padding=(12, 8, 12, 8),
                margin=(0, 0, 50, 0),
                width=250,
            )
            container = ft.Row(
                controls=[bubble, ft.Container(expand=True)],
                alignment=ft.MainAxisAlignment.START,
            )

        self.messages_list.controls.append(container)
        self.messages_list.update()
        try:
            self.messages_list.scroll_to(offset=-1, duration=300)
        except:
            pass

    def add_system_message(self, text, time=""):
        """Добавить системное сообщение"""
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
        self.messages_list.controls.append(msg)
        self.messages_list.update()

    def show_typing(self, username):
        self.typing_label.value = f"{username} печатает..."
        self.typing_label.update()
        if self.typing_timer:
            self.typing_timer.cancel()
        self.typing_timer = threading.Timer(3.0, self.hide_typing)
        self.typing_timer.daemon = True
        self.typing_timer.start()

    def hide_typing(self):
        self.typing_label.value = ""
        self.typing_label.update()

    def update_online_count(self, count):
        self.online_label.value = f"🟢 Онлайн: {count}"
        self.online_label.update()

    def send_message(self, e):
        text = self.message_input.value
        if text and text.strip():
            self.app.send_message(text)
            self.add_message(
                self.app.get_username(),
                text,
                datetime.now().strftime("%H:%M"),
                is_own=True
            )
            self.message_input.value = ""
            self.message_input.update()
            self.is_typing = False

    def on_text_change(self, e):
        if self.message_input.value and not self.is_typing:
            self.is_typing = True
            self.app.send_typing_status(True)
        elif not self.message_input.value and self.is_typing:
            self.is_typing = False
            self.app.send_typing_status(False)

    def on_logout(self, e):
        self.app.logout()