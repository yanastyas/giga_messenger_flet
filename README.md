# GigaMessenger — мессенджер для СНТ «Аргус»

Мобильное приложение-мессенджер для членов садоводческого некоммерческого товарищества (СНТ) «Аргус». Написано на Python с использованием Flet. Работает с облачной базой данных PostgreSQL в Yandex Cloud.

## 📋 Возможности

### Чат
- 💬 Общий чат в реальном времени
- 📜 История сообщений (загружается из БД при входе)
- 💾 Оффлайн-сообщения (доставляются при следующем входе)
- 🟢 Статусы online/offline
- ✏️ Индикатор «печатает...»
- 🔐 Регистрация и вход по имени пользователя и паролю (SHA-256)

### Работа с БД
- ☁️ Облачное хранение в PostgreSQL (Yandex Cloud)
- 🔒 SSL-подключение с сертификатом
- 📊 Сохранение всех сообщений и пользователей
- 🔄 Восстановление истории при перезапуске сервера

### В разработке
- 📋 Правила при регистрации
- 🚫 Блокировка за оскорбления
- 📧 Обращения председателю
- 💰 Запросы бухгалтеру
- 📰 Официальная информация СНТ
- 👑 Роли: председатель, правление, ревизия, админ
- 😶 Аватарка-инкогнито по умолчанию
- 🔒 Админ-панель

## 🏗️ Архитектура

```
┌───────────────────────┐
│  Flet-клиент (mobile) │
│  (Android / iOS)      │
└───────────┬───────────┘
            │ socket (JSON)
            ▼
┌───────────────────────┐
│  server/server.py     │ ← сервер на Python
│  (принимает сокеты)   │
└───────────┬───────────┘
            │ psycopg2 + SSL
            ▼
┌───────────────────────┐
│  PostgreSQL (Yandex)  │ ← облачная БД
│  users, messages, ... │
└───────────────────────┘
```

## 📁 Структура проекта

```
giga_messenger_flet/
├── .env                  # Секреты (НЕ в Git)
├── .env.example          # Шаблон для нового разработчика
├── .gitignore            # Исключения Git
├── README.md             # Этот файл
├── main.py               # Точка входа клиента
├── app_config.py         # Конфигурация сервера (SERVER_HOST, SERVER_PORT)
├── requirements.txt      # Зависимости Python
├── run.bat               # Скрипт запуска (Windows)
│
├── server/               # Серверная часть
│   ├── __init__.py
│   ├── server.py         # Сокет-сервер
│   ├── db_pg.py          # Работа с PostgreSQL
│   ├── migrate_db.py     # Миграции схемы БД
│   ├── make_admin.py     # Присвоение роли admin
│   └── check_roles.py    # Просмотр ролей
│
└── src/                  # Клиентская часть
    ├── __init__.py
    ├── app.py            # Главный класс приложения
    ├── config.py         # Конфигурация клиента
    ├── db.py             # Подключение к БД (для отладки)
    ├── init_db.py        # Создание таблиц
    ├── client/           # Сетевой клиент
    │   ├── __init__.py
    │   ├── database.py
    │   ├── encryption.py
    │   ├── file_handler.py
    │   └── socket_client.py
    ├── screens/          # Экраны Flet
    │   ├── __init__.py
    │   ├── chat_screen.py
    │   └── login_screen.py
    └── widgets/          # Виджеты
        ├── __init__.py
        └── message_bubble.py
```

## 🚀 Установка и запуск

### Требования
- Python 3.10+
- PostgreSQL 15+ (облако Yandex Cloud или локально)
- Git
- Windows / Linux / macOS

### 1. Клонирование репозитория

```bash
git clone https://github.com/yanastyas/giga_messenger_flet.git
cd giga_messenger_flet
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/macOS
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

Скопируйте `.env.example` → `.env` и заполните своими данными:

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/macOS
```

Откройте `.env` и укажите:
- `DB_HOST` — хост кластера PostgreSQL (FQDN)
- `DB_PORT` — порт (6432 для Yandex Cloud)
- `DB_NAME` — имя базы данных
- `DB_USER` — имя пользователя
- `DB_PASSWORD` — пароль
- `DB_SSLMODE` — `verify-full`

### 5. Скачивание SSL-сертификата Yandex Cloud

```bash
mkdir %USERPROFILE%\.postgresql
curl -o %USERPROFILE%\.postgresql\root.crt https://storage.yandexcloud.net/cloud-certs/CA.pem
```

### 6. Инициализация БД

```bash
python -m src.db            # Проверка подключения
python -m src.init_db       # Создание таблиц
python -m server.migrate_db # Обновление схемы (роли, апелляции)
```

### 7. Запуск сервера

В **первом** терминале:

```bash
python -m server.server
```

Ожидаемый вывод:

```
🚀 Сервер запущен на 127.0.0.1:8888
📦 База данных: PostgreSQL (Yandex Cloud)
```

