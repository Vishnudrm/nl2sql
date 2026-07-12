import sqlglot
from sqlglot import exp

def validate_sql(sql: str, valid_columns: list, valid_table: str = "data"):
    try:
        parsed = sqlglot.parse_one(sql, dialect="duckdb")
    except Exception as e:
        return False, f"SQL parse error: {e}"

    if not isinstance(parsed, exp.Select):
        return False, "Only SELECT statements are allowed"

    defined_aliases = set()
    for select_expr in parsed.expressions:
        if isinstance(select_expr, exp.Alias):
            defined_aliases.add(select_expr.alias)

    used_columns = {col.name for col in parsed.find_all(exp.Column)}
    unknown = used_columns - set(valid_columns) - defined_aliases
    if unknown:
        return False, f"Unknown columns referenced: {unknown}"

    return True, None