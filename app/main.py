"""FastAPI app: API + simple web UI for SQL agent."""
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from agent.sql_agent import ask_agent

app = FastAPI(title="SQL AI Agent", description="NL -> SQL по вакансиям HH.ru")

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    html = (Path(__file__).resolve().parent / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.post("/api/ask")
async def api_ask(question: str = Form(...)):
    result = ask_agent(question.strip())
    return result


def main():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
