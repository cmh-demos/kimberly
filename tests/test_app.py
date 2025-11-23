import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


# Mock Redis for testing
@pytest.fixture
def mock_redis():
    with patch("app.redis_client") as mock_redis:
        yield mock_redis


def test_chat_endpoint_unauthorized():
    response = client.post("/chat", json={"message": "Hello", "user_id": "test"})
    assert response.status_code == 403


def test_login():
    response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_chat_endpoint_authorized(mock_redis):
    # Mock login
    login_response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/chat", json={"message": "Hello", "user_id": "testuser"}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["memory_stored"] == True


def test_store_memory(mock_redis):
    login_response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    memory_data = {
        "content": "Test memory",
        "type": "long-term",
        "metadata": {"tags": ["test"]},
    }
    response = client.post("/memory", json=memory_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert "id" in data


def test_get_memory(mock_redis):
    # Mock stored memory
    mock_redis.get.return_value = json.dumps(
        {
            "id": "mem_123",
            "user_id": "testuser",
            "type": "long-term",
            "content": "Test memory",
            "size_bytes": 12,
            "metadata": {},
            "score": 0.0,
            "created_at": "2025-11-23T10:00:00",
            "last_seen_at": "2025-11-23T10:00:00",
        }
    )

    login_response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/memory?user_id=testuser&memory_type=long-term", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test memory"


def test_meditation(mock_redis):
    # Mock memories
    mock_redis.scan_iter.return_value = ["memory:testuser:long-term"]
    mock_redis.get.return_value = json.dumps(
        {
            "id": "mem_123",
            "user_id": "testuser",
            "type": "long-term",
            "content": "Test memory",
            "size_bytes": 1024 * 1024 * 3,  # 3MB to trigger pruning
            "metadata": {"tags": ["test"]},
            "score": 0.1,
            "created_at": "2025-11-20T10:00:00Z",
            "last_seen_at": "2025-11-22T10:00:00Z",
        }
    )

    login_response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/meditation?user_id=testuser", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "to_prune" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_agent_delegation():
    login_response = client.post(
        "/token", json={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    task_data = {
        "type": "schedule",
        "description": "Test task",
        "parameters": {"time": "2025-11-25T14:00:00Z"},
    }
    response = client.post("/agent", json=task_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "task_id" in data


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_rate_limiting():
    # Test rate limiting (would need multiple requests in quick succession)
    # For now, just ensure endpoint exists
    response = client.post("/chat", json={"message": "Hello"})
    # Should be 403 due to no auth, not rate limited
    assert response.status_code == 403


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Kimberly AI Assistant API"
