@echo off
echo Запуск Flet Desktop клиента...
start "" "venv\Lib\site-packages\flet_desktop\app\flet\flet.exe" --port 8888

echo Ожидание запуска клиента (10 секунд)...
timeout /t 10 /nobreak >nul

echo Запуск приложения...
venv\Scripts\python.exe main.py

pause
