# test_database.py
from src.client.database import MessageDatabase
from src.config import config

# Создаем экземпляр
db = MessageDatabase("test_user")

# Сохраняем сообщение
db.save_message(
    message_id="msg_001",
    sender="test_user",
    receiver="test_user2",
    message="Hello, GigaMessenger!"
)

# Получаем историю
history = db.get_chat_history("test_user2")
print(f"История: {history}")

# Добавляем реакцию
db.add_reaction("msg_001", "👍")

# Получаем реакции
reactions = db.get_reactions("msg_001")
print(f"Реакции: {reactions}")

db.close()
print("✅ Тест успешен!")