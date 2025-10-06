"""Application entrypoint that wires together routes and services."""

from __future__ import annotations

from fasthtml.common import serve
from fasthtml.jupyter import render_ft

from web.app import app  # noqa: F401 - ensure app is initialised
import web.routes  # noqa: F401  # register routes via side effects

serve()
render_ft()
