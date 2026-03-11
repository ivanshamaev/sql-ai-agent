#!/usr/bin/env python3
"""Console interface for SQL AI Agent."""
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table
import typer

from agent.sql_agent import ask_agent

console = Console()
app = typer.Typer(help="SQL AI Agent — вопросы по вакансиям HH.ru на естественном языке.")


@app.command()
def main(
    question: Optional[str] = typer.Argument(None, help="Вопрос по вакансиям, например: Топ-5 городов по числу вакансий"),
):
    if not question:
        console.print("[yellow]Использование:[/] python cli.py \"Ваш вопрос по вакансиям\"")
        console.print("[dim]Пример:[/] python cli.py Топ-5 городов по числу вакансий")
        sys.exit(0)
    result = ask_agent(question.strip())
    if result.get("error"):
        console.print("[red]Ошибка:[/]", result["error"])
        if result.get("sql"):
            console.print("[dim]SQL:[/]\n", result["sql"])
        sys.exit(1)
    if result.get("sql"):
        console.print("[cyan]SQL:[/]\n", result["sql"])
    rows = result.get("rows") or []
    if rows:
        table = Table(show_header=True, header_style="bold cyan")
        for key in rows[0].keys():
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row.get(k, "")) for k in rows[0].keys()])
        console.print(table)
        console.print(f"[dim]Строк: {len(rows)}[/]")
    else:
        console.print("[dim]Нет строк в результате.[/]")


if __name__ == "__main__":
    app()
