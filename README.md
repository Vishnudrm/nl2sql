# nl2sql

Ask your CSV or Excel data questions in plain English. `nl2sql` converts natural language into SQL, runs it locally against your file using DuckDB, and shows you both the query and the answer — no cloud API keys, no data leaving your machine.

```
$ nl2sql

Using sample_sales.csv (only data file found here)
What do you want to know: show me total sales by category

Generated SQL:
SELECT category, SUM(price * quantity) AS total_sales
FROM data
GROUP BY category;

Result:
   category  total_sales
Electronics      71600.0
 Stationery        850.0
  Furniture       7700.0

Save these results to a file? [y/N]:
```

---

## Tools Used

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black" alt="DuckDB" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama" />
  <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="pandas" />
  <img src="https://img.shields.io/badge/Typer-000000?style=for-the-badge&logo=fastapi&logoColor=white" alt="Typer" />
  <img src="https://img.shields.io/badge/Rich-FAE042?style=for-the-badge&logo=python&logoColor=black" alt="Rich" />
</p>

| Tool | Role in this project |
|---|---|
| **[Python](https://python.org)** | Core language for the entire pipeline |
| **[DuckDB](https://duckdb.org)** | In-memory SQL engine that CSV/Excel data is loaded into and queried against |
| **[Ollama](https://ollama.com)** | Runs the local LLM (`qwen3:8b`) that powers SQL generation and typo correction — no cloud API calls. Started on-demand and shut down automatically after each query |
| **[pandas](https://pandas.pydata.org)** | Reads Excel files, shapes query results into DataFrames, and exports results back to CSV/Excel |
| **[openpyxl](https://openpyxl.readthedocs.io)** | Engine pandas uses under the hood to read and write `.xlsx` files |
| **[sqlglot](https://github.com/tobymao/sqlglot)** | Parses and validates every generated SQL query before it's allowed to execute |
| **[Typer](https://typer.tiangolo.com)** | Builds the command-line interface, including all interactive prompts |
| **[Rich](https://github.com/Textualize/rich)** | Syntax-highlighted SQL and formatted terminal output |

*Note: `sqlglot` doesn't have an official logo on shields.io, so it's listed in the table only, not the badge row above.*

---

## Table of Contents

- [The Full Vision](#the-full-vision)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [File-by-File Breakdown](#file-by-file-breakdown)
- [Setup](#setup)
- [Usage](#usage)
- [Example Walkthrough](#example-walkthrough)
- [Current State](#current-state)
- [Roadmap — What's Left to Build](#roadmap--whats-left-to-build)
- [License](#license)

---

## The Full Vision

Most people who work with spreadsheets hit the same wall: simple lookups are easy, but the moment you need to filter on multiple conditions, group by several fields, or ask a slightly complex question, you're either wrestling with nested formulas or writing SQL by hand. `nl2sql` is meant to close that gap completely — a tool you point at any CSV or Excel file, sitting anywhere on your machine, and just *ask*.

The complete vision for this tool is:

- **Zero setup per file.** Drop into any folder with data in it, type your question, and it just works — no manual loading, no specifying paths if there's only one obvious file to query.
- **Runs entirely locally.** Powered by a local LLM through Ollama (currently `qwen3:8b`), so sensitive data never leaves your machine and there's no API key or per-query cost.
- **Understands your data, not just your words.** It doesn't blindly translate text to SQL — it looks at your actual column names, types, and sample values first, so it knows what's actually queryable before it writes anything.
- **Forgiving of how you actually type.** Typos, shorthand, and casual phrasing get corrected before the query is built, and the tool tells you what it understood your question to mean.
- **Honest about its limits.** If you ask for something that isn't in the data (like a column that doesn't exist), it says so plainly instead of guessing or silently returning the wrong thing.
- **Safe by construction.** Every generated query is validated before execution — only `SELECT` statements are ever allowed, and every column referenced is checked against the real schema first.
- **Usable from anywhere.** Installed once, callable as a plain command (`nl2sql`) from any terminal, on any folder, without needing to `cd` into the project directory, activate a virtual environment, or type `python cli.py`.
- **Handles more than one file.** Whether that's picking between multiple files sitting in a folder, or eventually reasoning across related files together.
- **Doesn't waste resources when idle.** The local LLM only runs while you're actually asking it something — not sitting in memory 24/7 as a background service.
- **Lets you keep what you found.** Once you have a result, you can save it straight back out as a CSV or Excel file without leaving the tool.

Not all of this exists yet — see [Current State](#current-state) for what's actually built today, and [Roadmap](#roadmap--whats-left-to-build) for what's coming next.

---

## How It Works

Every query goes through the same pipeline, regardless of what you ask:

```
nl2sql (no arguments needed)
     │
     ▼
1. Discover data files in the current directory
   (auto-pick if there's one, ask if there's several)
     │
     ▼
2. Ask what you want to know, if not already given
     │
     ▼
3. Start Ollama on demand (only if it isn't already running)
     │
     ▼
4. Load the file into DuckDB (CSV or Excel)
     │
     ▼
5. Extract schema: column names, types, sample values
     │
     ▼
6. Correct typos in your question (using an LLM, aware of your real column/value names)
     │
     ▼
7. Build a prompt: schema + rules + your (corrected) question
     │
     ▼
8. Ask the local LLM (qwen3:8b via Ollama) to generate SQL
     │
     ▼
9. Validate the SQL: only SELECT statements, only real columns/aliases
     │
     ├─ Invalid? → retry once with the error fed back to the LLM
     │
     ▼
10. Execute the validated SQL against DuckDB
     │
     ▼
11. Show you the SQL used and the result table
     │
     ▼
12. Ask if you'd like to save the result (format, filename, location)
     │
     ▼
13. Stop Ollama, if this run was the one that started it
```

The key design decision behind this pipeline is **step 5 and step 9**: the LLM is never left to guess at your data's shape, and its output is never trusted blindly. It's shown the real schema before generating anything, and every query is checked against that same schema before it's allowed to run. This is what keeps the tool from hallucinating columns that don't exist or executing something destructive.

---

## Project Structure

```
nl2sql/
├── core/
│   ├── __init__.py
│   ├── discover.py       # Finds CSV/Excel files in the current directory
│   ├── ollama_manager.py # Starts/stops Ollama on demand, only if needed
│   ├── load.py            # Loads CSV/Excel into an in-memory DuckDB table
│   ├── schema.py           # Extracts column names, types, and sample values
│   ├── correct.py           # Fixes typos in the question using schema context
│   ├── prompt.py             # Builds the LLM prompt from schema + question
│   ├── generator.py           # Calls Ollama, cleans the raw model output
│   ├── validator.py            # Parses & validates generated SQL with sqlglot
│   ├── executor.py              # Runs validated SQL, returns a DataFrame
│   └── exporter.py               # Saves a result DataFrame to CSV or Excel
├── examples/
│   └── sample_sales.csv   # Sample dataset for trying the tool out
├── cli.py                # Entry point — wires the whole pipeline together
├── pyproject.toml        # Packaging config — makes `nl2sql` a global command
├── requirements.txt
└── README.md
```

---

## File-by-File Breakdown

### `core/discover.py`
Scans the current directory for `.csv`, `.xlsx`, and `.xls` files and returns them as a sorted list. Doesn't print or prompt anything itself — just reports what it found, leaving the decision of what to do with that list to `cli.py`.

### `core/ollama_manager.py`
Checks whether Ollama's API is already reachable at `localhost:11434`. If not, spawns `ollama serve` as a background process with `OLLAMA_MODELS` pointed at the actual model storage location, and waits until the API responds before continuing. Only stops the process it started itself — if Ollama was already running some other way, it's left alone. This means Ollama no longer needs to run as an always-on background service; it starts only while a query is in progress and shuts down right after.

### `core/load.py`
Takes a filepath and loads it into an **in-memory DuckDB database** as a table named `data`. CSVs are read directly using DuckDB's `read_csv_auto`, which infers column types automatically (so a date column comes through as `DATE`, not text). Excel files are read via `pandas.read_excel` and registered into DuckDB as a queryable table. Returns the live DuckDB connection so the rest of the pipeline can query it.

### `core/schema.py`
Given a DuckDB connection, runs `DESCRIBE` on the table to get every column's name and type, then pulls up to 5 distinct sample values per column. This schema — types *and* real sample values — is what gets handed to the LLM later, which is what lets it correctly infer things like "total sales" meaning `price * quantity`, or know that `region` actually contains values like `North`/`South`, not something it has to guess at.

### `core/correct.py`
Takes the user's raw question and the schema, and asks the LLM to fix spelling mistakes while explicitly telling it the real column names and known values in the dataset. This prevents the correction step from "fixing" a real term (like a category name) into something wrong, since the model is told what's actually valid. Returns the cleaned-up question, which is what actually gets used to build the SQL prompt.

### `core/prompt.py`
Builds the exact text sent to the LLM: the table name, a formatted list of columns with types and sample values, a short set of hard rules (SELECT-only, only use listed columns, respond with `CANNOT_ANSWER: <reason>` if the question needs data that doesn't exist), and the question itself. This is the single place that controls how the LLM is instructed — nearly all prompt tuning happens here.

### `core/generator.py`
Sends the prompt to Ollama's local API (`qwen3:8b` by default) with `think: false`, since qwen3 is a hybrid "thinking" model that can otherwise emit internal reasoning before its answer. Also strips any leftover `<think>...</think>` blocks or markdown code fences as a safety net, in case the model doesn't fully honor the `think: false` flag. Returns clean, ready-to-parse SQL text.

### `core/validator.py`
Parses the generated SQL with `sqlglot` (targeting the DuckDB dialect) and checks three things before anything is allowed to run: that it parsed as valid SQL at all, that it's a `SELECT` statement (never `INSERT`/`UPDATE`/`DELETE`/`DROP`), and that every column referenced actually exists in the real schema — while correctly ignoring column aliases the query defines for itself (like `AS total_quantity` reused in an `ORDER BY`), so it doesn't flag its own aliases as unknown columns.

### `core/executor.py`
Takes a validated SQL string and the DuckDB connection, executes it, and returns the result as a pandas DataFrame — or a clean error message if execution fails for some other reason (e.g. a runtime type mismatch that validation didn't catch).

### `core/exporter.py`
Takes a result DataFrame and a target filepath, and writes it out as CSV or Excel based on the file extension. Deliberately has no idea where that filepath came from — it doesn't ask the user anything itself, it just saves.

### `cli.py`
The entry point. Wires every module above into one command:
```bash
nl2sql                        # fully interactive
nl2sql <file>                  # question still prompted for
nl2sql <file> "<question>"      # fully explicit, original style
```
It resolves the file (auto-discovering or prompting if not given), resolves the question (prompting if not given), starts Ollama if needed, loads the file, extracts the schema, corrects the question, builds the prompt, generates SQL, checks for `CANNOT_ANSWER`, validates the SQL (retrying once if invalid), executes it, prints both the generated SQL (syntax-highlighted via Rich) and the result table, optionally saves the result to a file, and stops Ollama if this run was the one that started it.

---

## Setup

**Requirements:** Python 3.10+, [Ollama](https://ollama.com) installed (no need to keep it running — `nl2sql` manages that itself), [pipx](https://pipx.pypa.io) for a global install.

```bash
# Clone the repo
git clone https://github.com/Vishnudrm/nl2sql.git
cd nl2sql

# Pull the model this tool uses
ollama pull qwen3:8b

# Install nl2sql as a global command
pipx install -e .
```

That's it — no venv to activate, no `cd`-ing into the project directory afterward. `nl2sql` is now on your PATH everywhere.

*(If you'd rather run it inside a plain virtual environment instead of pipx: `python3 -m venv venv && source venv/bin/activate && pip install -e .` works the same way, but the command only exists while that venv is active.)*

## Usage

The simplest way to use it — just run it from a folder with your data:

```bash
cd wherever/your/data/is
nl2sql
```

It'll find your file (or ask which one, if there's more than one), ask what you want to know, and offer to save the result when it's done.

You can still be explicit if you prefer:
```bash
nl2sql examples/sample_sales.csv "show me total sales by category"
nl2sql examples/sample_sales.csv "electronics orders in the north or south region"
nl2sql examples/sample_sales.csv "what's the best selling product"
```

## Example Walkthrough

Given `examples/sample_sales.csv` (order_id, product, category, price, quantity, order_date, region), run from inside `examples/`:

```bash
$ nl2sql

Using sample_sales.csv (only data file found here)
What do you want to know: shwo me toatl sales by categry

Interpreted as: "Show me total sales by category"

Generated SQL:
SELECT category, SUM(price * quantity) AS total_sales
FROM data
GROUP BY category;

Result:
   category  total_sales
Electronics      71600.0
 Stationery        850.0
  Furniture       7700.0

Save these results to a file? [y/N]: y
Format (csv/excel) [csv]: excel
Filename (without extension) [results]: category_totals
Save location (directory) [.]: .
Saved to category_totals.xlsx
```

Notice the typo-riddled input ("shwo", "toatl", "categry") gets corrected and shown back to you before the query is even built — so you always know exactly what question was actually answered.

---

## Current State

What's built and working right now:

- ✅ Load CSV files into DuckDB with automatic type inference
- ✅ Basic Excel (`.xlsx`) loading via pandas
- ✅ Schema extraction (column names, types, sample distinct values)
- ✅ Typo correction using schema-aware LLM prompting
- ✅ Schema-aware SQL generation via a local LLM (qwen3:8b through Ollama)
- ✅ SQL validation: SELECT-only enforcement, unknown-column detection, alias-aware checking
- ✅ Graceful `CANNOT_ANSWER` handling when a question references data that doesn't exist
- ✅ One automatic retry when the first generated query fails validation
- ✅ Query execution against DuckDB with clean error handling
- ✅ CLI interface with syntax-highlighted SQL output (via Typer + Rich)
- ✅ Tested against grouping, filtering, multi-condition (AND/OR), date-range, and ranking questions
- ✅ **Global CLI install** — packaged with `pyproject.toml`, installable via `pipx install -e .`, callable as `nl2sql` from any directory, no venv activation needed
- ✅ **Auto-discovery of data files** — no file given? Automatically uses the one CSV/Excel file in the current directory, or lists all of them and asks which one to use
- ✅ **Fully interactive mode** — running `nl2sql` with no arguments at all prompts for both the file and the question
- ✅ **On-demand Ollama lifecycle** — Ollama starts automatically right before a query needs it (only if it isn't already running) and shuts itself down again afterward, instead of running as an always-on background service
- ✅ **Export results** — after a query, optionally save the result table straight to a new CSV or Excel file, with prompts for format, filename, and save location

This is a fully working end-to-end pipeline, usable from anywhere on the machine.

---

## Roadmap — What's Left to Build

- [ ] **Excel edge cases** — handle multi-sheet workbooks explicitly (currently defaults to the first sheet; needs a `--sheet` flag or a prompt when more than one sheet exists)
- [ ] **Multi-file support (opt-in)** — support querying across more than one file in a single question, as an explicit opt-in mode rather than silent automatic joining, since inferring join keys between unrelated files is where these tools tend to get unreliable
- [ ] **Interactive/REPL mode** — a `nl2sql chat <file>` mode that keeps a session open, so follow-up questions ("now just electronics") work without re-typing the file path or losing context
- [ ] **Test suite** — formal `pytest` tests for the validator specifically (valid queries, unknown columns, alias handling, disallowed statement types), since that's the component most responsible for the tool's safety and trustworthiness
- [ ] **README polish** — usage GIF/screenshot at the top, now that the CLI is globally installable and fully interactive

---

## License

MIT