import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Kimberly AI Assistant API"