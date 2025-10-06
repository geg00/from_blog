"""Application setup for the FastHTML demo."""

from __future__ import annotations

from fasthtml.common import FastHTML, Script

app = FastHTML(hdrs=(Script(src="https://cdn.tailwindcss.com"),))
rt = app.route

__all__ = ["app", "rt"]
