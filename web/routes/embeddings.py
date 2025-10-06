"""Embeddings playground routes and API."""

from __future__ import annotations

import datetime as dt
import json
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
    Label,
    Main,
    P,
    Pre,
    Summary,
    Textarea,
    Title,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from web.app import rt
from web.config import HUGGINGFACE_API_TOKEN, HUGGINGFACE_EMBEDDING_MODEL
from web.services.llm import fetch_huggingface_embeddings
from web.utils.formatting import format_embedding_preview, format_timestamp

embedding_history: List[Dict[str, Any]] = []


@rt("/embeddings/playground")
def embeddings_playground_page():
    recent_entries = list(reversed(embedding_history[-10:]))

    history_cards = []
    for entry in recent_entries:
        header = Div(
            Div(
                format_timestamp(entry["timestamp"]),
                cls="text-xs font-semibold text-gray-500",
            ),
            Div(
                f"Inputs: {len(entry.get('inputs', []))}",
                cls="text-xs text-gray-400",
            ),
            cls="flex justify-between mb-2",
        )

        input_block = Div(
            *[P(f"“{text}”", cls="text-sm text-gray-800") for text in entry.get("inputs", [])],
            cls="space-y-1 mb-3",
        )

        if entry.get("error"):
            body = Div(
                P("Request failed", cls="font-semibold text-red-600 mb-1"),
                P(entry["error"], cls="text-sm text-red-500"),
            )
            card_cls = "bg-red-50 border border-red-200"
        else:
            vectors = entry.get("vectors", [])
            previews = [
                Div(
                    P(f"Vector {idx + 1}", cls="text-xs font-semibold text-gray-500"),
                    Pre(
                        format_embedding_preview(vector),
                        cls="text-xs bg-gray-900 text-green-200 rounded px-3 py-2 overflow-x-auto",
                    ),
                    cls="mb-2",
                )
                for idx, vector in enumerate(vectors)
            ]
            body = Div(
                P(
                    f"Dimension: {entry.get('dimension', 0)}",
                    cls="text-xs text-gray-500 mb-2",
                ),
                *previews,
            )
            card_cls = "bg-white border border-gray-200"

        history_cards.append(
            Div(
                header,
                input_block,
                body,
                cls=f"{card_cls} rounded-lg p-4 shadow-sm",
            )
        )

    status_banner = None
    if not HUGGINGFACE_API_TOKEN:
        status_banner = Div(
            "Set HF_TOKEN (or HUGGINGFACE_API_TOKEN/HUGGINGFACEHUB_API_TOKEN) to enable live embeddings.",
            cls="bg-yellow-100 border border-yellow-300 text-yellow-800 px-4 py-3 rounded mb-6",
        )

    content_children = [
        A(
            "← Back to Dashboard",
            href="/",
            cls="text-blue-600 hover:text-blue-800 mb-6 inline-block",
        ),
        H1("Embeddings Playground", cls="text-3xl font-bold mb-2 text-gray-800"),
        P(
            f"Model: {HUGGINGFACE_EMBEDDING_MODEL}",
            cls="text-sm text-gray-500 mb-6",
        ),
    ]

    if status_banner:
        content_children.append(status_banner)

    content_children.extend(
        [
            Div(
                Form(
                    Div(
                        Label(
                            "Enter one phrase per line",
                            cls="text-sm font-medium text-gray-700",
                        ),
                        Textarea(
                            name="texts",
                            placeholder="Example: How can Medicare help me?\nSecond example phrase",
                            rows=4,
                            cls="w-full mt-2 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500",
                        ),
                        cls="mb-4",
                    ),
                    Div(
                        Button(
                            "Generate Embeddings",
                            type="submit",
                            cls="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700",
                        ),
                        cls="flex justify-end",
                    ),
                    method="post",
                    action="/embeddings/playground/run",
                    cls="bg-white border border-gray-200 rounded-lg p-6 shadow-sm",
                ),
                cls="mb-8",
            ),
            Div(
                H2("Helpful Resources", cls="text-2xl font-semibold mb-4 text-gray-800"),
                Div(
                    Div(
                        H3(
                            "Getting Started with Embeddings (Hugging Face Blog)",
                            cls="text-lg font-semibold text-gray-800 mb-2",
                        ),
                        P(
                            "A friendly introduction which explains how sentence transformers map text to vectors, "
                            "with practical advice on picking models and tuning performance.",
                            cls="text-sm text-gray-600",
                        ),
                        A(
                            "Read the guide",
                            href="https://huggingface.co/blog/getting-started-with-embeddings",
                            cls="text-purple-600 hover:text-purple-800 text-sm",
                        ),
                        cls="p-4 bg-white border border-gray-200 rounded-lg shadow-sm",
                    ),
                    Div(
                        H3(
                            "Vector Databases: Which One Should You Use?",
                            cls="text-lg font-semibold text-gray-800 mb-2",
                        ),
                        P(
                            "Comparison of popular vector stores (Pinecone, Weaviate, Chroma, FAISS) and how they "
                            "fit different workloads.",
                            cls="text-sm text-gray-600",
                        ),
                        A(
                            "Explore comparisons",
                            href="https://www.pinecone.io/learn/vector-database/",
                            cls="text-purple-600 hover:text-purple-800 text-sm",
                        ),
                        cls="p-4 bg-white border border-gray-200 rounded-lg shadow-sm",
                    ),
                    cls="grid gap-4 md:grid-cols-2 mb-8",
                ),
            ),
            Div(
                H2("Recent Requests", cls="text-2xl font-semibold mb-4 text-gray-800"),
                Div(
                    *history_cards
                    if history_cards
                    else [
                        Div(
                            "Run your first request to see embeddings previewed here.",
                            cls="text-sm text-gray-500",
                        )
                    ],
                    cls="grid gap-4",
                ),
            ),
        ]
    )

    return (
        Title("Embeddings Playground"),
        Main(
            Div(
                *content_children,
                cls="max-w-3xl mx-auto py-10",
            )
        ),
    )


