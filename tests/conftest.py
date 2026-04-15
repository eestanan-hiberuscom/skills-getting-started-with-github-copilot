import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def isolate_activities() -> None:
    """Restore the in-memory database after each test."""
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def sample_signup() -> dict[str, str]:
    return {
        "activity_name": "Chess Club",
        "email": "test.student@mergington.edu",
    }