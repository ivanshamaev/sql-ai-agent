# SQL AI Agent

AI-агент для запросов к PostgreSQL на естественном языке. Данные — вакансии с [HH.ru](https://hh.ru) (схема совместима с их API).

Режимы работы:
- **Консоль** — быстрые запросы из терминала
- **Веб-интерфейс** — простой UI на FastAPI (одна страница, ввод вопроса и таблица с результатом)

Агент формирует SQL по вашему вопросу с помощью LLM с **OpenAI-совместимым API** (endpoint `POST /v1/chat/completions`): OpenAI, OpenRouter и т.п. API Cursor (api.cursor.com) для этого не подходит — используйте ключ OpenAI или OpenRouter.

---

## Требования

- Python 3.11+
- PostgreSQL 14+
- API-ключ для LLM (OpenAI-совместимый endpoint)

---

## Быстрый старт (Docker)

1. Клонируйте репозиторий и перейдите в каталог проекта.

2. Создайте файл `.env` в корне проекта:

```bash
cp .env.sample .env
```

Заполните в `.env`:
- `OPENAI_API_KEY` — ключ от провайдера с API в формате OpenAI (например, [OpenAI](https://platform.openai.com/api-keys) или [OpenRouter](https://openrouter.ai/keys)).
- `OPENAI_BASE_URL` — базовый URL API (`https://api.openai.com/v1` или `https://openrouter.ai/api/v1`). Сервис должен поддерживать `POST /v1/chat/completions`.

3. Запустите сервисы:

```bash
docker compose up -d --build
```

PostgreSQL поднимется на порту 5432, веб-интерфейс — на **http://localhost:8001**. Схема БД создаётся автоматически при первом запуске (миграции в `migrations/` монтируются в `docker-entrypoint-initdb.d`).

4. Загрузите тестовые вакансии с HH.ru (в контейнер приложения или локально с указанием `DATABASE_URL`):

```bash
# Локально (после pip install -r requirements.txt и при запущенном Postgres)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sql_ai_agent
python scripts/load_hh_vacancies.py

# Или выполнить внутри контейнера
docker compose exec app python scripts/load_hh_vacancies.py
```

Переменная `DATABASE_URL` внутри контейнера уже указывает на сервис `postgres`, поэтому второй вариант подходит при работе полностью в Docker.

5. Откройте в браузере http://localhost:8001 и задайте вопрос, например:
   - «Топ-10 работодателей по количеству вакансий»
   - «Вакансии с зарплатой от 100000»
   - «Сколько вакансий по городам?»

---

## Запуск без Docker (локально)

1. Установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Запустите PostgreSQL и создайте БД:

```bash
createdb sql_ai_agent
psql -d sql_ai_agent -f migrations/001_init_schema.sql
```

3. Создайте `.env` (см. выше) и при необходимости измените `DATABASE_URL`.

4. Загрузите вакансии:

```bash
python scripts/load_hh_vacancies.py
```

5. Запуск веб-интерфейса:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Или консольный режим:

```bash
python cli.py "Топ-5 городов по числу вакансий"
```

---

## Переменные окружения

| Переменная           | Описание                              | По умолчанию                    |
|----------------------|----------------------------------------|---------------------------------|
| `DATABASE_URL`       | Подключение к PostgreSQL              | `postgresql://postgres:postgres@localhost:5432/sql_ai_agent` |
| `OPENAI_API_KEY`     | Ключ LLM (обязательно)                 | —                               |
| `OPENAI_BASE_URL`    | Базовый URL OpenAI-совместимого API   | `https://api.openai.com/v1`     |
| `OPENAI_MODEL`       | Модель (например, gpt-4o-mini)        | `gpt-4o-mini`                   |
| `AGENT_READ_ONLY`    | Разрешать только SELECT               | `true`                          |

---

## Использование агента

- **Веб**: откройте http://localhost:8001, введите вопрос в поле и нажмите «Выполнить». Будет показан сгенерированный SQL и таблица результата.
- **Консоль**: `python cli.py "Ваш вопрос"`. Вывод: SQL и таблица в терминале.
- **API**: `POST /api/ask` с полем формы `question`. Ответ: `{ "sql": "...", "rows": [...], "error": null }`.

Агент использует схему БД (таблицы `vacancies`, `areas`, `employers`) и локальные навыки из каталога `skills/` (рекомендации по написанию SQL), чтобы генерировать только SELECT-запросы (при `AGENT_READ_ONLY=true`).

---

## Структура проекта

```
sql-ai-agent/
├── app/                 # Веб: FastAPI + шаблон index.html
├── agent/                # Ядро агента: промпты, извлечение SQL, выполнение
├── migrations/           # SQL-миграции (схема для HH.ru)
├── scripts/              # load_hh_vacancies.py, entrypoint
├── skills/               # Локальные «навыки» (best practices) для промпта
├── config.py             # Настройки (pydantic-settings)
├── cli.py                # Консольный интерфейс
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Skills (навыки)

В каталоге `skills/` лежат markdown-файлы с рекомендациями по PostgreSQL и по схеме проекта. Они подставляются в системный промпт агента. Можно добавить свои файлы или использовать идеи из:

- [pg-aiguide](https://github.com/timescale/pg-aiguide) (Postgres + TimescaleDB)
- [supabase/agent-skills](https://github.com/supabase/agent-skills) (best practices по Postgres/Supabase)
- [wshobson/agents](https://github.com/wshobson/agents) (плагины/навыки для агентов)

Формат: обычный Markdown; имя файла произвольное (например, `postgres-best-practices.md`).

---

## Безопасность

- По умолчанию агент выполняет только **SELECT** (и CTE с SELECT). Изменить поведение можно через `AGENT_READ_ONLY=false` (не рекомендуется для общих окружений).
- Не передавайте в приложение секреты БД и API-ключи через фронтенд; используйте только переменные окружения на сервере.

---

## Лицензия

MIT.
