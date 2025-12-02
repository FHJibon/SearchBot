import json
import aiosqlite
import os
import httpx
from app.config import OPENAI_API_KEY, OPENAI_URL, MODEL, MAX_TOKENS, TEMP, CSV_PATH

SQLITE_DB = "Data/Data.db"

def _load_csv_header(csv_path):
    import pandas as pd
    try:
        df_header = pd.read_csv(csv_path, nrows=0)
        return list(df_header.columns)
    except Exception:
        return []

def _init_sqlite_db(csv_path, db_path):
    import pandas as pd
    import sqlite3
    if not os.path.exists(db_path):
        df = pd.read_csv(csv_path).fillna("")
        conn = sqlite3.connect(db_path)
        df.to_sql("boats", conn, index=False, if_exists="replace")
        conn.close()

async def _query_sqlite_async(query, params=(), limit=100):
    async with aiosqlite.connect(SQLITE_DB) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(query + f" LIMIT {limit}", params) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

_init_sqlite_db(CSV_PATH, SQLITE_DB)

CSV_HEADER = _load_csv_header(CSV_PATH)

async def ai_search_boats(query, top_k=None):
    count_sql = "SELECT COUNT(*) as cnt FROM boats"
    count_rows = await _query_sqlite_async(count_sql, (), limit=1)
    total = count_rows[0]["cnt"] if count_rows else 0
    max_rows = 3000
    if total > max_rows:
        return {
            "error": f"Too many rows in database ({total}). Please filter or reduce dataset size.",
            "details": "Sending all rows to the LLM is not practical."
        }

    sql = "SELECT * FROM boats"
    all_rows = await _query_sqlite_async(sql, (), limit=max_rows)

    instructions = (
        "You are a boat search assistant. The user may ask queries about boats, "
        "their specifications, pricing, and other attributes.\n\n"
        "You have access to a dataset with the following column names:\n"
        f"{CSV_HEADER}\n\n"
        "Here is the full data (each item is a row):\n"
        f"{json.dumps(all_rows, ensure_ascii=False)}\n\n"
        "Your job:\n"
        "1. Read the user's query and semantically search the provided data for all relevant matches.\n"
        "2. Decide which subset of columns is most relevant to the user's query.\n"
        "3. Return a concise JSON response using ONLY those relevant columns and real data.\n"
        "4. Do not include unnecessary columns or verbose text. Use as few tokens as possible while still answering the query helpfully.\n"
        "5. If the user specifies a number of results or if 'top_k' is provided, respect that as the maximum number of items to include.\n"
        "6. The final answer MUST be valid JSON and nothing else (no prose).\n"
        "7. If the data does not contain a match, return an empty list."
    )

    prompt_payload = {
        "instructions": instructions,
        "csv_header": CSV_HEADER,
        "csv_sample": all_rows,
        "user_query": query,
        "top_k": top_k,
        "response_format": (
            "Return JSON only. Include all fields that are relevant to the "
            "user's query, but avoid irrelevant columns to minimize tokens."
        ),
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert boat search assistant. "
                           "Always return strictly valid JSON.",
            },
            {
                "role": "user",
                "content": json.dumps(prompt_payload),
            },
        ],
        "temperature": TEMP,
        "max_tokens": MAX_TOKENS,
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENAI_URL, headers=headers, json=payload)
    except Exception as e:
        return {
            "error": "Failed to call LLM API",
            "details": str(e),
        }

    if response.status_code != 200:
        return {
            "error": f"API returned status {response.status_code}",
            "details": response.text,
        }

    data: Dict[str, Any] = response.json()

    if "choices" not in data or not data["choices"]:
        return {
            "error": "No choices returned from API",
            "raw_response": data,
        }

    ai_text: str = data["choices"][0]["message"]["content"]

    def _strip_code_block(text: str) -> str:
        if text.strip().startswith("```"):
            lines = text.strip().splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text.strip()

    cleaned_text = _strip_code_block(ai_text)

    try:
        parsed = json.loads(cleaned_text)
        return parsed
    except json.JSONDecodeError:
        return {
            "result": ai_text,
            "warning": "Model response was not valid JSON. Returned raw text instead.",
        }