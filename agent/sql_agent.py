"""SQL agent: natural language -> SQL -> execution."""
import re
from typing import Any

from openai import OpenAI
from psycopg import connect
from psycopg.rows import dict_row

from agent.prompts import build_system_prompt
from config import get_settings


def extract_sql_from_response(content: str) -> str | None:
    """Extract first SQL block from markdown (```sql ... ```) or return trimmed content."""
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # No block: treat whole content as SQL if it looks like it
    stripped = content.strip()
    if stripped.upper().startswith("SELECT") or stripped.upper().startswith("WITH"):
        return stripped
    return None


def is_read_only(sql: str) -> bool:
    """Check that SQL is read-only (SELECT/WITH only)."""
    sql_upper = sql.upper().strip()
    # Allow only SELECT and CTE (WITH)
    if sql_upper.startswith("WITH") or sql_upper.startswith("SELECT"):
        # Disallow dangerous keywords
        dangerous = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE")
        for kw in dangerous:
            if re.search(rf"\b{kw}\b", sql_upper):
                return False
        return True
    return False


def run_sql(database_url: str, sql: str, read_only: bool) -> list[dict[str, Any]]:
    with connect(database_url, row_factory=dict_row) as conn:
        if read_only and not is_read_only(sql):
            raise ValueError("Разрешены только SELECT-запросы. Отключите AGENT_READ_ONLY или измените запрос.")
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                return [dict(row) for row in cur.fetchall()]
            return []


def ask_agent(question: str) -> dict[str, Any]:
    """
    Ask the agent: turn question into SQL and run it.
    Returns dict with keys: sql, rows, error (if any).
    """
    settings = get_settings()
    if not settings.openai_api_key:
        return {"sql": None, "rows": [], "error": "OPENAI_API_KEY не задан"}

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url.rstrip("/"),
    )
    system = build_system_prompt(settings.skills_dir)

    try:
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        sql = extract_sql_from_response(content)
        if not sql:
            return {"sql": None, "rows": [], "error": "Не удалось извлечь SQL из ответа модели", "raw": content}

        rows = run_sql(settings.database_url, sql, settings.agent_read_only)
        return {"sql": sql, "rows": rows, "error": None}
    except Exception as e:
        return {"sql": None, "rows": [], "error": str(e)}
