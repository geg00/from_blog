"""Chat experience routes."""

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
    Img,
    Main,
    P,
    Pre,
    Summary,
    Textarea,
    Title,
)
from starlette.responses import RedirectResponse

from web.app import rt
from web.services.llm import call_openai
from web.ui.scripts import recording_script
from web.utils.formatting import format_timestamp

chat_history: List[Dict[str, Any]] = []


@rt("/chat")
def chat_page():
    return (
        Title("Chat"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                Img(
                    src="https://images.unsplash.com/photo-1577563908411-5077b6dc7624?w=400",
                    cls="w-24 h-24 rounded-full mx-auto mb-4",
                ),
                H1("AI Chat Assistant", cls="text-3xl font-bold text-center mb-2"),
                P(
                    "Have natural conversations with an AI assistant powered by OpenAI's GPT-4."
                    " This endpoint demonstrates message history, timestamps, and voice input",
                    cls="text-gray-600 text-center mb-4 max-w-2xl mx-auto",
                ),
                Details(
                    Summary(
                        "View Sample Code",
                        cls="cursor-pointer text-blue-600 hover:text-blue-800 font-semibold",
                    ),
                    Pre(
                        Code(
                            '''@rt("/chat/send")
def post(message: str):
    timestamp = dt.datetime.now()
    chat_history.append({"role": "user", "content": f"You: {message}", "timestamp": timestamp})
    bot_response = call_openai([{"role": "user", "content": message}])
    chat_history.append({"role": "assistant", "content": f"Bot: {bot_response}", "timestamp": dt.datetime.now()})
    return RedirectResponse("/chat", status_code=303)
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
                    for msg in chat_history
                ],
                id="chat-container",
                cls="bg-gray-50 rounded-lg shadow-lg p-6 mb-4 min-h-96",
            ),
            Div(
                Form(
                    Div(
                        Textarea(
                            name="message",
                            placeholder="Send a message...",
                            cls="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
                            rows=2,
                        ),
                        Button(
                            "Send",
                            type="submit",
                            cls="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700",
                        ),
                        cls="flex flex-col gap-2 mb-2",
                    ),
                    action="/chat/send",
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
                        "Clear Chat",
                        href="/chat/clear",
                        cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
                    ),
                    cls="flex gap-2",
                ),
                cls="mb-4",
            ),
            cls="max-w-3xl mx-auto p-6",
        ),
    )


@rt("/chat/send")
def chat_send(message: str):
    timestamp = dt.datetime.now()
    chat_history.append(
        {"role": "user", "content": f"You: {message}", "timestamp": timestamp}
    )
    bot_response = call_openai([{ "role": "user", "content": message }])
    chat_history.append(
        {
            "role": "assistant",
            "content": f"Bot: {bot_response}",
            "timestamp": dt.datetime.now(),
        }
    )
    return RedirectResponse("/chat", status_code=303)


@rt("/chat/clear")
def chat_clear():
    chat_history.clear()
    return RedirectResponse("/chat", status_code=303)


__all__ = ["chat_page", "chat_send", "chat_clear", "chat_history"]
