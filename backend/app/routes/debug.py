"""Development-only helpers (do not expose in production without protection)."""

from fastapi import APIRouter, Query

from app.services.ai_service import generate_pubmed_query

router = APIRouter()


@router.get("/debug-query")
def debug_query(
    topic: str = Query(..., min_length=1, description="Research topic to expand into a PubMed query"),
):
    generated_query = generate_pubmed_query(topic)
    return {"topic": topic, "generated_query": generated_query}
