"""In-memory todo management for the MCP demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Todo:
    id: int
    title: str
    description: str = ""
    completed: bool = False


todos: List[Todo] = []
_next_todo_id = 1


def get_todos() -> List[Todo]:
    return list(todos)


def ensure_seed_todos() -> None:
    if todos:
        return
    add_todo("Prepare AI demo", "Walk through the dashboard experiences.")
    add_todo("Review pull requests", "Focus on chat endpoint changes.")


def add_todo(title: str, description: str = "") -> Todo:
    global _next_todo_id
    todo = Todo(id=_next_todo_id, title=title.strip(), description=description.strip())
    todos.append(todo)
    _next_todo_id += 1
    return todo


def find_todo(todo_id: int) -> Todo | None:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    return None


def update_todo(todo_id: int, title: str, description: str, completed: bool) -> Todo | None:
    todo = find_todo(todo_id)
    if not todo:
        return None
    todo.title = title.strip() or todo.title
    todo.description = description.strip()
    todo.completed = completed
    return todo


def delete_todo(todo_id: int) -> bool:
    todo = find_todo(todo_id)
    if not todo:
        return False
    todos.remove(todo)
    return True


def complete_todo(todo_id: int) -> bool:
    todo = find_todo(todo_id)
    if not todo:
        return False
    todo.completed = True
    return True


def parse_completed_flag(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y", "done", "completed"}

__all__ = [
    "Todo",
    "todos",
    "get_todos",
    "ensure_seed_todos",
    "add_todo",
    "find_todo",
    "update_todo",
    "delete_todo",
    "complete_todo",
    "parse_completed_flag",
]
