import os
import re
import json
from pathlib import Path
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv


def _build_client() -> OpenAI:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def generate_section_queries(topic: str) -> dict[str, list[dict[str, str]]]:
    client = _build_client()
    user_prompt = (
        "Convert the user's topic into a scientifically meaningful PubMed search query. "
        "If the input is vague or general (e.g. 'car', 'science'), expand it into a relevant "
        "biomedical or research-focused query using appropriate keywords.\n\n"
        "Produce section-based PubMed search queries from that interpretation.\n\n"
        f"Topic: {topic.strip()}\n\n"
        "Return STRICT JSON only with this exact shape:\n"
        '{\n'
        '  "sections": [\n'
        '    {"name": "...", "query": "...", "type": "review|research"}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- 4 to 6 sections total\n"
        "- Include: Introduction (review papers)\n"
        "- Include core biology sections\n"
        "- Include methods or models section\n"
        "- Include future directions section\n"
        "- Each query must be a valid PubMed boolean query\n"
        "- query strings only, no explanations, no markdown"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You produce strict JSON for section-based PubMed queries. "
                    "Output only JSON."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = (response.choices[0].message.content or "").strip()
    data = json.loads(raw)
    sections_raw = data.get("sections", [])
    if not isinstance(sections_raw, list):
        raise RuntimeError("Invalid response format from AI: sections must be a list")

    sections: list[dict[str, str]] = []
    for section in sections_raw:
        if not isinstance(section, dict):
            continue
        name = str(section.get("name", "")).strip()
        query = str(section.get("query", "")).strip()
        section_type = str(section.get("type", "research")).strip().lower()
        if not name or not query:
            continue
        if section_type not in {"review", "research"}:
            section_type = "research"
        # Guarantee a usable PubMed query even if model returns vague/empty text.
        query = query.strip()
        if not query:
            continue
        if not any(op in query for op in (" AND ", " OR ", " NOT ")):
            query = f"({query}) AND (biomedical OR research)"
        sections.append({"name": name, "query": query, "type": section_type})

    if not 4 <= len(sections) <= 6:
        raise RuntimeError("AI returned an invalid number of sections (expected 4-6)")

    return {"sections": sections}


def generate_pubmed_query(topic: str) -> str:
    section_data = generate_section_queries(topic)
    sections = section_data.get("sections", [])
    if not sections:
        raise RuntimeError("No section queries generated")
    return sections[0]["query"]


def extract_keywords(topic: str) -> list[str]:
    client = _build_client()
    user_prompt = (
        "Extract 3-5 main scientific keywords from this research topic.\n\n"
        f"Topic: {topic.strip()}\n\n"
        "Return only keywords, no explanation. Prefer short clean terms. "
        "Use a comma-separated list."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract concise scientific keywords. "
                    "Return exactly 3-5 terms as a comma-separated list."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw = (response.choices[0].message.content or "").strip()
    parts = re.split(r"[,\n;]+", raw)
    keywords: list[str] = []
    seen: set[str] = set()
    for part in parts:
        term = part.strip().strip(".").strip('"').strip("'").lower()
        if not term:
            continue
        if term in seen:
            continue
        seen.add(term)
        keywords.append(term)
        if len(keywords) == 5:
            break
    return keywords


def is_scientific_topic(topic: str) -> bool:
    client = _build_client()
    user_prompt = (
        "Determine whether this topic is scientific/academic enough for biomedical "
        f"literature search.\n\nTopic: {topic.strip()}\n\n"
        'Return strict JSON: {"is_scientific": true|false}'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict classifier for scientific search relevance. "
                    "Only output JSON."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = (response.choices[0].message.content or "").strip()
    data = json.loads(raw)
    return bool(data.get("is_scientific", False))
