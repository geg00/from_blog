"""Vector search playground routes."""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from fasthtml.common import (
    A,
    Button,
    Details,
    Div,
    Form,
    H1,
    H2,
    Input,
    Main,
    P,
    Summary,
    Title,
)
from starlette.responses import RedirectResponse

from web.app import rt
from web.services.vector_store import (
    ensure_vector_store,
    search_vectors,
    synthesize_vector_answer,
    vector_store_info,
)
from web.ui.scripts import recording_script
from web.utils.formatting import format_timestamp

vector_history: List[Dict[str, Any]] = []


@rt("/vectors")
def vectors_page():
    ensure_vector_store()
    return (
        Title("Vector Search"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                H1("Vector RAG Assistant", cls="text-3xl font-bold text-center mb-2"),
                P(
                    "Search literary passages from Little Women and synthesize answers from retrieved context.",
                    cls="text-gray-600 text-center mb-4 max-w-2xl mx-auto",
                ),
                Details(
                    Summary(
                        "View Vector Store Details",
                        cls="cursor-pointer text-purple-600 hover:text-purple-800 font-semibold",
                    ),
                    Div(
                        P(
                            f"Embedding backend: {vector_store_info['backend']}",
                            cls="mb-1 text-sm text-gray-500",
                        ),
                        P(
                            f"Embedding dimension: {vector_store_info['embedding_dim']}",
                            cls="mb-1 text-sm text-gray-500",
                        ),
                        P(
                            f"Source: {vector_store_info['source']}",
                            cls="mb-2 text-sm text-gray-500",
                        ),
                        cls="bg-white p-4 rounded-lg shadow-sm",
                    ),
                    cls="bg-white border border-gray-200 rounded-lg p-4 mb-6",
                ),
                cls="py-8",
            ),
            Div(
                *[
                    Div(
                        Div(
                            Div(
                                "🔍" if msg["role"] == "assistant" else "👤",
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
                    for msg in vector_history
                ],
                id="vector-container",
                cls="bg-gray-50 rounded-lg shadow-lg p-6 mb-4 min-h-96",
            ),
            Div(
                Form(
                    Div(
                        Input(
                            type="text",
                            name="query",
                            placeholder="Search documents e.g. 'family relationships'",
                            cls="flex-1 p-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-purple-500",
                        ),
                        Button(
                            "Search",
                            type="submit",
                            cls="bg-purple-600 text-white px-6 py-3 rounded-r-lg hover:bg-purple-700",
                        ),
                        cls="flex mb-2",
                    ),
                    action="/vectors/search",
                    method="post",
                ),
                Div(
                    A(
                        "Clear Search",
                        href="/vectors/clear",
                        cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 mr-2",
                    ),
                    Button(
                        "🎤 Voice Input",
                        type="button",
                        cls="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600",
                        onclick="startRecording(this)",
                        data_target="input[name='query']",
                    ),
                    cls="flex gap-2",
                ),
                cls="mb-4",
            ),
            cls="max-w-4xl mx-auto p-6",
        ),
    )


@rt("/vectors/search")
def vectors_search(query: str):
    timestamp = dt.datetime.now()
    vector_history.append(
        {
            "role": "user",
            "content": f"Search: {query}",
            "timestamp": timestamp,
        }
    )
    results = search_vectors(query, top_k=3)
    if results:
        answer = synthesize_vector_answer(query, results)
        details = "\n\n".join(
            [
                f"Score: {result['score']:.3f}\nSource: {result['title']}\nSnippet: {result['text']}"
                for result in results
            ]
        )
        summary = f"Answer:\n{answer}\n\nTop matches:\n\n{details}"
    else:
        summary = "No results found for that query."

    vector_history.append(
        {
            "role": "assistant",
            "content": summary,
            "timestamp": dt.datetime.now(),
        }
    )
    return RedirectResponse("/vectors", status_code=303)


@rt("/vectors/clear")
def vectors_clear():
    vector_history.clear()
    return RedirectResponse("/vectors", status_code=303)


__all__ = ["vectors_page", "vectors_search", "vectors_clear", "vector_history"]
