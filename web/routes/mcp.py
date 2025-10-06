"""Model Context Protocol demo routes."""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from fasthtml.common import (
    A,
    Button,
    Code,
    Details,
    Div,
    Form,
    H1,
    H2,
    H3,
    Img,
    Input,
    Li,
    Main,
    P,
    Pre,
    Summary,
    Textarea,
    Title,
    Ul,
)
from starlette.responses import RedirectResponse

from web.app import rt
from web.services.llm import call_openai
from web.services.todos import (
    Todo,
    add_todo,
    complete_todo,
    delete_todo,
    ensure_seed_todos,
    get_todos,
    parse_completed_flag,
    update_todo,
)
from web.ui.scripts import recording_script
from web.utils.formatting import format_timestamp

mcp_history: List[Dict[str, Any]] = []


def heuristic_command(message: str) -> str:
    lower = message.lower()
    words = lower.split()

    for token in words:
        if token.isdigit():
            todo_id = token
            break
    else:
        todo_id = ""

    if "delete" in lower or "remove" in lower:
        return f"DELETE|{todo_id}" if todo_id else "NOOP|Could not determine todo to delete."
    if "complete" in lower or "done" in lower:
        return f"COMPLETE|{todo_id}" if todo_id else "NOOP|Could not determine todo to complete."
    if "update" in lower:
        return "NOOP|Provide structured update instructions."

    if "add" in lower or "create" in lower or "new" in lower:
        return f"CREATE|{message.title()}|"

    return "NOOP|I was unable to understand the request."


def process_mcp_command(message: str) -> str:
    todos_snapshot = get_todos()
    context = "\n".join(
        [
            f"ID {todo.id}: {todo.title} - {todo.description or 'No description'}"
            + (" (completed)" if todo.completed else "")
            for todo in todos_snapshot
        ]
    ) or "No todos yet."

    prompt = f"""Current todos:
{context}

User command: {message}

You are a todo assistant. Respond with one command using this format:
CREATE|title|description
UPDATE|id|title|description|completed
DELETE|id
COMPLETE|id
"""

    response = call_openai(
        [
            {"role": "system", "content": "You translate natural language into todo commands."},
            {"role": "user", "content": prompt},
        ]
    ).strip()

    if "|" not in response:
        response = heuristic_command(message)
    return response


def execute_mcp_action(command: str) -> str:
    parts = [part.strip() for part in command.split("|")]
    if not parts:
        return "No action returned."

    action = parts[0].upper()

    if action == "CREATE" and len(parts) >= 2:
        title = parts[1]
        description = parts[2] if len(parts) >= 3 else ""
        todo = add_todo(title, description)
        return f"Created todo #{todo.id}: {todo.title}."

    if action == "UPDATE" and len(parts) >= 5 and parts[1].isdigit():
        todo_id = int(parts[1])
        updated = update_todo(todo_id, parts[2], parts[3], parse_completed_flag(parts[4]))
        return f"Updated todo #{todo_id}." if updated else f"Todo #{todo_id} not found."

    if action == "DELETE" and len(parts) >= 2 and parts[1].isdigit():
        todo_id = int(parts[1])
        return "Deleted todo." if delete_todo(todo_id) else f"Todo #{todo_id} not found."

    if action == "COMPLETE" and len(parts) >= 2 and parts[1].isdigit():
        todo_id = int(parts[1])
        return "Marked todo as complete." if complete_todo(todo_id) else f"Todo #{todo_id} not found."

    if action == "NOOP" and len(parts) >= 2:
        return parts[1]

    return f"Unrecognised command: {command}"


