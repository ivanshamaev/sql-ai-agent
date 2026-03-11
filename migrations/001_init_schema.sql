-- Schema for HH.ru vacancies (compatible with API response)
-- https://github.com/hhru/api/blob/master/docs/vacancies.md

CREATE TABLE IF NOT EXISTS areas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT
);

CREATE TABLE IF NOT EXISTS employers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    alternate_url TEXT
);

CREATE TABLE IF NOT EXISTS vacancies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT,
    alternate_url TEXT,
    published_at TIMESTAMPTZ,
    archived BOOLEAN DEFAULT FALSE,
    salary_from INTEGER,
    salary_to INTEGER,
    salary_currency TEXT,
    salary_gross BOOLEAN,
    area_id TEXT REFERENCES areas(id),
    employer_id TEXT REFERENCES employers(id),
    employment_id TEXT,
    employment_name TEXT,
    experience_id TEXT,
    experience_name TEXT,
    type_id TEXT DEFAULT 'open',
    premium BOOLEAN DEFAULT FALSE,
    has_test BOOLEAN DEFAULT FALSE,
    response_letter_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vacancies_employer ON vacancies(employer_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_area ON vacancies(area_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_published_at ON vacancies(published_at);
CREATE INDEX IF NOT EXISTS idx_vacancies_salary_from ON vacancies(salary_from) WHERE salary_from IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_vacancies_name_gin ON vacancies USING gin(to_tsvector('russian', name));

COMMENT ON TABLE vacancies IS 'Вакансии с hh.ru API';
COMMENT ON TABLE areas IS 'Регионы (города)';
COMMENT ON TABLE employers IS 'Работодатели';
