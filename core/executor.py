def execute_sql(con, sql: str):
    try:
        return con.execute(sql).fetchdf(), None
    except Exception as e:
        return None, str(e)