### 8. Запуск клиента

Во **втором** терминале:

```bash
flet run main.py
```

Откроется окно приложения. Введите имя пользователя, пароль, IP сервера (`127.0.0.1`) и нажмите **Регистрация**.

## 🗄️ Схема базы данных

### Таблица `users`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ |
| `username` | VARCHAR(100) | Уникальное имя пользователя |
| `password_hash` | VARCHAR(255) | SHA-256 хеш пароля |
| `display_name` | VARCHAR(100) | Отображаемое имя |
| `avatar_url` | TEXT | URL аватарки |
| `role` | VARCHAR(50) | `member`, `chairman`, `board_member`, `audit_member`, `admin` |
| `status` | VARCHAR(20) | `active` / `blocked` |
| `block_until` | BIGINT | Время окончания блокировки (unix timestamp) |
| `created_at` | BIGINT | Дата регистрации |
| `last_seen` | BIGINT | Последний вход |
| `rules_accepted` | BOOLEAN | Согласие с правилами |

### Таблица `messages`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ |
| `sender_username` | VARCHAR(100) | Отправитель |
| `receiver_username` | VARCHAR(100) | Получатель (`NULL` для общего чата) |
| `text` | TEXT | Текст сообщения |
| `timestamp` | BIGINT | Время отправки |

### Таблица `offline_messages`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Первичный ключ |
| `to_user` | VARCHAR(100) | Получатель |
| `from_user` | VARCHAR(100) | Отправитель |
| `message` | TEXT | Текст сообщения |
| `timestamp` | BIGINT | Время |

### Другие таблицы

- `appeals` — обращения председателю
- `accounting_requests` — запросы бухгалтеру
- `info_posts` — официальная информация СНТ
- `bans` — история блокировок

## 🔑 Роли пользователей

| Роль | Значение | Возможности |
|------|----------|-------------|
| `member` | Член СНТ | Чтение чата, отправка сообщений |
| `chairman` | Председатель | + публикация официальной информации |
| `board_member` | Член правления | + публикация официальной информации |
| `audit_member` | Ревизионная комиссия | + публикация официальной информации |
| `admin` | Администратор | Полный доступ, управление ролями и блокировками |

Присвоение роли:

```bash
python -m server.make_admin <username>
```

## 🔧 Скрипты для разработчика

| Скрипт | Назначение |
|--------|-----------|
| `python -m src.db` | Проверка подключения к PostgreSQL |
| `python -m src.init_db` | Первичное создание таблиц |
| `python -m server.migrate_db` | Обновление схемы БД |
| `python -m server.make_admin <username>` | Присвоение роли admin |
| `python -m server.check_roles` | Список пользователей и их ролей |
| `python -m server.server` | Запуск сервера |

## 🛠️ Технологии

- **Python 3.10+** — язык программирования
- **Flet** — кроссплатформенный UI (Android, iOS, Windows, macOS, Linux)
- **PostgreSQL 18** — облачная база данных (Yandex Cloud)
- **psycopg2** — драйвер PostgreSQL для Python
- **python-dotenv** — загрузка переменных окружения из `.env`
- **Yandex Cloud** — облачная инфраструктура (Managed Service for PostgreSQL)
- **Socket** — клиент-серверное взаимодействие
- **SHA-256** — хеширование паролей

## 🔒 Безопасность

- ✅ Пароли хешируются через SHA-256
- ✅ SSL-подключение к БД (`verify-full` + корневой сертификат)
- ✅ `.env` не попадает в Git
- ✅ `.env.example` содержит только заглушки
- ✅ Переменные окружения не хранятся в коде

## 🤝 Как внести вклад

1. Форкните репозиторий
2. Создайте ветку (`git checkout -b feature/новая-функция`)
3. Закоммитьте изменения (`git commit -m "Добавил новую функцию"`)
4. Запушьте (`git push origin feature/новая-функция`)
5. Создайте Pull Request

## 📌 Планы развития

- [x] Общий чат с историей
- [x] PostgreSQL в Yandex Cloud
- [x] Регистрация и вход
- [ ] Правила при регистрации
- [ ] Блокировка за оскорбления
- [ ] Обращения председателю
- [ ] Запросы бухгалтеру
- [ ] Официальная информация
- [ ] Роли и админ-панель
- [ ] Аватарки и профили
- [ ] Отправка фото/видео/файлов
- [ ] Упаковка в APK для Android
- [ ] Развёртывание сервера в облаке

## 📄 Лицензия

Проект создан для СНТ «Аргус». Все права защищены.

## 📞 Контакты

- **GitHub:** [@yanastyas](https://github.com/yanastyas)
- **Репозиторий:** [giga_messenger_flet](https://github.com/yanastyas/giga_messenger_flet)

---

⭐ Если проект был полезен — поставьте звезду на GitHub!
