import duckdb
import pandas as pd

def load_file(filepath: str, table_name: str = "data"):
    con = duckdb.connect(database=":memory:")
    if filepath.endswith(".csv"):
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{filepath}')")
    elif filepath.endswith((".xlsx", ".xls")):
        df = pd.read_excel(filepath)
        con.register(table_name, df)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")
    return con