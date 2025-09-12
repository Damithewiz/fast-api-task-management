"""
End-to-end tests for the FastAPI to-do app using FastAPI's TestClient.
"""

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import main
from fastapi.testclient import TestClient
import pytest
import re

# Create one client for all tests
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_in_memory_store():
    """
    Automatically run before each test.
    Clears the in-memory database and resets the auto-incrementing ID.
    """
    main._tasks.clear()
    main._next_id = 1
    yield

def test_list_tasks_initially_empty():
    res = client.get("/tasks")
    assert res.status_code == 200
    assert res.json() == []


def test_create_task_and_get_it_back():
    # Create a new task
    payload = {"title": "Buy milk", "description": "2 litres", "completed": False}
    res = client.post("/tasks", json=payload)
    assert res.status_code == 201
    data = res.json()

    # Basic shape checks
    assert data["id"] == 1
    assert data["title"] == "Buy milk"
    assert data["description"] == "2 litres"
    assert data["completed"] is False

    assert isinstance(data["created_at"], str)
    assert re.search(r"Z$|\+00:00$", data["created_at"])

    # Now fetch via GET /tasks/1
    res2 = client.get("/tasks/1")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["id"] == 1
    assert data2["title"] == "Buy milk"


def test_create_defaults_completed_false_when_omitted():
    # completed is optional in TaskCreate and should default to False
    payload = {"title": "Walk dog", "description": "Evening walk"}
    res = client.post("/tasks", json=payload)
    assert res.status_code == 201
    assert res.json()["completed"] is False


def test_update_task_partial_fields_only():
    # Seed a task
    client.post("/tasks", json={"title": "Study", "description": "Ch. 1", "completed": False})

    # Update just 'completed'
    res = client.put("/tasks/1", json={"completed": True})
    assert res.status_code == 200
    updated = res.json()
    assert updated["completed"] is True
    assert updated["title"] == "Study"          # unchanged
    assert updated["description"] == "Ch. 1"    # unchanged


def test_delete_task_and_404_afterwards():
    # Seed
    client.post("/tasks", json={"title": "Trash", "description": "Take out", "completed": False})

    # Delete it
    res = client.delete("/tasks/1")
    assert res.status_code == 204
    assert res.text == ""  # 204 No Content

    # Now it should be gone
    res2 = client.get("/tasks/1")
    assert res2.status_code == 404
    assert "not found" in res2.json()["detail"].lower()


def test_get_missing_returns_404():
    res = client.get("/tasks/999")
    assert res.status_code == 404


def test_validation_errors_422_on_bad_input():
    # Empty title should fail (min_length=1)
    res = client.post("/tasks", json={"title": "", "description": "oops"})
    assert res.status_code == 422

    # Title too long should fail (max_length=200)
    long_title = "x" * 201
    res2 = client.post("/tasks", json={"title": long_title})
    assert res2.status_code == 422
