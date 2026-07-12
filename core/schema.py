def extract_schema(con, table_name: str = "data"):
    columns = con.execute(f"DESCRIBE {table_name}").fetchall()
    schema_info = []
    for col_name, col_type, *_ in columns:
        try:
            sample = con.execute(
                f"SELECT DISTINCT {col_name} FROM {table_name} LIMIT 5"
            ).fetchall()
            sample_values = [s[0] for s in sample]
        except Exception:
            sample_values = []
        schema_info.append({
            "column": col_name,
            "type": col_type,
            "sample_values": sample_values
        })
    return schema_info