@rt("/embeddings/playground/run")
def embeddings_playground_run(texts: str):
    timestamp = dt.datetime.now()
    entries = [line.strip() for line in texts.splitlines() if line.strip()]

    if not entries:
        embedding_history.append(
            {
                "timestamp": timestamp,
                "inputs": [],
                "error": "Enter at least one non-empty line to generate embeddings.",
            }
        )
        if len(embedding_history) > 25:
            del embedding_history[:-25]
        return RedirectResponse("/embeddings/playground", status_code=303)

    try:
        vectors = fetch_huggingface_embeddings(entries)
        dimension = len(vectors[0]) if vectors and vectors[0] else 0
        embedding_history.append(
            {
                "timestamp": timestamp,
                "inputs": entries,
                "vectors": vectors,
                "dimension": dimension,
            }
        )
    except Exception as exc:
        embedding_history.append(
            {
                "timestamp": timestamp,
                "inputs": entries,
                "error": str(exc),
            }
        )

    if len(embedding_history) > 25:
        del embedding_history[:-25]

    return RedirectResponse("/embeddings/playground", status_code=303)


@rt("/embeddings")
async def embeddings_endpoint(request: Request):
    if request.method != "POST":
        return JSONResponse(
            {
                "error": "Use POST with JSON body {'inputs': ['text', ...]} to generate embeddings.",
                "model": HUGGINGFACE_EMBEDDING_MODEL,
            },
            status_code=405,
        )

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)
    except Exception as exc:  # pragma: no cover - defensive branch
        return JSONResponse({"error": f"Unable to read request body: {exc}"}, status_code=400)

    raw_inputs = payload.get("inputs")
    if raw_inputs is None and "text" in payload:
        raw_inputs = payload["text"]

    if isinstance(raw_inputs, str):
        texts = [raw_inputs.strip()]
    elif isinstance(raw_inputs, list):
        texts = [str(item).strip() for item in raw_inputs if isinstance(item, str)]
    else:
        return JSONResponse(
            {"error": "Provide 'inputs' as a string or list of strings."},
            status_code=400,
        )

    texts = [text for text in texts if text]
    if not texts:
        return JSONResponse(
            {"error": "At least one non-empty text input is required."}, status_code=400
        )

    try:
        embeddings = fetch_huggingface_embeddings(texts)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)

    dimension = len(embeddings[0]) if embeddings and embeddings[0] else 0
    return JSONResponse(
        {
            "model": HUGGINGFACE_EMBEDDING_MODEL,
            "count": len(embeddings),
            "dimension": dimension,
            "embeddings": embeddings,
        }
    )


__all__ = [
    "embeddings_playground_page",
    "embeddings_playground_run",
    "embeddings_endpoint",
    "embedding_history",
]
