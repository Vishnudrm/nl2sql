import requests

def correct_question(question: str, schema_info: list, model="qwen3:8b") -> str:
    known_values = []
    for col in schema_info:
        known_values.extend(str(v) for v in col["sample_values"])

    prompt = f"""Fix any typos or spelling mistakes in this question. Keep the meaning and intent exactly the same. Do not add or remove information, just correct spelling.

Known valid terms in this dataset (column names and sample values): {', '.join(known_values)}

Question: {question}

Corrected question (return ONLY the corrected text, nothing else, no explanation):"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False
        }
    )
    corrected = response.json()["response"].strip()
    corrected = corrected.strip('"').strip("'")
    return corrected