@rt("/mcp")
def mcp_page():
    ensure_seed_todos()
    todos_snapshot = get_todos()
    return (
        Title("MCP Todo Manager"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                H1("MCP Todo Manager", cls="text-3xl font-bold text-center mb-2"),
                P(
                    "Model Context Protocol demo for natural language todo management."
                    " Prompts are translated into structured commands before execution.",
                    cls="text-gray-600 text-center mb-4 max-w-2xl mx-auto",
                ),
                Div(
                    Div(
                        Img(
                            src="/mcp-logo",
                            alt="Model Context Protocol logo",
                            cls="h-24 mx-auto mb-4 drop-shadow-sm",
                        ),
                        cls="flex justify-center",
                    ),
                    H2("How MCP servers fit in", cls="text-xl font-semibold mb-2"),
                    P(
                        "MCP servers expose tools, data sources, and prompts that a host application can call "
                        "via a shared JSON-RPC interface. They usually run as separate processes (often over stdio) "
                        "so any language can implement one.",
                        cls="text-gray-600 mb-2",
                    ),
                    Ul(
                        Li(
                            "Hosts discover server capabilities (tools, resources, prompts) at startup and request calls on demand.",
                        ),
                        Li(
                            "Servers keep business logic and credentials outside the host, while still giving the model structured access.",
                        ),
                        Li(
                            "You can register multiple servers with a single host to compose different data domains.",
                        ),
                        cls="list-disc list-inside text-gray-600 mb-2",
                    ),
                    P(
                        "Learn more about building and running servers in the Model Context Protocol getting started guide. ",
                        A(
                            "Read the docs",
                            href="https://modelcontextprotocol.io/docs/getting-started/intro",
                            cls="text-blue-600 hover:text-blue-800",
                        ),
                        cls="text-gray-600",
                    ),
                    cls="bg-white shadow-sm border border-gray-200 rounded-lg p-4 mb-6 text-left",
                ),
                Details(
                    Summary(
                        "View Sample Code",
                        cls="cursor-pointer text-blue-600 hover:text-blue-800 font-semibold",
                    ),
                    Pre(
                        Code(
                            '''def process_mcp_command(message: str) -> str:
    todos = get_todos()
    context = "\n".join(
        [f"ID {todo.id}: {todo.title} - {todo.description}" for todo in todos]
    ) or "No todos yet."

    prompt = f"""Current todos:\n{context}\n\nUser command: {message}\n\nYou are a todo assistant. Respond with one command using this format:\nCREATE|title|description\nUPDATE|id|title|description|completed\nDELETE|id\nCOMPLETE|id\n"""

    response = call_openai([
        {"role": "system", "content": "You translate natural language into todo commands."},
        {"role": "user", "content": prompt},
    ]).strip()

    if "|" not in response:
        response = heuristic_command(message)
    return response
''',
                            cls="language-python",
                        ),
                        cls="bg-gray-100 p-4 rounded text-sm overflow-x-auto",
                    ),
                    cls="mb-6",
                ),
                cls="py-8",
            ),
            Div(
                *[
                    Div(
                        Div(
                            Div(
                                "⚙️" if msg["role"] == "assistant" else "👤",
                                cls="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-lg mr-3",
                            ),
                            Div(
                                Div(
                                    msg["content"],
                                    cls="mb-1 bg-white rounded-2xl px-4 py-2 shadow-sm",
                                ),
                                Div(
                                    format_timestamp(msg["timestamp"])
                                    if "timestamp" in msg
                                    else "",
                                    cls="text-xs text-gray-400 px-4",
                                ),
                                cls="flex-1",
                            ),
                            cls=f"flex {'flex-row-reverse' if msg['role'] == 'user' else 'flex-row'}",
                        ),
                        cls=f"mb-4 {'ml-12' if msg['role'] == 'user' else 'mr-12'}",
                    )
                    for msg in mcp_history
                ],
                id="mcp-container",
                cls="bg-gray-50 rounded-lg shadow-lg p-6 mb-4 min-h-96",
            ),
            Div(
                Form(
                    Div(
                        Textarea(
                            name="message",
                            placeholder="Teach the MCP host what to do...",
                            cls="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                            rows=3,
                        ),
                        cls="mb-2",
                    ),
                    Div(
                        Button(
                            "Send",
                            type="submit",
                            cls="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700",
                        ),
                        Button(
                            "🎤 Voice Input",
                            type="button",
                            cls="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600",
                            onclick="startRecording(this)",
                        ),
                        A(
                            "Clear MCP",
                            href="/mcp/clear",
                            cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
                        ),
                        cls="flex gap-2",
                    ),
                    action="/mcp/send",
                    method="post",
                ),
                cls="mb-4",
            ),
            Div(
                H2("Current Todos", cls="text-2xl font-semibold text-gray-800 mb-3"),
                Div(
                    *[
                        Div(
                            Div(
                                H3(todo.title, cls="text-lg font-semibold text-gray-800"),
                                P(
                                    f"ID {todo.id}"
                                    + (" – completed" if todo.completed else ""),
                                    cls="text-xs uppercase tracking-wide text-gray-500",
                                ),
                                cls="flex items-center justify-between mb-1",
                            ),
                            P(todo.description or "No description", cls="text-sm text-gray-600"),
                            cls="bg-white border border-gray-200 rounded-lg shadow-sm p-4",
                        )
                        for todo in todos_snapshot
                    ]
                    or [
                        Div(
                            "No todos yet. Try adding one via the MCP chat!",
                            cls="text-sm text-gray-500",
                        )
                    ],
                    cls="grid gap-4",
                ),
            ),
            cls="max-w-4xl mx-auto p-6 space-y-6",
        ),
    )


@rt("/mcp/send")
def mcp_send(message: str):
    timestamp = dt.datetime.now()
    mcp_history.append(
        {"role": "user", "content": f"You: {message}", "timestamp": timestamp}
    )
    command = process_mcp_command(message)
    result = execute_mcp_action(command)
    mcp_history.append(
        {
            "role": "assistant",
            "content": f"Command: {command}\nResult: {result}",
            "timestamp": dt.datetime.now(),
        }
    )
    return RedirectResponse("/mcp", status_code=303)


@rt("/mcp/clear")
def mcp_clear():
    mcp_history.clear()
    return RedirectResponse("/mcp", status_code=303)


__all__ = ["mcp_page", "mcp_send", "mcp_clear", "mcp_history"]
