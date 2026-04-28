import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLE_TOPIC = "macrophage heterogeneity in tuberculosis"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_topic() -> str:
    return SAMPLE_TOPIC
