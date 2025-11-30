from fastapi import APIRouter
from app.services.ai_search import ai_search_boats
from app.schemas.schema import SearchRequest

router = APIRouter()

@router.post("/search")
def search_boats(request: SearchRequest):
    query = request.query
    results = ai_search_boats(query)
    return {"query": query, "results": results}