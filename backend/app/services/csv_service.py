import io
from typing import Any

import pandas as pd


def _excel_hyperlink(url: str, text: str) -> str:
    safe_url = str(url).replace('"', '""')
    safe_text = str(text).replace('"', '""')
    return f'=HYPERLINK("{safe_url}", "{safe_text}")'


def papers_to_csv(papers: list) -> str:
    rows: list[dict[str, Any]] = []
    for paper in papers:
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            authors_cell = "; ".join(str(a) for a in authors)
        else:
            authors_cell = "" if authors is None else str(authors)
        publication_type = paper.get("publication_type", [])
        if isinstance(publication_type, list):
            publication_type_cell = "; ".join(str(v) for v in publication_type)
        else:
            publication_type_cell = (
                "" if publication_type is None else str(publication_type)
            )
        keywords = paper.get("keywords", [])
        if isinstance(keywords, list):
            keywords_cell = "; ".join(str(v) for v in keywords)
        else:
            keywords_cell = "" if keywords is None else str(keywords)
        link = "" if paper.get("link") is None else str(paper.get("link", ""))
        title = "" if paper.get("title") is None else str(paper.get("title", ""))
        title_cell = _excel_hyperlink(link, title) if link else title
        year_value = paper.get("year", "")
        if isinstance(year_value, int):
            year_sort = year_value
        elif str(year_value).isdigit():
            year_sort = int(str(year_value))
        else:
            year_sort = -1

        rows.append(
            {
                "PMID": paper.get("pmid", ""),
                "Title": title_cell,
                "Year": year_value,
                "Journal": paper.get("journal", ""),
                "Authors": authors_cell,
                "PublicationType": publication_type_cell,
                "DOI": paper.get("doi", ""),
                "Keywords": keywords_cell,
                "Abstract": paper.get("abstract", ""),
                "Section": paper.get("section", ""),
                "Link": link,
                "_year_sort": year_sort,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["Section", "_year_sort"], ascending=[True, False])
    df = df[
        [
            "PMID",
            "Title",
            "Year",
            "Journal",
            "Authors",
            "PublicationType",
            "DOI",
            "Keywords",
            "Abstract",
            "Section",
            "Link",
        ]
    ]
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
