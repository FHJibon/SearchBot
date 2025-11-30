import pandas as pd
import requests, json
from app.config import OPENAI_API_KEY, OPENAI_URL, MODEL, MAX_TOKENS, TEMP, CSV_PATH

df = pd.read_csv(CSV_PATH).fillna("")
boat_records = df.to_dict(orient="records")

def ai_search_boats(query: str, top_k: int | None = None):
    prompt = {
        "instructions": "You are a boat search assistant. The user may ask queries. Use the CSV data to find all matching boats.",
        "csv_data": boat_records,
        "user_query": query,
        "top_k": top_k,
        "response_format": "Return JSON only. Include all details of matching boats."
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert boat search assistant."},
            {"role": "user", "content": json.dumps(prompt)}
        ],
        "temperature": TEMP,
        "max_tokens": MAX_TOKENS
    }

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    r = requests.post(OPENAI_URL, headers=headers, json=payload)

    if r.status_code != 200:
        return {"error": f"API returned status {r.status_code}", "details": r.text}

    data = r.json()
    if "choices" not in data or not data["choices"]:
        return {"error": "No choices returned from API", "raw_response": data}

    ai_text = data["choices"][0]["message"]["content"]

    try:
        result = json.loads(ai_text)
    except json.JSONDecodeError:
        return {"result": ai_text}