import logging
import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.ai_service import (
    extract_keywords,
    generate_section_queries,
    is_scientific_topic,
)
from app.services.csv_service import papers_to_csv
from app.services.pubmed_service import fetch_pubmed_papers

logger = logging.getLogger(__name__)

router = APIRouter()


def _slug_keyword(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "papers"


def _year_sort_value(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text) if text.isdigit() else -1


def _sort_papers(papers: list[dict]) -> list[dict]:
    return sorted(
        papers,
        key=lambda p: (
            str(p.get("section", "")),
            -_year_sort_value(p.get("year")),
        ),
    )


@router.get("/papers")
def get_papers(
    query: str = Query(
        ...,
        min_length=1,
        description="Research topic or keywords (converted to a PubMed query by AI)",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=200,
        description="Final number of papers returned after deduplication and sorting",
    ),
    format: Literal["csv", "json"] = Query(
        "csv",
        description="Response format: csv (download) or json (metadata + papers)",
    ),
):
    if not is_scientific_topic(query):
        raise HTTPException(
            status_code=422,
            detail="Please enter a scientific topic related to research/biomedical literature.",
        )

    keywords = extract_keywords(query)
    logger.info("AI-generated keywords: %s", keywords)

    section_data = generate_section_queries(query)
    sections = section_data.get("sections", [])
    if not sections:
        raise RuntimeError("No section queries generated")
    logger.info("AI-generated section queries: %s", sections)

    combined: list[dict] = []
    seen_pmids: set[str] = set()
    for section in sections:
        section_name = str(section.get("name", "")).strip() or "Section"
        section_query = str(section.get("query", "")).strip()
        if not section_query:
            continue
        papers = fetch_pubmed_papers(section_query, max_results=limit)
        for paper in papers:
            pmid = str(paper.get("pmid", "")).strip()
            if pmid:
                if pmid in seen_pmids:
                    continue
                seen_pmids.add(pmid)
            paper_with_section = {**paper, "section": section_name}
            combined.append(paper_with_section)

    final_papers = _sort_papers(combined)[:limit]

    if format == "json":
        return JSONResponse(
            {
                "keywords": keywords,
                "sections": sections,
                "papers": final_papers,
            },
            headers={"X-Keywords": ",".join(keywords)},
        )

    csv_text = papers_to_csv(final_papers)
    csv_bytes = csv_text.encode("utf-8")
    first_keyword = keywords[0] if keywords else "papers"
    filename = f"{_slug_keyword(first_keyword)}_papers.csv"

    def csv_body():
        yield csv_bytes

    return StreamingResponse(
        csv_body(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Keywords": ",".join(keywords),
        },
    )
