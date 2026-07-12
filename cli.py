import typer
from rich.console import Console
from rich.syntax import Syntax

from core.load import load_file
from core.schema import extract_schema
from core.correct import correct_question
from core.prompt import build_prompt
from core.generator import generate_sql
from core.validator import validate_sql
from core.executor import execute_sql

app = typer.Typer()
console = Console()

@app.command()
def query(file: str, question: str):
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
    else:
        console.print(f"[bold red]Execution error:[/bold red] {exec_error}")

if __name__ == "__main__":
    app()