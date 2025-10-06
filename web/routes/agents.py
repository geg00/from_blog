"""Agent assistant routes."""

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
    Img,
    Input,
    Main,
    P,
    Pre,
    Summary,
    Title,
)
from starlette.responses import RedirectResponse

from web.app import rt
from web.services.agents import process_agent_message
from web.ui.scripts import recording_script
from web.utils.formatting import format_timestamp

agent_history: List[Dict[str, Any]] = []


@rt("/agents")
def agents_page():
    return (
        Title("AI Agents"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                H1("AI Agent Assistant", cls="text-3xl font-bold text-center mb-2"),
                P(
                    "Intelligent agents with built-in web search via DuckDuckGo."
                    " When relevant, the assistant augments answers with fresh search results.",
                    cls="text-gray-600 text-center mb-4 max-w-2xl mx-auto",
                ),
                Div(
                    H2("How the agent thinks and acts", cls="text-xl font-semibold mb-2 text-gray-800"),
                    P(
                        "The interaction pattern follows the ReAct approach—agents interleave reasoning steps with "
                        "actions such as web lookups or tool calls to gather evidence before answering. This pattern "
                        "was introduced in the research paper ",
                        A(
                            "ReAct: Synergizing Reasoning and Acting in Language Models",
                            href="https://arxiv.org/pdf/2210.03629",
                            cls="text-blue-600 hover:text-blue-800",
                        ),
                        ", which highlights how combining chain-of-thought with tool use improves reliability.",
                        cls="text-gray-600 mb-3",
                    ),
                    P(
                        "For a practical implementation reference, the open-source ",
                        A(
                            "LangChain ReAct agent",
                            href="https://github.com/langchain-ai/react-agent?tab=readme-ov-file",
                            cls="text-blue-600 hover:text-blue-800",
                        ),
                        " project demonstrates how to structure prompts, maintain scratchpads, and register tools. "
                        "While this demo stays framework-agnostic, the concepts of action planning, observation logging, "
                        "and iterative refinement mirror that example.",
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
                            '''def process_agent_message(message: str) -> tuple[str, str]:
    search_results = search_duckduckgo(message)
    if search_results:
        prompt = f"Search results: {search_results}\n\nQuestion: {message}\n\nUse the search findings when relevant."
        source = "search"
    else:
        prompt, source = message, "direct"

    reply = call_openai([
        {"role": "system", "content": "You are a helpful AI research assistant."},
        {"role": "user", "content": prompt},
    ])
    return reply, source
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
                                "🤖" if msg["role"] == "assistant" else "👤",
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
                    for msg in agent_history
                ],
                id="agents-container",
                cls="bg-gray-50 rounded-lg shadow-lg p-6 mb-4 min-h-96",
            ),
            Div(
                Form(
                    Div(
                        Input(
                            type="text",
                            name="message",
                            placeholder="Ask the research agent...",
                            cls="flex-1 p-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-green-500",
                        ),
                        Button(
                            "Send",
                            type="submit",
                            cls="bg-green-600 text-white px-6 py-3 rounded-r-lg hover:bg-green-700",
                        ),
                        cls="flex mb-2",
                    ),
                    action="/agents/send",
                    method="post",
                ),
                Div(
                    Button(
                        "🎤 Voice Input",
                        type="button",
                        cls="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600",
                        onclick="startRecording(this)",
                    ),
                    A(
                        "Clear Agent",
                        href="/agents/clear",
                        cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
                    ),
                    cls="flex gap-2",
                ),
                cls="mb-4",
            ),
            cls="max-w-3xl mx-auto p-6",
        ),
    )


@rt("/agents/send")
def agents_send(message: str):
    timestamp = dt.datetime.now()
    agent_history.append(
        {"role": "user", "content": f"You: {message}", "timestamp": timestamp}
    )
    reply, source = process_agent_message(message)
    agent_history.append(
        {
            "role": "assistant",
            "content": f"Agent ({source}): {reply}",
            "timestamp": dt.datetime.now(),
        }
    )
    return RedirectResponse("/agents", status_code=303)


@rt("/agents/clear")
def agents_clear():
    agent_history.clear()
    return RedirectResponse("/agents", status_code=303)


__all__ = ["agents_page", "agents_send", "agents_clear", "agent_history"]
