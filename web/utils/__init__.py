"""Utility helpers used across the FastHTML demo."""

from .formatting import format_embedding_preview, format_timestamp
from .vectors import cosine_similarity_matrix

__all__ = [
    "format_embedding_preview",
    "format_timestamp",
    "cosine_similarity_matrix",
]
