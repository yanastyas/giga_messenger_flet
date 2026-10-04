# main.py
import flet as ft
from src.app import GigaMessengerApp

def main(page: ft.Page):
    page.window.width = 400
    page.window.height = 700
    page.window.resizable = False
    page.title = "GigaMessenger"
    page.bgcolor = "#0f0f1a"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    app = GigaMessengerApp()
    app.run(page)

if __name__ == '__main__':
    ft.app(target=main, port=8888)