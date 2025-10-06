"""Guardrails compliance validation routes."""

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
    Img,
    Input,
    Li,
    Main,
    P,
    Summary,
    Title,
    Ul,
)
from starlette.responses import RedirectResponse

from web.app import rt
from web.services.llm import call_openai
from web.ui.scripts import recording_script
from web.utils.formatting import format_timestamp

guardrails_history: List[Dict[str, Any]] = []


def validate_compliance(message: str) -> bool:
    compliance_prompt = f"""You are a compliance officer. Analyze this request for Code of Conduct violations:\n\n"{message}"\n\nCheck for these violations:\n- Confidential/Proprietary Information disclosure\n- Conflicts of Interest  \n- Improper Gifts/Entertainment (like accepting tickets for contracts)\n- Discrimination/Harassment\n- Bribery/Kickbacks\n- Falsification of Records\n- Unauthorized Communications\n\nAnswer ONLY with "VIOLATION" or "COMPLIANT" - nothing else."""

    response = call_openai(
        [
            {
                "role": "system",
                "content": "You are a strict compliance officer. Answer only VIOLATION or COMPLIANT.",
            },
            {"role": "user", "content": compliance_prompt},
        ]
    )
    return "VIOLATION" in response.upper()


@rt("/guardrails")
def guardrails_page():
    return (
        Title("Guardrails"),
        recording_script,
        Main(
            A(
                "← Back to Dashboard",
                href="/",
                cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
            ),
            Div(
                H1("AI Guardrails System", cls="text-3xl font-bold text-center mb-2"),
                P(
                    "Test compliance validation system that checks user requests against Company Code of Conduct before processing. "
                    "This endpoint demonstrates AI-powered content moderation and policy enforcement.",
                    cls="text-gray-600 text-center mb-8 max-w-2xl mx-auto",
                ),
                cls="py-8",
            ),
            Div(
                H2("Guardrails workflow", cls="text-xl font-semibold mb-3 text-gray-800 text-center"),
                Img(
                    src="/guardrails-workflow",
                    alt="Guardrails with and without policy enforcement workflow",
                    cls="w-full max-w-4xl mx-auto mb-4 rounded-lg border border-gray-200 shadow-sm",
                ),
                P(
                    "Guardrails keeps large language model outputs within policy by wrapping prompts with validators, "
                    "repair flows, and structured schemas. The official project showcases how policy checks, fallbacks, and "
                    "corrections plug directly into your application workflow before responses reach end users.",
                    cls="text-gray-600 mb-3",
                ),
                Ul(
                    Li(
                        "Define validation rails that capture business rules, compliance constraints, or formatting requirements.",
                    ),
                    Li(
                        "Automatically repair model outputs when checks fail, ensuring downstream systems only see approved content.",
                    ),
                    Li(
                        "Compose reusable rails and evaluate them with the Guardrails Hub to monitor quality over time.",
                    ),
                    cls="list-disc list-inside text-gray-600 mb-3",
                ),
                P(
                    "Explore the open-source toolkit, recipes, and hub integrations on the Guardrails repository. ",
                    A(
                        "Visit Guardrails on GitHub",
                        href="https://github.com/guardrails-ai/guardrails",
                        cls="text-red-600 hover:text-red-800",
                    ),
                    cls="text-gray-600",
                ),
                cls="bg-white shadow-sm border border-gray-200 rounded-lg p-6 mb-6",
            ),
            Div(
                *[
                    Div(
                        Div(
                            Div(
                                "🛡️" if msg["role"] == "assistant" else "👤",
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
                    for msg in guardrails_history
                ],
                id="guardrails-container",
                cls="bg-gray-50 rounded-lg shadow-lg p-6 mb-4 min-h-96",
            ),
            Div(
                Form(
                    Div(
                        Input(
                            type="text",
                            name="message",
                            placeholder="Test compliance validation: Ask anything...",
                            cls="flex-1 p-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-red-500",
                        ),
                        Button(
                            "Validate",
                            type="submit",
                            cls="bg-red-600 text-white px-6 py-3 rounded-r-lg hover:bg-red-700",
                        ),
                        cls="flex mb-2",
                    ),
                    action="/guardrails/validate",
                    method="post",
                ),
                Div(
                    A(
                        "Clear Guardrails",
                        href="/guardrails/clear",
                        cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
                    ),
                    cls="flex gap-2",
                ),
                cls="mb-4",
            ),
            cls="max-w-4xl mx-auto p-6",
        ),
    )


@rt("/guardrails/validate")
def guardrails_validate(message: str):
    timestamp = dt.datetime.now()
    guardrails_history.append(
        {"role": "user", "content": f"You: {message}", "timestamp": timestamp}
    )

    if validate_compliance(message):
        response = (
            "🚫 Guardrail Triggered – Potential Code of Conduct Violation 🚫\n\n"
            "This request may violate the Company's Code of Conduct or policy. Please consult your supervisor, "
            "HR, Legal/Compliance, Internal Audit, or call the Compliance Hotline. No further action will be taken until reviewed."
        )
    else:
        response = call_openai([{ "role": "user", "content": message }])

    guardrails_history.append(
        {
            "role": "assistant",
            "content": f"Guardrails: {response}",
            "timestamp": dt.datetime.now(),
        }
    )
    return RedirectResponse("/guardrails", status_code=303)


@rt("/guardrails/clear")
def guardrails_clear():
    guardrails_history.clear()
    return RedirectResponse("/guardrails", status_code=303)


__all__ = ["guardrails_page", "guardrails_validate", "guardrails_clear", "guardrails_history"]
