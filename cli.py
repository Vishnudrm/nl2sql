from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from core.discover import find_data_files
from core.ollama_manager import start_ollama, stop_ollama
from core.load import load_file
from core.schema import extract_schema
from core.correct import correct_question
from core.prompt import build_prompt
from core.generator import generate_sql
from core.validator import validate_sql
from core.executor import execute_sql
from core.exporter import export_dataframe

app = typer.Typer()
console = Console()

def resolve_file(file: Optional[str]) -> str:
    """Return a concrete filepath, prompting the user if one wasn't given."""
    if file:
        return file

    candidates = find_data_files()

    if not candidates:
        console.print("[bold red]No CSV or Excel files found in this directory.[/bold red]")
        raise typer.Exit(code=1)

    if len(candidates) == 1:
        console.print(f"[dim]Using {candidates[0]} (only data file found here)[/dim]")
        return candidates[0]

    console.print("\n[bold]Multiple data files found:[/bold]")
    for i, path in enumerate(candidates, start=1):
        console.print(f"  {i}. {path}")

    choice = typer.prompt("Which file do you want to query? (number)")
    try:
        index = int(choice) - 1
        if index < 0 or index >= len(candidates):
            raise ValueError
    except ValueError:
        console.print("[bold red]Invalid selection.[/bold red]")
        raise typer.Exit(code=1)

    return candidates[index]

def maybe_export(df) -> None:
    """Ask the user if they want to save the result, and if so, where and in what format."""
    if not typer.confirm("\nSave these results to a file?", default=False):
        return

    format_choice = typer.prompt("Format (csv/excel)", default="csv").strip().lower()
    ext = ".csv" if format_choice.startswith("csv") else ".xlsx"

    filename = typer.prompt("Filename (without extension)", default="results")
    location = typer.prompt("Save location (directory)", default=".")

    save_path = Path(location) / f"{filename}{ext}"

    try:
        export_dataframe(df, str(save_path))
        console.print(f"[green]Saved to {save_path}[/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to save file: {e}[/bold red]")

@app.command()
def query(file: Optional[str] = typer.Argument(None), question: Optional[str] = typer.Argument(None)):
    file = resolve_file(file)
    if not question:
        question = typer.prompt("What do you want to know")

    ollama_process = start_ollama()
    try:
        con = load_file(file)
        schema_info = extract_schema(con)
        valid_columns = [c["column"] for c in schema_info]

        corrected_question = correct_question(question, schema_info)
        if corrected_question.lower() != question.lower():
            console.print(f"[dim]Interpreted as: \"{corrected_question}\"[/dim]")

        prompt = build_prompt(schema_info, "data", corrected_question)
        sql = generate_sql(prompt)

        if sql.startswith("CANNOT_ANSWER"):
            console.print(f"[bold red]{sql}[/bold red]")
            raise typer.Exit(code=1)

        valid, error = validate_sql(sql, valid_columns)

        if not valid:
            console.print(f"[yellow]First attempt invalid: {error}. Retrying...[/yellow]")
            retry_prompt = prompt + f"\n\nPrevious attempt failed: {error}\nTry again:"
            sql = generate_sql(retry_prompt)

            if sql.startswith("CANNOT_ANSWER"):
                console.print(f"[bold red]{sql}[/bold red]")
                raise typer.Exit(code=1)

            valid, error = validate_sql(sql, valid_columns)

        if not valid:
            console.print(f"[bold red]Could not generate valid SQL: {error}[/bold red]")
            raise typer.Exit(code=1)

        console.print("\n[bold]Generated SQL:[/bold]")
        console.print(Syntax(sql, "sql", theme="monokai"))

        df, exec_error = execute_sql(con, sql)
        if df is not None:
            console.print("\n[bold]Result:[/bold]")
            console.print(df.to_string(index=False))
            maybe_export(df)
        else:
            console.print(f"[bold red]Execution error:[/bold red] {exec_error}")
    finally:
        stop_ollama(ollama_process)

if __name__ == "__main__":
    app()