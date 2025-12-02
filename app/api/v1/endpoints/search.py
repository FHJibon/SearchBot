from fastapi import APIRouter
from app.services.ai_search import ai_search_boats
from app.schemas.schema import SearchRequest

router = APIRouter()

@router.post("/search", tags=["AI Search"])
async def search(request: SearchRequest):
    result = await ai_search_boats(request.query)
    return result