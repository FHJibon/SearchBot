from fastapi import FastAPI
from app.api.v1.endpoints import search

app = FastAPI(title="AI Search Bot")
app.include_router(search.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Search Bot API"}