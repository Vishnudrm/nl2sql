def build_prompt(schema_info, table_name, question):
    schema_text = "\n".join(
        f"- {col['column']} ({col['type']}), examples: {col['sample_values']}"
        for col in schema_info
    )
    return f"""You are a SQL generator for DuckDB. Given this table schema, write ONE SQL query to answer the question.

Table: {table_name}
Columns:
{schema_text}

Rules:
- Only use SELECT statements, never INSERT/UPDATE/DELETE/DROP
- Only reference columns listed above
- If the question asks for information that does NOT exist in the columns above (e.g. a field not listed), respond with exactly: CANNOT_ANSWER: <short reason>
- Return ONLY the SQL query, no explanation, no markdown fences, no reasoning

Question: {question}

SQL:"""