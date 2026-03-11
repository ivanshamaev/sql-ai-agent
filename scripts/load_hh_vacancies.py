#!/usr/bin/env python3
"""
Load vacancies from HH.ru API into PostgreSQL.
Run after migrations. Uses public API (no auth for search).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from dotenv import load_dotenv
from psycopg import connect

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sql_ai_agent")
HH_API = "https://api.hh.ru"


def fetch_vacancies(text: str = "Python", per_page: int = 50, pages: int = 2) -> list[dict]:
    vacancies = []
    with httpx.Client(timeout=30.0) as client:
        for page in range(pages):
            r = client.get(
                f"{HH_API}/vacancies",
                params={"text": text, "per_page": per_page, "page": page},
            )
            r.raise_for_status()
            data = r.json()
            vacancies.extend(data.get("items", []))
            if page >= data.get("pages", 1) - 1:
                break
    return vacancies


def vacancy_to_row(item: dict) -> dict:
    salary = item.get("salary") or {}
    area = item.get("area") or {}
    employer = item.get("employer") or {}
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "url": item.get("url"),
        "alternate_url": item.get("alternate_url"),
        "published_at": item.get("published_at"),
        "archived": item.get("archived", False),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "salary_currency": salary.get("currency"),
        "salary_gross": salary.get("gross"),
        "area_id": area.get("id"),
        "employer_id": employer.get("id"),
        "employment_id": (item.get("employment") or {}).get("id"),
        "employment_name": (item.get("employment") or {}).get("name"),
        "experience_id": (item.get("experience") or {}).get("id"),
        "experience_name": (item.get("experience") or {}).get("name"),
        "type_id": (item.get("type") or {}).get("id", "open"),
        "premium": item.get("premium", False),
        "has_test": item.get("has_test", False),
        "response_letter_required": item.get("response_letter_required", False),
    }


def ensure_area(conn, area_id: str, name: str, url: str | None):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO areas (id, name, url) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, url = EXCLUDED.url",
            (area_id, name, url),
        )


def ensure_employer(conn, employer_id: str, name: str, url: str | None, alternate_url: str | None):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO employers (id, name, url, alternate_url)
               VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, url = EXCLUDED.url, alternate_url = EXCLUDED.alternate_url""",
            (employer_id, name, url, alternate_url),
        )


def insert_vacancy(conn, row: dict):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vacancies (
                id, name, url, alternate_url, published_at, archived,
                salary_from, salary_to, salary_currency, salary_gross,
                area_id, employer_id, employment_id, employment_name,
                experience_id, experience_name, type_id, premium, has_test, response_letter_required
            ) VALUES (
                %(id)s, %(name)s, %(url)s, %(alternate_url)s, %(published_at)s, %(archived)s,
                %(salary_from)s, %(salary_to)s, %(salary_currency)s, %(salary_gross)s,
                %(area_id)s, %(employer_id)s, %(employment_id)s, %(employment_name)s,
                %(experience_id)s, %(experience_name)s, %(type_id)s, %(premium)s, %(has_test)s, %(response_letter_required)s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name, url = EXCLUDED.url, alternate_url = EXCLUDED.alternate_url,
                published_at = EXCLUDED.published_at, archived = EXCLUDED.archived,
                salary_from = EXCLUDED.salary_from, salary_to = EXCLUDED.salary_to,
                salary_currency = EXCLUDED.salary_currency, salary_gross = EXCLUDED.salary_gross,
                area_id = EXCLUDED.area_id, employer_id = EXCLUDED.employer_id,
                employment_id = EXCLUDED.employment_id, employment_name = EXCLUDED.employment_name,
                experience_id = EXCLUDED.experience_id, experience_name = EXCLUDED.experience_name,
                type_id = EXCLUDED.type_id, premium = EXCLUDED.premium,
                has_test = EXCLUDED.has_test, response_letter_required = EXCLUDED.response_letter_required
            """,
            row,
        )


def main():
    print("Fetching vacancies from HH.ru (text=Python)...")
    items = fetch_vacancies(text="Python", per_page=50, pages=2)
    print(f"Got {len(items)} items")

    with connect(DATABASE_URL) as conn:
        seen_areas = set()
        seen_employers = set()
        for item in items:
            row = vacancy_to_row(item)
            area = item.get("area")
            if area and area.get("id") and area["id"] not in seen_areas:
                ensure_area(conn, area["id"], area.get("name", ""), area.get("url"))
                seen_areas.add(area["id"])
            emp = item.get("employer")
            if emp and emp.get("id") and emp["id"] not in seen_employers:
                ensure_employer(conn, emp["id"], emp.get("name", ""), emp.get("url"), emp.get("alternate_url"))
                seen_employers.add(emp["id"])
            insert_vacancy(conn, row)
        conn.commit()
    print("Done.")


if __name__ == "__main__":
    main()
