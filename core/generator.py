import requests
import re

def generate_sql(prompt: str, model="qwen3:8b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False
        }
    )
    raw = response.json()["response"].strip()
    return clean_sql(raw)

def clean_sql(raw: str) -> str:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"^```sql\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return raw