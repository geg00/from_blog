"""Query GPT playground routes."""

from __future__ import annotations

import json
from typing import Any, List

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
    Label,
    Li,
    Main,
    P,
    Pre,
    Span,
    Summary,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
)
from starlette.responses import JSONResponse, RedirectResponse

from web.app import rt
from web.services.query import (
    introspect_query_schema,
    parse_bool_flag,
    process_query_request,
    query_gpt_history,
)
from web.ui.scripts import recording_script
from web.services.query import format_schema_description


@rt("/query-gpt")
def query_gpt_endpoint(question: str = "", run: str = "false"):
    question_text = question.strip()
    run_flag = parse_bool_flag(run)
    payload, status_code = process_query_request(question_text, run_flag)
    return JSONResponse(payload, status_code=status_code)


@rt("/query-gpt/playground")
def query_gpt_playground():
    schema = introspect_query_schema()
    schema_text = format_schema_description(schema)
    history_cards: List[Any] = []
    for entry in reversed(query_gpt_history[-10:]):
        badge = Span(
            "Offline" if entry.get("offline") else "OpenAI",
            cls="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold "
            + (
                "bg-amber-100 text-amber-700"
                if entry.get("offline")
                else "bg-indigo-100 text-indigo-700"
            ),
        )
        sql_preview = entry.get("sql", "-- none") or "-- none"
        execution = entry.get("execution") or {}
        history_cards.append(
            Div(
                Div(
                    Div(
                        H3(entry.get("question", ""), cls="text-lg font-semibold text-gray-800"),
                        badge,
                        cls="flex items-center justify-between mb-2 gap-3",
                    ),
                    Pre(
                        Code(sql_preview, cls="language-sql"),
                        cls="bg-gray-900 text-gray-100 p-3 rounded mb-3 overflow-x-auto text-xs",
                    ),
                    Div(
                        Div(
                            Div("Confidence", cls="text-xs uppercase tracking-wide text-gray-500"),
                            Div(
                                f"{entry.get('confidence', 0):.2f}",
                                cls="text-sm font-semibold text-gray-800",
                            ),
                        ),
                        Div(
                            Div("Risk", cls="text-xs uppercase tracking-wide text-gray-500"),
                            Div(
                                str(entry.get("risk_flagged", False)),
                                cls="text-sm font-semibold text-gray-800",
                            ),
                        ),
                        Div(
                            Div("Rows", cls="text-xs uppercase tracking-wide text-gray-500"),
                            Div(
                                str(execution.get("row_count", 0)),
                                cls="text-sm font-semibold text-gray-800",
                            ),
                        ),
                        cls="grid grid-cols-3 gap-2 mb-2",
                    ),
                    P(entry.get("rationale", ""), cls="text-xs text-gray-500"),
                    cls="flex-1",
                ),
                cls="bg-white border border-gray-200 rounded-lg shadow-sm p-4 space-y-2",
            )
        )

    history_content = history_cards or [
        Div(
            "No runs yet. Submit a question to see history here.",
            cls="text-gray-500",
        )
    ]

    return (
        Title("Query GPT"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                H1("Query GPT Playground", cls="text-3xl font-bold text-gray-800 mb-2"),
                P(
                    "Transform natural language into safe SQL powered by the Text-to-SQL endpoint.",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        Img(
                            src="https://blog.uber-cdn.com/cdn-cgi/image/width=1400,quality=80,onerror=redirect,format=auto/wp-content/uploads/2024/09/cover-photo-1-2-17265874295011.jpeg",
                            alt="Uber QueryGPT hero image",
                            cls="w-full rounded-xl shadow-lg object-cover",
                        ),
                        cls="md:w-1/2",
                    ),
                    Div(
                        H2(
                            "Inspired by Uber's QueryGPT",
                            cls="text-2xl font-semibold text-gray-800 mb-3",
                        ),
                        P(
                            "Uber's QueryGPT team built a natural-language interface to their internal warehouse—"
                            "this playground brings the same energy with sandbox data and secure guardrails.",
                            cls="text-gray-600 mb-3 text-sm md:text-base",
                        ),
                        Ul(
                            Li("Use conversational prompts to draft SQL instantly."),
                            Li("Preview the generated statement before you run it."),
                            Li("Execute safely with automatic LIMITs and risk checks."),
                            cls="list-disc list-inside text-gray-600 mb-3 text-sm md:text-base",
                        ),
                        A(
                            "Read the full QueryGPT story",
                            href="https://www.uber.com/blog/query-gpt/",
                            cls="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-semibold",
                            target="_blank",
                        ),
                        cls="md:w-1/2 space-y-3",
                    ),
                    cls="flex flex-col md:flex-row gap-6 mb-8",
                ),
                Div(
                    H2("Schema Overview", cls="text-xl font-semibold text-gray-800 mb-3"),
                    Pre(
                        schema_text,
                        cls="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs",
                    ),
                    cls="mb-8",
                ),
                Form(
                    Div(
                        Label(
                            "Ask a question",
                            cls="text-sm font-medium text-gray-700",
                        ),
                        Input(
                            type="text",
                            name="question",
                            placeholder="e.g. How many enterprise tickets are still open?",
                            cls="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mt-2",
                        ),
                        cls="mb-4",
                    ),
                    Div(
                        Label(
                            "Run SQL immediately",
                            cls="text-sm font-medium text-gray-700",
                        ),
                        Input(
                            type="checkbox",
                            name="run",
                            value="true",
                            cls="mt-2",
                        ),
                        Span(
                            " Execute query after generation",
                            cls="text-sm text-gray-600 ml-2",
                        ),
                        cls="mb-4 flex items-center",
                    ),
                    Div(
                        Button(
                            "Generate SQL",
                            type="submit",
                            cls="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700",
                        ),
                        cls="flex justify-end",
                    ),
                    action="/query-gpt/playground/submit",
                    method="post",
                    cls="bg-white border border-gray-200 rounded-lg shadow-sm p-6",
                ),
                Div(
                    H2("Recent Runs", cls="text-xl font-semibold text-gray-800 mb-3"),
                    Div(*history_content, cls="grid gap-4"),
                ),
            ),
            cls="bg-gray-50 min-h-screen p-8 max-w-5xl mx-auto space-y-6",
        ),
    )


