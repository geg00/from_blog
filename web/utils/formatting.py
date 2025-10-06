"""Utility helpers for formatting timestamps and embeddings."""

from __future__ import annotations

import datetime as dt
from typing import List


def format_timestamp(timestamp: dt.datetime) -> str:
    now = dt.datetime.now()
    if timestamp.date() == now.date():
        return f"Today {timestamp.strftime('%I:%M %p')}"
    if timestamp.date() == (now - dt.timedelta(days=1)).date():
        return f"Yesterday {timestamp.strftime('%I:%M %p')}"
    return timestamp.strftime('%m/%d %I:%M %p')


def format_embedding_preview(vector: List[float], limit: int = 12) -> str:
    preview = ", ".join(f"{val:.3f}" for val in vector[:limit])
    remaining = max(len(vector) - limit, 0)
    if remaining > 0:
        return f"[{preview}, … +{remaining} more]"
    return f"[{preview}]"

__all__ = ["format_timestamp", "format_embedding_preview"]
