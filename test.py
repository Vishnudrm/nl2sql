from core.load import load_file
from core.schema import extract_schema
from core.prompt import build_prompt
from core.generator import generate_sql
from core.validator import validate_sql
from core.executor import execute_sql

con = load_file("examples/sample_sales.csv")
schema_info = extract_schema(con)
valid_columns = [c["column"] for c in schema_info]

question = "show me total sales by category"
prompt = build_prompt(schema_info, "data", question)
sql = generate_sql(prompt)

print("=== Generated SQL ===")
print(sql)

valid, error = validate_sql(sql, valid_columns)
print("\n=== Validation ===")
print(f"Valid: {valid}, Error: {error}")

if valid:
    df, exec_error = execute_sql(con, sql)
    print("\n=== Result ===")
    if df is not None:
        print(df)
    else:
        print(f"Execution error: {exec_error}")