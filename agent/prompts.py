"""Prompt building for the SQL agent."""
from pathlib import Path

from agent.schema_desc import SCHEMA_DESC

SYSTEM_TEMPLATE = """Ты — SQL-агент. Твоя задача: по вопросу пользователя на естественном языке сформировать один SQL-запрос к PostgreSQL.

Схема БД:
{schema}

Правила:
- Отвечай только одним SQL-запросом. Без пояснений до или после запроса.
- Запрос должен быть только SELECT (никаких INSERT/UPDATE/DELETE/DDL), если иное не разрешено.
- Используй только существующие таблицы и поля из схемы выше.
- Для поиска по названию вакансии можно использовать ILIKE или to_tsvector('russian', name).
- По умолчанию фильтруй неархивные вакансии: archived = FALSE.
- Формат ответа: помести запрос в блок markdown с языком sql, например:
```sql
SELECT ...
```
"""


def load_skills_text(skills_dir: Path) -> str:
    text_parts = []
    if not skills_dir.is_dir():
        return ""
    for path in sorted(skills_dir.glob("*.md")):
        text_parts.append(path.read_text(encoding="utf-8"))
    if not text_parts:
        return ""
    return "\n\n---\n\nДополнительные рекомендации (best practices):\n\n" + "\n\n".join(text_parts)


def build_system_prompt(skills_dir: Path | None = None) -> str:
    base = SYSTEM_TEMPLATE.format(schema=SCHEMA_DESC)
    if skills_dir and skills_dir.is_dir():
        base += load_skills_text(skills_dir)
    return base