@rt("/query-gpt/playground/submit")
def query_gpt_playground_submit(question: str = "", run: str = "false"):
    question_text = question.strip()
    run_flag = parse_bool_flag(run)
    payload, status_code = process_query_request(question_text, run_flag)

    if status_code >= 400:
        return RedirectResponse("/query-gpt/playground", status_code=303)

    execution = payload.get("execution") or {}
    rows = execution.get("rows") or []
    results_table = (
        Table(
            Thead(
                Tr(
                    *[Th(str(col), cls="text-left text-xs uppercase text-gray-500") for col in rows[0].keys()]
                )
            ),
            Tbody(
                *[
                    Tr(
                        *[
                            Td(str(row.get(col, "")), cls="text-sm text-gray-700 py-1")
                            for col in rows[0].keys()
                        ]
                    )
                    for row in rows
                ]
            ),
            cls="min-w-full text-sm",
        )
        if rows
        else P("No rows returned.", cls="text-sm text-gray-500")
    )

    meta_badge = Span(
        "Offline plan" if payload.get("offline") else "OpenAI plan",
        cls="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold "
        + (
            "bg-amber-100 text-amber-700"
            if payload.get("offline")
            else "bg-indigo-100 text-indigo-700"
        ),
    )

    warning_block = (
        Div(
            payload.get("warning"),
            cls="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded",
        )
        if payload.get("warning")
        else None
    )

    error_block = (
        Div(
            Div("Generation error", cls="font-semibold mb-1 text-red-700"),
            P(payload.get("error", "Unknown error."), cls="text-sm text-red-600"),
            Pre(
                Code(str(payload.get("raw_response", "")), cls="language-json"),
                cls="bg-red-50 text-red-700 p-3 rounded mt-2 overflow-x-auto text-xs",
            ),
            cls="bg-red-100 border border-red-200 px-4 py-3 rounded-lg mb-4",
        )
        if payload.get("error")
        else None
    )

    sql_panel = Div(
        Div(
            H2("Generated SQL", cls="text-xl font-semibold text-gray-800 mb-2"),
            meta_badge,
            cls="flex items-center justify-between mb-2",
        ),
        Pre(
            Code(payload.get("sql", "-- no sql generated"), cls="language-sql"),
            cls="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm",
        ),
        P(payload.get("rationale", ""), cls="text-sm text-gray-600 mt-3"),
        cls="bg-white border border-gray-200 rounded-xl shadow-sm p-6",
    )

    metrics_cards = Div(
        Div(
            Div("Confidence", cls="text-xs uppercase tracking-wide text-gray-500 mb-1"),
            Div(f"{payload.get('confidence', 0):.2f}", cls="text-2xl font-semibold text-gray-800"),
            cls="bg-white border border-gray-200 rounded-lg p-4 shadow-sm",
        ),
        Div(
            Div("Risk Flagged", cls="text-xs uppercase tracking-wide text-gray-500 mb-1"),
            Div(str(payload.get("risk_flagged", False)), cls="text-2xl font-semibold text-gray-800"),
            P(payload.get("risk_reason", ""), cls="text-xs text-gray-500 mt-1"),
            cls="bg-white border border-gray-200 rounded-lg p-4 shadow-sm",
        ),
        cls="grid grid-cols-1 md:grid-cols-2 gap-4",
    )

    execution_children: List[Any] = [
        H2("Sample Results", cls="text-xl font-semibold text-gray-800 mb-2")
    ]
    if warning_block:
        execution_children.append(warning_block)
    execution_children.append(results_table)
    if rows:
        execution_children.append(
            Div(
                f"Rows returned: {execution.get('row_count', 0)}"
                + (" (truncated)" if execution.get("truncated") else ""),
                cls="text-xs text-gray-500 mt-2",
            )
        )
        execution_children.append(
            Div(
                f"Runtime: {execution.get('runtime_ms', 0)} ms",
                cls="text-xs text-gray-500",
            ),
        )
    execution_panel = Div(
        *execution_children,
        cls="bg-white border border-gray-200 rounded-xl shadow-sm p-6",
    )

    content_sections: List[Any] = [
        A(
            "← Back to Playground",
            href="/query-gpt/playground",
            cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
        ),
        error_block if error_block else sql_panel,
        metrics_cards,
    ]

    if not payload.get("error"):
        content_sections.append(execution_panel)
    if payload.get("schema_snapshot"):
        content_sections.append(
            Details(
                Summary(
                    "View Schema Context",
                    cls="cursor-pointer text-blue-600 hover:text-blue-800 font-semibold",
                ),
                Pre(
                    Code(json.dumps(payload["schema_snapshot"], indent=2), cls="language-json"),
                    cls="bg-gray-100 p-4 rounded-lg overflow-x-auto text-xs",
                ),
                cls="bg-white border border-gray-200 rounded-xl shadow-sm p-4",
            )
        )
    content_sections.append(
        Details(
            Summary(
                "Raw Payload",
                cls="cursor-pointer text-blue-600 hover:text-blue-800 font-semibold",
            ),
            Pre(
                Code(json.dumps(payload, indent=2), cls="language-json"),
                cls="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs",
            ),
            cls="bg-white border border-gray-200 rounded-xl shadow-sm p-4",
        )
    )

    return (
        Title("Query GPT Result"),
        recording_script,
        Main(
            Div(
                *[section for section in content_sections if section],
                cls="max-w-5xl mx-auto space-y-6",
            ),
            cls="bg-gray-50 min-h-screen p-8",
        ),
    )


__all__ = [
    "query_gpt_endpoint",
    "query_gpt_playground",
    "query_gpt_playground_submit",
]
