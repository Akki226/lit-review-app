import time
from typing import Any

from Bio import Entrez, Medline

Entrez.email = "placeholder@example.com"
Entrez.tool = "lit-review-app"


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _single_str(value: Any) -> str:
    parts = _as_str_list(value)
    return parts[0] if parts else ""


def _year_from_dp(dp: Any) -> int | None:
    if not dp:
        return None
    text = str(dp).strip()
    if len(text) >= 4 and text[:4].isdigit():
        y = int(text[:4])
        if 1800 <= y <= 2100:
            return y
    return None


def _doi_from_record(record: dict[str, Any]) -> str:
    for aid in _as_str_list(record.get("AID")):
        if "[doi]" in aid.lower():
            return aid.split(" ", 1)[0].strip()
    lid = _single_str(record.get("LID"))
    if lid and "[doi]" in lid.lower():
        return lid.split(" ", 1)[0].strip()
    return ""


def fetch_pubmed_papers(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    with Entrez.esearch(db="pubmed", term=query, retmax=max_results) as search_handle:
        search_record = Entrez.read(search_handle)

    id_list = search_record.get("IdList", [])
    if not id_list:
        return []

    time.sleep(0.35)

    with Entrez.efetch(
        db="pubmed",
        id=",".join(id_list),
        rettype="medline",
        retmode="text",
    ) as fetch_handle:
        records = list(Medline.parse(fetch_handle))

    papers: list[dict[str, Any]] = []
    for record in records:
        pmid = _single_str(record.get("PMID"))
        journal = record.get("JT") or record.get("TA") or ""
        if isinstance(journal, list):
            journal = journal[0] if journal else ""

        papers.append(
            {
                "pmid": pmid,
                "title": _single_str(record.get("TI")),
                "authors": _as_str_list(record.get("AU")),
                "journal": str(journal),
                "year": _year_from_dp(record.get("DP")),
                "publication_type": _as_str_list(record.get("PT")),
                "doi": _doi_from_record(record),
                "keywords": _as_str_list(record.get("OT") or record.get("MH")),
                "abstract": _single_str(record.get("AB")),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            }
        )

    return papers
