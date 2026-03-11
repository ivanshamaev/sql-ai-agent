"""Database schema description for the LLM prompt."""
SCHEMA_DESC = """
Таблицы PostgreSQL (вакансии с HH.ru):

areas (регионы):
  id TEXT PK, name TEXT, url TEXT

employers (работодатели):
  id TEXT PK, name TEXT, url TEXT, alternate_url TEXT

vacancies (вакансии):
  id TEXT PK, name TEXT, url TEXT, alternate_url TEXT,
  published_at TIMESTAMPTZ, archived BOOLEAN,
  salary_from INTEGER, salary_to INTEGER, salary_currency TEXT, salary_gross BOOLEAN,
  area_id TEXT FK -> areas.id, employer_id TEXT FK -> employers.id,
  employment_id TEXT, employment_name TEXT, experience_id TEXT, experience_name TEXT,
  type_id TEXT, premium BOOLEAN, has_test BOOLEAN, response_letter_required BOOLEAN,
  created_at TIMESTAMPTZ

Связи: vacancies.area_id = areas.id, vacancies.employer_id = employers.id.
По умолчанию учитывать только неархивные вакансии: archived = FALSE.
"""
