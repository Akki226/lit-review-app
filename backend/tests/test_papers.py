from unittest.mock import patch

SAMPLE_PAPERS_A = [
    {
        "pmid": "111",
        "title": "Macrophage subsets in Mycobacterium tuberculosis infection",
        "authors": ["Smith A", "Lee B"],
        "journal": "Front Immunol",
        "year": 2023,
        "publication_type": ["Journal Article"],
        "doi": "10.1016/example.111",
        "keywords": ["tuberculosis", "macrophage"],
        "abstract": "Heterogeneity of macrophages during TB.",
        "link": "https://pubmed.ncbi.nlm.nih.gov/111/",
    }
]
SAMPLE_PAPERS_B = [
    {
        "pmid": "111",  # duplicate PMID should be removed
        "title": "Duplicate of first PMID",
        "authors": ["Dup D"],
        "journal": "Duplicate J",
        "year": 2022,
        "publication_type": ["Journal Article"],
        "doi": "10.1016/example.dup",
        "keywords": ["duplicate"],
        "abstract": "Duplicate paper.",
        "link": "https://pubmed.ncbi.nlm.nih.gov/111/",
    },
    {
        "pmid": "222",
        "title": "TB mouse model methods",
        "authors": ["Chan C"],
        "journal": "Methods Mol Biol",
        "year": 2021,
        "publication_type": ["Journal Article"],
        "doi": "10.1016/example.222",
        "keywords": ["tuberculosis", "mouse model"],
        "abstract": "Model-focused paper.",
        "link": "https://pubmed.ncbi.nlm.nih.gov/222/",
    },
]


def test_papers_csv_uses_ai_query_then_pubmed(client, sample_topic):
    sections = [
        {
            "name": "Introduction",
            "query": '("tuberculosis"[Title/Abstract]) AND review[Publication Type]',
            "type": "review",
        },
        {
            "name": "Methods and Models",
            "query": '("tuberculosis"[Title/Abstract]) AND model[Title/Abstract]',
            "type": "research",
        },
    ]
    with (
        patch(
            "app.routes.papers.is_scientific_topic",
            return_value=True,
        ),
        patch(
            "app.routes.papers.extract_keywords",
            return_value=["tuberculosis", "macrophage", "heterogeneity"],
        ) as mock_keywords,
        patch(
            "app.routes.papers.generate_section_queries",
            return_value={"sections": sections},
        ) as mock_sections,
        patch(
            "app.routes.papers.fetch_pubmed_papers",
            side_effect=[SAMPLE_PAPERS_A, SAMPLE_PAPERS_B],
        ) as mock_pubmed,
    ):
        response = client.get("/papers", params={"query": sample_topic})

    assert response.status_code == 200
    mock_keywords.assert_called_once_with(sample_topic)
    mock_sections.assert_called_once_with(sample_topic)
    assert mock_pubmed.call_count == 2
    mock_pubmed.assert_any_call(sections[0]["query"], max_results=10)
    mock_pubmed.assert_any_call(sections[1]["query"], max_results=10)


