from app.services.csv_service import papers_to_csv


def test_papers_to_csv_columns_and_authors_joined():
    papers = [
        {
            "pmid": "12345678",
            "title": "TB macrophage paper",
            "section": "Introduction",
            "authors": ["One A", "Two B"],
            "journal": "J Leukoc Biol",
            "year": 2022,
            "publication_type": ["Review"],
            "doi": "10.1000/example.doi",
            "keywords": ["tuberculosis", "macrophage", "heterogeneity"],
            "abstract": "macrophage heterogeneity in tuberculosis models",
            "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        }
    ]
    csv_str = papers_to_csv(papers)
    lines = csv_str.strip().splitlines()
    assert lines[0] == "PMID,Title,Year,Journal,Authors,PublicationType,DOI,Keywords,Abstract,Section,Link"
    assert "12345678" in lines[1]
    assert 'HYPERLINK(""https://pubmed.ncbi.nlm.nih.gov/12345678/"", ""TB macrophage paper"")' in lines[1]
    assert "Introduction" in lines[1]
    assert "One A; Two B" in lines[1]
    assert "Review" in lines[1]
    assert "10.1000/example.doi" in lines[1]
    assert "tuberculosis; macrophage; heterogeneity" in lines[1]
    assert "macrophage heterogeneity in tuberculosis models" in csv_str
    assert "https://pubmed.ncbi.nlm.nih.gov/12345678/" in csv_str


def test_papers_to_csv_sorted_by_section_then_year_desc():
    papers = [
        {
            "pmid": "2",
            "title": "Older intro paper",
            "section": "Introduction",
            "authors": ["B"],
            "journal": "J2",
            "year": 2021,
            "publication_type": ["Review"],
            "doi": "",
            "keywords": ["tb"],
            "abstract": "older",
            "link": "https://pubmed.ncbi.nlm.nih.gov/2/",
        },
        {
            "pmid": "1",
            "title": "Newer intro paper",
            "section": "Introduction",
            "authors": ["A"],
            "journal": "J1",
            "year": 2024,
            "publication_type": ["Review"],
            "doi": "",
            "keywords": ["tb"],
            "abstract": "newer",
            "link": "https://pubmed.ncbi.nlm.nih.gov/1/",
        },
        {
            "pmid": "3",
            "title": "Methods paper",
            "section": "Methods",
            "authors": ["C"],
            "journal": "J3",
            "year": 2023,
            "publication_type": ["Journal Article"],
            "doi": "",
            "keywords": ["model"],
            "abstract": "methods",
            "link": "https://pubmed.ncbi.nlm.nih.gov/3/",
        },
    ]
    csv_str = papers_to_csv(papers)
    lines = csv_str.strip().splitlines()
    assert "Newer intro paper" in lines[1]
    assert "Older intro paper" in lines[2]
    assert "Methods paper" in lines[3]
