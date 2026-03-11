# Архитектура проекта SQL AI Agent

## 1. Состав системы

| Компонент | Назначение |
|-----------|------------|
| **Точки входа** | CLI (`cli.py`), веб (FastAPI в `app/main.py`) |
| **Ядро агента** | `agent/` — промпты, вызов LLM, извлечение SQL, выполнение в БД |
| **Конфигурация** | `config.py` — настройки из `.env` |
| **Данные** | PostgreSQL: схема в `migrations/`, загрузка из HH.ru в `scripts/load_hh_vacancies.py` |
| **Навыки** | `skills/*.md` — текст в системный промпт (best practices) |
| **Инфраструктура** | Docker: образ приложения + контейнер Postgres |

---

## 2. Поток запроса (кто что вызывает)

```
Пользователь
    │
    ├── Веб: браузер → GET / → HTML
    │              → POST /api/ask (question) → app.main.api_ask()
    │
    └── Консоль: python cli.py "вопрос" → cli.main()
                        │
                        ▼
              agent.sql_agent.ask_agent(question)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   config.get_settings()   agent.prompts.build_system_prompt()
        │                        │
        │                        ├── agent.schema_desc.SCHEMA_DESC
        │                        └── skills/*.md (load_skills_text)
        │
        ▼
   OpenAI client.chat.completions.create(system, user=question)
        │
        ▼
   extract_sql_from_response(content) → sql
        │
        ▼
   run_sql(database_url, sql) → is_read_only() → psycopg execute
        │
        ▼
   return { "sql", "rows", "error" }
        │
        ▼
   Веб: JSON в ответ; CLI: таблица в консоль
```

---

## 3. Модули и зависимости

```
config.py
  └── читает .env, отдаёт Settings (database_url, openai_*, skills_dir)

agent/schema_desc.py
  └── константа SCHEMA_DESC (описание таблиц для промпта)

agent/prompts.py
  ├── импортирует SCHEMA_DESC
  ├── load_skills_text(skills_dir) — читает *.md из skills/
  └── build_system_prompt(skills_dir) — шаблон + схема + skills

agent/sql_agent.py
  ├── импортирует build_system_prompt, get_settings
  ├── extract_sql_from_response() — парсит ```sql ... ``` или SELECT/WITH
  ├── is_read_only() — проверка, что нет INSERT/UPDATE/DELETE/DDL
  ├── run_sql() — psycopg: execute, возврат list[dict]
  └── ask_agent(question) — оркестрация: settings → LLM → sql → run_sql → result

app/main.py
  ├── импортирует ask_agent
  ├── GET / → index.html
  └── POST /api/ask (Form: question) → ask_agent(question) → JSON

cli.py
  └── импортирует ask_agent; typer + rich для вывода
```

**Внешние зависимости по ходу запроса:** `.env` → PostgreSQL (миграции при старте контейнера), LLM API (OpenAI-совместимый endpoint).

---

## 4. Взаимодействие с внешними системами

| Внешняя система | Кто обращается | Когда |
|-----------------|----------------|-------|
| **PostgreSQL** | `agent/sql_agent.run_sql()` | Выполнение сгенерированного SQL |
| **LLM API** (OpenAI/OpenRouter) | `agent/sql_agent.ask_agent()` → `OpenAI().chat.completions.create()` | Генерация SQL по вопросу |
| **Файловая система** | `config` (skills_dir), `prompts.load_skills_text()` | Загрузка skills; `app/main` — чтение index.html |
| **HH.ru API** | только `scripts/load_hh_vacancies.py` | Наполнение БД (не входит в цикл запроса пользователя) |

---

## 5. Слои (упрощённо)

| Слой | Содержимое |
|------|------------|
| **Ввод** | CLI, веб-форма, POST /api/ask |
| **Оркестрация** | `ask_agent()`: конфиг → промпт → LLM → извлечение SQL → проверка read-only → выполнение |
| **Данные** | PostgreSQL (вакансии, области, работодатели); схема из migrations |
| **Конфиг и статика** | config.py, .env; skills/, app/templates/ |

---

## 6. Диаграмма компонентов

```
                    ┌─────────────┐
                    │   .env      │
                    └──────┬──────┘
                           │
    ┌──────────────┐       ▼       ┌──────────────────┐
    │  cli.py      │──────────────▶│  config.py       │
    └──────┬───────┘               │  get_settings()  │
           │                       └────────┬─────────┘
           │                                │
           │  ┌─────────────────────────────┘
           │  │
           ▼  ▼  ┌─────────────────────────────────────────┐
    ┌──────────────┐     ┌──────────────────────────────┐  │
    │  app/main.py │────▶│  agent/sql_agent.py           │  │
    │  (FastAPI)   │     │  ask_agent()                  │  │
    └──────────────┘     └───────┬──────────────────────┘  │
                                │                           │
           ┌────────────────────┼────────────────────┐       │
           ▼                    ▼                    ▼       │
    ┌───────────────┐   ┌───────────────┐   ┌─────────────┐ │
    │ agent/prompts │   │ OpenAI client  │   │ run_sql()   │ │
    │ build_system_ │   │ chat.completions│   │ → psycopg   │ │
    │ prompt()      │   │                │   │ → PostgreSQL│ │
    └───────┬───────┘   └────────────────┘   └─────────────┘ │
            │                                                      │
            ├── schema_desc.SCHEMA_DESC                            │
            └── skills/*.md ────────────────────────────────────────┘
```