def test_papers_limit_parameter(client, sample_topic):
    sections = [
        {"name": "Introduction", "query": "tuberculosis review", "type": "review"},
        {"name": "Core Biology", "query": "macrophage tuberculosis", "type": "research"},
    ]
    with (
        patch(
            "app.routes.papers.is_scientific_topic",
            return_value=True,
        ),
        patch(
            "app.routes.papers.extract_keywords",
            return_value=["tuberculosis", "macrophage"],
        ),
        patch(
            "app.routes.papers.generate_section_queries",
            return_value={"sections": sections},
        ),
        patch(
            "app.routes.papers.fetch_pubmed_papers",
            side_effect=[SAMPLE_PAPERS_A, SAMPLE_PAPERS_B],
        ) as mock_pubmed,
    ):
        response = client.get(
            "/papers",
            params={"query": sample_topic, "limit": 5},
        )

    assert response.status_code == 200
    assert mock_pubmed.call_count == 2
    mock_pubmed.assert_any_call(sections[0]["query"], max_results=5)
    mock_pubmed.assert_any_call(sections[1]["query"], max_results=5)

    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition.lower()
    assert "tuberculosis_papers.csv" in disposition
    assert response.headers.get("content-type", "").startswith("text/csv")
    assert response.headers.get("x-keywords") == "tuberculosis,macrophage"

    body = response.text
    assert "PMID,Title,Year,Journal,Authors,PublicationType,DOI,Keywords,Abstract,Section,Link" in body
    assert 'HYPERLINK(""https://pubmed.ncbi.nlm.nih.gov/111/"", ""Macrophage subsets in Mycobacterium tuberculosis infection"")' in body
    assert "111" in body
    assert "Smith A; Lee B" in body
    assert "Front Immunol" in body
    assert "2023" in body
    assert "Journal Article" in body
    assert "10.1016/example.111" in body
    assert "tuberculosis; macrophage" in body
    assert "Heterogeneity of macrophages during TB." in body
    assert "https://pubmed.ncbi.nlm.nih.gov/111/" in body
    assert "Duplicate of first PMID" not in body


def test_papers_json_format_returns_structured_payload(client, sample_topic):
    sections = [
        {"name": "Introduction", "query": "tuberculosis review", "type": "review"},
        {"name": "Core Biology", "query": "macrophage tuberculosis", "type": "research"},
    ]
    with (
        patch(
            "app.routes.papers.is_scientific_topic",
            return_value=True,
        ),
        patch(
            "app.routes.papers.extract_keywords",
            return_value=["tuberculosis", "macrophage"],
        ),
        patch(
            "app.routes.papers.generate_section_queries",
            return_value={"sections": sections},
        ),
        patch(
            "app.routes.papers.fetch_pubmed_papers",
            side_effect=[SAMPLE_PAPERS_A, SAMPLE_PAPERS_B],
        ),
    ):
        response = client.get(
            "/papers",
            params={"query": sample_topic, "format": "json"},
        )

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")
    assert response.headers.get("x-keywords") == "tuberculosis,macrophage"

    payload = response.json()
    assert payload["keywords"] == ["tuberculosis", "macrophage"]
    assert payload["sections"] == sections
    assert isinstance(payload["papers"], list)
    assert len(payload["papers"]) == 2
    assert payload["papers"][0]["pmid"] == "222"
    assert payload["papers"][0]["section"] == "Core Biology"
    assert payload["papers"][1]["pmid"] == "111"
    assert payload["papers"][1]["section"] == "Introduction"


def test_papers_limit_is_final_cap(client, sample_topic):
    sections = [
        {"name": "Introduction", "query": "tuberculosis review", "type": "review"},
        {"name": "Core Biology", "query": "macrophage tuberculosis", "type": "research"},
    ]
    with (
        patch(
            "app.routes.papers.is_scientific_topic",
            return_value=True,
        ),
        patch(
            "app.routes.papers.extract_keywords",
            return_value=["tuberculosis", "macrophage"],
        ),
        patch(
            "app.routes.papers.generate_section_queries",
            return_value={"sections": sections},
        ),
        patch(
            "app.routes.papers.fetch_pubmed_papers",
            side_effect=[SAMPLE_PAPERS_A, SAMPLE_PAPERS_B],
        ),
    ):
        response = client.get(
            "/papers",
            params={"query": sample_topic, "format": "json", "limit": 1},
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["papers"]) == 1
    assert payload["papers"][0]["pmid"] == "222"


def test_papers_missing_query_returns_422(client):
    response = client.get("/papers")
    assert response.status_code == 422


def test_papers_non_scientific_topic_returns_422(client):
    with patch(
        "app.routes.papers.is_scientific_topic",
        return_value=False,
    ):
        response = client.get("/papers", params={"query": "lol random stuff"})
    assert response.status_code == 422
