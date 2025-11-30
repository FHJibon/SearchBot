import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o"
MAX_TOKENS = 1000
TEMP = 0.4
CSV_PATH = "Data/data.csv"