# Postgres best practices for SQL agent

Use when generating SQL for this project (PostgreSQL, schema: vacancies from HH.ru).

## General
- Prefer standard SQL and PostgreSQL idioms.
- Use meaningful aliases (v for vacancies, e for employers, a for areas).
- For text search use `to_tsvector('russian', name)` and `plainto_tsquery('russian', ...)` or `ILIKE` for simple patterns.

## Schema (HH.ru vacancies)
- **vacancies**: id (text), name, url, alternate_url, published_at (timestamptz), archived (bool), salary_from, salary_to, salary_currency, salary_gross, area_id, employer_id, employment_id/name, experience_id/name, type_id, premium, has_test, response_letter_required, created_at.
- **areas**: id (text), name, url.
- **employers**: id (text), name, url, alternate_url.

## Queries
- Always filter out archived if not explicitly asked: `WHERE archived = FALSE` or `AND v.archived = FALSE`.
- For salary use salary_from/salary_to; handle NULL (vacancy may not disclose salary).
- Joins: `vacancies.area_id = areas.id`, `vacancies.employer_id = employers.id`.
- Dates: published_at is ISO text from API; stored as TIMESTAMPTZ. Use `published_at::date` or `DATE(published_at)` for day.

## Safety
- Prefer SELECT only. Do not generate INSERT/UPDATE/DELETE/DDL unless explicitly requested and allowed.
