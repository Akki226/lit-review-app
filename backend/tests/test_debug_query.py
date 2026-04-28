from unittest.mock import patch


def test_debug_query_returns_topic_and_generated_query(client, sample_topic):
    generated = (
        '("macrophages"[MeSH Terms] OR macrophage[Title/Abstract]) AND '
        '("tuberculosis"[MeSH Terms] OR Mycobacterium tuberculosis[Title/Abstract]) '
        "AND heterogeneity[Title/Abstract]"
    )
    with patch(
        "app.routes.debug.generate_pubmed_query",
        return_value=generated,
    ) as mock_ai:
        response = client.get("/debug-query", params={"topic": sample_topic})

    assert response.status_code == 200
    assert response.json() == {
        "topic": sample_topic,
        "generated_query": generated,
    }
    mock_ai.assert_called_once_with(sample_topic)


def test_debug_query_missing_topic_returns_422(client):
    response = client.get("/debug-query")
    assert response.status_code == 422
