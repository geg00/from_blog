"""Shared configuration constants for the FastHTML demo app."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_TOKEN = (
    os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_API_TOKEN")
    or os.getenv("HUGGINGFACEHUB_API_TOKEN")
)
HUGGINGFACE_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
HUGGINGFACE_API_URL = (
    f"https://api-inference.huggingface.co/pipeline/feature-extraction/"
    f"{HUGGINGFACE_EMBEDDING_MODEL}"
)

EMBEDDING_DIM = 512
EXPECTED_OPENAI_EMBED_DIM = 1536

DATA_DIR = Path(__file__).resolve().parent / "data"
VECTOR_STORE_PATH = DATA_DIR / "little_women_vectors.pkl"
GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/514/pg514.txt"
MAX_GUTENBERG_CHUNKS = 200

QUERY_GPT_DB_PATH = DATA_DIR / "query_gpt_demo.db"
QUERY_GPT_HISTORY_LIMIT = 25
QUERY_SCHEMA_TTL = dt.timedelta(minutes=15)

__all__ = [
    "OPENAI_API_KEY",
    "HUGGINGFACE_API_TOKEN",
    "HUGGINGFACE_EMBEDDING_MODEL",
    "HUGGINGFACE_API_URL",
    "EMBEDDING_DIM",
    "EXPECTED_OPENAI_EMBED_DIM",
    "DATA_DIR",
    "VECTOR_STORE_PATH",
    "GUTENBERG_URL",
    "MAX_GUTENBERG_CHUNKS",
    "QUERY_GPT_DB_PATH",
    "QUERY_GPT_HISTORY_LIMIT",
    "QUERY_SCHEMA_TTL",
]
