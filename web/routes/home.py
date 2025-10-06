"""Home page and static assets routes."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, List

from fasthtml.common import A, Div, H1, H2, H3, Img, Li, Main, P, Title, Ul
from starlette.responses import FileResponse

from web.app import rt

BASE_DIR = Path(__file__).resolve().parent.parent

@rt("/")
def home_page():
    cards: List[Dict[str, Any]] = [
        {
            "title": "Chat",
            "icon": "💬",
            "url": "/chat",
            "description": "Interactive conversations",
            "gradient": "from-blue-50 to-blue-100",
            "date": dt.date(2025, 9, 8),
            "order": 3,
        },
        {
            "title": "Agents",
            "icon": "🤖",
            "url": "/agents",
            "description": "AI agent management",
            "gradient": "from-green-50 to-green-100",
            "date": dt.date(2025, 9, 8),
            "order": 2,
        },
        {
            "title": "Vectors",
            "icon": "🔢",
            "url": "/vectors",
            "description": "Vector operations",
            "gradient": "from-purple-50 to-purple-100",
            "date": dt.date(2025, 9, 15),
            "order": 0,
        },
        {
            "title": "Embeddings",
            "icon": "🧬",
            "url": "/embeddings/playground",
            "description": "Generate and inspect embeddings",
            "gradient": "from-indigo-50 to-purple-100",
            "date": dt.date(2025, 9, 15),
            "order": 1,
        },
        {
            "title": "Query GPT",
            "icon": "🧠",
            "url": "/query-gpt/playground",
            "description": "Natural language to SQL",
            "gradient": "from-amber-50 to-yellow-100",
            "date": dt.date(2025, 9, 12),
            "order": 0,
        },
        {
            "title": "MCP",
            "icon": "⚡",
            "url": "/mcp",
            "description": "Model Context Protocol",
            "gradient": "from-orange-50 to-orange-100",
            "date": dt.date(2025, 9, 8),
            "order": 1,
        },
        {
            "title": "Guardrails",
            "icon": "🛡️",
            "url": "/guardrails",
            "description": "Compliance validation",
            "gradient": "from-red-50 to-red-100",
            "date": dt.date(2025, 9, 8),
            "order": 0,
        },
        {
            "title": "DSPy",
            "icon": "🧩",
            "url": "/dspy",
            "description": "Conversation history with DSPy",
            "gradient": "from-rose-50 to-pink-100",
            "date": dt.date(2025, 9, 22),
            "order": 0,
        },
    ]

    sorted_cards = sorted(
        cards,
        key=lambda card: (card["date"], card.get("order", 0)),
        reverse=True,
    )

    def format_card_date(value: dt.date) -> str:
        formatted = value.strftime("%d %b %Y")
        return formatted.lstrip("0")

    card_elements = [
        A(
            Div(
                Div(card["icon"], cls="text-5xl mb-4"),
                H3(card["title"], cls="text-2xl font-bold mb-3 text-gray-800"),
                P(
                    card["description"],
                    cls="text-gray-600 text-sm",
                ),
                Div(
                    P(
                        format_card_date(card["date"]),
                        cls="text-xs font-semibold text-gray-600",
                    ),
                    cls="mt-auto pt-4 border-t border-white/60",
                ),
                cls=(
                    f"bg-gradient-to-br {card['gradient']} p-8 rounded-xl shadow-lg "
                    "hover:shadow-2xl hover:scale-105 transform transition-all duration-300 "
                    "cursor-pointer border border-gray-100 flex flex-col h-full"
                ),
            ),
            href=card["url"],
            cls="block h-full",
        )
        for card in sorted_cards
    ]

    return Title("Home"), Main(
        Div(
            Div(
                Div(
                    Img(
                        src="/GG",
                        cls="w-32 h-32 rounded-lg mx-auto mb-6 shadow-lg border-4 border-white",
                    ),
                    H1("Gerardo Garcia", cls="text-3xl font-bold mb-2 text-gray-800"),
                    P("AI Engineer / Data Engineer", cls="text-lg text-gray-600 mb-4"),
                    P(
                        "As a seasoned AI Engineer, I specialize in transforming complex business challenges into "
                        "intelligent, automated solutions using cutting-edge Generative AI technologies. My expertise "
                        "spans the complete AI development lifecycle—from prompt engineering and RAG implementation "
                        "to production-grade deployment of LLM-powered applications.",
                        cls="text-gray-700 leading-relaxed max-w-4xl mx-auto",
                    ),
                    A(
                        "Learn More",
                        href="/whoami",
                        cls="inline-block mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700",
                    ),
                    cls="text-center py-12",
                ),
                cls="bg-gradient-to-r from-blue-50 to-indigo-100 mb-12",
            ),
            H1("Dashboard", cls="text-4xl font-bold mb-2 text-gray-800 text-center"),
            P("Choose a service to get started", cls="text-gray-600 text-center mb-12"),
            Div(*card_elements, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 max-w-7xl mx-auto"),
            cls="min-h-screen bg-gray-50 p-8",
        )
    )


@rt("/GG")
def serve_profile_image() -> Any:
    image_path = BASE_DIR / "GG.jpeg"
    return FileResponse(image_path)


@rt("/mcp-logo")
def serve_mcp_logo() -> Any:
    logo_path = BASE_DIR / "mcp-logo.svg"
    return FileResponse(logo_path)


@rt("/guardrails-workflow")
def serve_guardrails_workflow() -> Any:
    workflow_path = BASE_DIR / "guardrails-workflow.svg"
    return FileResponse(workflow_path)


@rt("/whoami")
def whoami():
    return Title("About Me"), Main(
        A(
            "← Back to Dashboard",
            href="/",
            cls="text-blue-600 hover:text-blue-800 mb-4 inline-block",
        ),
        Div(
            Img(
                src="/GG",
                cls="w-32 h-32 rounded-lg mx-auto mb-6 shadow-lg border-4 border-white",
            ),
            H1("Gerardo Garcia", cls="text-4xl font-bold text-center mb-2"),
            P(
                "AI Engineer / Data Engineer",
                cls="text-xl text-gray-600 text-center mb-8",
            ),
            cls="py-8",
        ),
        Div(
            H2("AI Expertise", cls="text-2xl font-bold mb-4"),
            P(
                "AI Engineer, I specialize in transforming complex business challenges into intelligent, "
                "automated solutions using cutting-edge Generative AI technologies. My expertise spans the complete "
                "AI development lifecycle—from prompt engineering and RAG implementation to production-grade deployment"
                " of LLM-powered applications.",
                cls="mb-4 text-gray-700 leading-relaxed",
            ),
            P(
                "My approach to GenAI development emphasizes practical implementation through Proof of Concept "
                "development and Agile methodologies. I build robust, scalable AI solutions that integrate seamlessly "
                "with existing enterprise infrastructure while maintaining reliability and security.",
                cls="mb-6 text-gray-700 leading-relaxed",
            ),
            H2("Professional Profile", cls="text-2xl font-bold mb-4"),
            P(
                "Innovative AI Product Engineer with extensive experience applying advanced LLM/Generative AI "
                "technologies to security, developer tools, and supply chain use cases. Python expert and prompt "
                "engineering specialist delivering production-ready integrations.",
                cls="mb-6 text-gray-700 leading-relaxed",
            ),
            H2("Technical Skills", cls="text-2xl font-bold mb-4"),
            Ul(
                Li("Programming: Python Expert (production/OOP/error handling)", cls="mb-2"),
                Li("SQL: Microsoft SQL Server, Oracle, MySQL, PostgreSQL", cls="mb-2"),
                Li(
                    "Generative AI/LLMs: OpenAI, HuggingFace, Gemini, Llama, LangChain, RAG, prompt engineering",
                    cls="mb-2",
                ),
                Li("Vector Databases: Pinecone, Chroma, Weaviate, FAISS", cls="mb-2"),
                Li("Cloud & Infra: AWS, Azure, Terraform, Docker", cls="mb-2"),
                Li("Big Data: PySpark, REST integrations, distributed ETL", cls="mb-2"),
                Li("MLOps: CI/CD, TDD/BDD, model serving, monitoring", cls="mb-2"),
                Li("AI Product Owner skills: vision, requirements, stakeholders, ethical AI", cls="mb-2"),
                cls="list-disc list-inside text-gray-700",
            ),
            H2("Leadership & Communication", cls="text-2xl font-bold mb-4 mt-8"),
            Ul(
                Li("Cross-functional leadership and mentoring", cls="mb-2"),
                Li("Translating technical insights for stakeholders", cls="mb-2"),
                Li("Agile project management and sprint planning", cls="mb-2"),
                Li("Client relationship management and requirements gathering", cls="mb-2"),
                cls="list-disc list-inside text-gray-700",
            ),
            H2("Contact", cls="text-2xl font-bold mb-4 mt-8"),
            P("📧 gerardo.e.garcia@gmail.com", cls="mb-2 text-gray-700"),
            P("📱 832-594-9644", cls="mb-2 text-gray-700"),
            P("📍 TX (US Citizen)", cls="mb-2 text-gray-700"),
            cls="bg-white p-8 rounded-lg shadow-lg",
        ),
        cls="max-w-4xl mx-auto p-6",
    )


__all__ = [
    "home_page",
    "serve_profile_image",
    "serve_mcp_logo",
    "serve_guardrails_workflow",
    "whoami",
]
