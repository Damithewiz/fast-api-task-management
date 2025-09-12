# Simple Task Management API (FastAPI)

A minimal FastAPI app for a to-do list using in-memory storage.

## Features
- Endpoints:
  - `GET /tasks` — list all tasks
  - `POST /tasks` — create a task
  - `GET /tasks/{task_id}` — fetch a task by ID
  - `PUT /tasks/{task_id}` — update a task (partial or full)
  - `DELETE /tasks/{task_id}` — delete a task
- Pydantic models for validation & typed responses
- In-memory store (no database)
- Type hints throughout
- Basic error handling (`404` on missing tasks, `422` on invalid input)

## Requirements
- Python 3.9+
- FastAPI
- Uvicorn
- Pytest (for tests)

## What the tests cover
- Empty list initially
- Create → read back (including created_at format)
- Default values (completed defaults to False)
- Partial updates (only provided fields change)
- Delete flow and subsequent 404
- 404 on missing ID
- Validation (422) for invalid input

## How To Run End-To-End Tests
- Make sure the virtual enviroment is activated
- source .venv/bin/activate
- python -m pytest -q

## Setup
```bash
cd fastapi-todo # Clone the repo or open the folder

python3 -m venv .venv # Create and activate a virtual environment
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

pip install -r requirements.txt # Install dependencies