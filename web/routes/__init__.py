"""Route registrations for the FastHTML application."""

from __future__ import annotations

# Import modules for side effects so their decorators register routes.
from . import agents, chat, dspy, embeddings, guardrails, home, mcp, query_gpt, vectors  # noqa: F401

__all__ = [
    "agents",
    "chat",
    "dspy",
    "embeddings",
    "guardrails",
    "home",
    "mcp",
    "query_gpt",
    "vectors",
]
