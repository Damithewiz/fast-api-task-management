from __future__ import annotations  # future-proof typing 

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel, Field

app = FastAPI(
    title= "Simple Task Management API",
    version= "1.0.0",
    description= "A small FastAPI app that manages a to-do list using in-memory storage.",
)


# Request models are seperated from Response models and this keeps concerns clear and lets us apply different validation rules.
class TaskBase(BaseModel):
    """
    Fields shared by multiple models (title, description).
    We validate title is not empty and cap lengths for sanity.
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class TaskCreate(TaskBase):
    """
    Model for creating a new task.
    - 'completed' defaults to False (new tasks start incomplete).
    """
    completed: bool = False


class TaskUpdate(BaseModel):
    """
    Model for updating an existing task (PUT).
    We allow partial updates by making fields Optional.
    Only fields provided by the client will be changed.
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: Optional[bool] = None


class Task(TaskBase):
    """
    Model returned to clients.
    Includes server-managed fields (id, created_at).
    """
    id: int
    completed: bool
    created_at: datetime


# An in-memory "database" where a simple dict maps task_id -> Task
_tasks: Dict[int, Task] = {}
_next_id: int = 1  # auto-incrementing ID counter


def _now_utc() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _get_next_id() -> int:
    """Return the next integer ID and increment the counter."""
    global _next_id
    _id = _next_id
    _next_id += 1
    return _id


def _get_task_or_404(task_id: int) -> Task:
    """
    Helper to fetch a task or raise a 404 error.
    Keeping this logic in one place avoids duplication in route handlers.
    """
    task = _tasks.get(task_id)
    if task is None:
        # FastAPI automatically serializes HTTPException detail to JSON.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return task


# Routes / Endpoints
@app.get(
    "/tasks",
    response_model=List[Task],
    summary="Return all tasks",
    tags=["Tasks"],
)
def list_tasks() -> List[Task]:
    """
    Return all tasks currently stored in memory.
    FastAPI uses the response_model to validate/serialize the output.
    """
    return list(_tasks.values())


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    tags=["Tasks"],
)
def create_task(payload: TaskCreate) -> Task:
    """
    Create a new task from the client-provided payload.
    - We assign an auto-incrementing ID.
    - We set created_at to current UTC time.
    """
    task_id = _get_next_id()
    task = Task(
        id=task_id,
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        created_at=_now_utc(),
    )
    _tasks[task_id] = task
    return task


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get a specific task",
    tags=["Tasks"],
)
def get_task(task_id: int) -> Task:
    """
    Fetch a single task by ID.
    Returns 404 if not found (via helper).
    """
    return _get_task_or_404(task_id)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task",
    tags=["Tasks"],
)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    """
    Update an existing task.
    We support partial updates with PUT for simplicity in this take-home test.
    Only fields explicitly provided in the request will be changed.
    """
    existing = _get_task_or_404(task_id)

    # Convert the existing Task to a dict we can modify
    update_data = existing.model_dump()

    # Apply only provided fields; leave the rest unchanged
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.completed is not None:
        update_data["completed"] = payload.completed

    # Re-validate through the Task model to keep types consistent
    updated = Task(**update_data)
    _tasks[task_id] = updated
    return updated


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    tags=["Tasks"],
    response_class=Response,   # <— ensure no JSON body is produced
)
def delete_task(task_id: int) -> Response:
    """
    Delete a task by id. Returns 204 with an empty body.
    """
    _get_task_or_404(task_id)  # 404 if not found
    del _tasks[task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)