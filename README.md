# Telegram-бот для описаний товаров Wildberries / Ozon

Бот на Python, aiogram и OpenAI API генерирует продающие описания товаров и SEO-ключевые слова для маркетплейсов Wildberries и Ozon.

## Возможности

- Команда `/start` с приветствием.
- Кнопка `📝 Создать описание товара`.
- Генерация ответа по названию товара:
  - продающее описание до 1000 символов;
  - SEO-ключевые слова списком.
- 3 бесплатных успешных генерации на пользователя.
- Сообщение `Лимит исчерпан` после превышения лимита.
- SQLite-хранилище пользователей и количества запросов.
- Логирование и обработка ошибок.

## Структура проекта

```text
.
├── main.py
├── requirements.txt
├── .env.example
├── database/
│   ├── __init__.py
│   └── db.py
├── handlers/
│   ├── __init__.py
│   └── user.py
└── services/
    ├── __init__.py
    └── ai.py
```

## Запуск

1. Создайте и активируйте виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
```

4. Заполните переменные в `.env`:

```env
BOT_TOKEN=ваш_токен_бота_из_BotFather
OPENAI_API_KEY=ваш_openai_api_key
OPENAI_MODEL=gpt-5.1
DATABASE_PATH=bot.db
LOG_LEVEL=INFO
```

5. Запустите бота:

```bash
python main.py
```

## Примечания

- `BOT_TOKEN` можно получить у Telegram-бота [@BotFather](https://t.me/BotFather).
- `OPENAI_API_KEY` создаётся в кабинете OpenAI Platform.
- База SQLite создаётся автоматически при первом запуске.
