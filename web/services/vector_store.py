"""Vector store utilities and in-memory cache management."""

from __future__ import annotations

import pickle
from typing import Any, Dict, List

import numpy as np
import requests

from web.config import (
    EMBEDDING_DIM,
    EXPECTED_OPENAI_EMBED_DIM,
    GUTENBERG_URL,
    MAX_GUTENBERG_CHUNKS,
    OPENAI_API_KEY,
    VECTOR_STORE_PATH,
)
from web.services.llm import call_openai, get_embedding
from web.utils.vectors import cosine_similarity_matrix

vector_store: Dict[str, List[Any]] = {"documents": [], "metadata": [], "embeddings": []}
vector_store_info: Dict[str, Any] = {
    "backend": "unknown",
    "embedding_dim": EMBEDDING_DIM,
    "source": "unloaded",
}
_vector_store_loaded = False


def _clean_gutenberg_text(raw_text: str) -> str:
    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"
    if start_marker in raw_text:
        raw_text = raw_text.split(start_marker, 1)[1]
    if end_marker in raw_text:
        raw_text = raw_text.split(end_marker, 1)[0]
    return raw_text.strip()


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
    return chunks


def _build_vector_store_from_gutenberg() -> Dict[str, Any]:
    response = requests.get(GUTENBERG_URL, timeout=15)
    response.raise_for_status()
    text = _clean_gutenberg_text(response.text)
    chunks = _chunk_text(text)
    if not chunks:
        raise ValueError("No chunks produced from Gutenberg text.")
    chunks = chunks[:MAX_GUTENBERG_CHUNKS]
    embeddings = [get_embedding(chunk) for chunk in chunks]
    metadata = [{"doc_name": f"Little Women – Chunk {idx + 1}"} for idx in range(len(chunks))]
    embedding_dim = int(embeddings[0].shape[0]) if embeddings else EMBEDDING_DIM
    backend = (
        "openai"
        if OPENAI_API_KEY and embedding_dim == EXPECTED_OPENAI_EMBED_DIM
        else "deterministic"
    )
    data: Dict[str, Any] = {
        "documents": chunks,
        "metadata": metadata,
        "embeddings": embeddings,
        "embedding_backend": backend,
        "embedding_dim": embedding_dim,
        "source": "gutenberg",
    }
    VECTOR_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VECTOR_STORE_PATH.open("wb") as f:
        pickle.dump(data, f)
    return data


def _load_pickled_vector_store() -> Dict[str, Any]:
    if not VECTOR_STORE_PATH.exists():
        raise FileNotFoundError
    with VECTOR_STORE_PATH.open("rb") as f:
        data = pickle.load(f)
    if not isinstance(data, dict):
        raise ValueError("Vector store pickle format invalid.")
    if not data.get("documents") or not data.get("embeddings"):
        raise ValueError("Vector store pickle missing data.")
    return data


def _default_vector_store_data() -> Dict[str, Any]:
    documents = [
        "Jo March longs to become a published author while supporting her family.",
        "Meg balances societal expectations with her desire for a loving home.",
        "Beth embodies kindness, offering quiet strength to everyone around her.",
        "Amy pursues artistry and self-improvement across continents.",
    ]
    metadata = [
        {"doc_name": "Little Women – Chapter 1"},
        {"doc_name": "Little Women – Chapter 5"},
        {"doc_name": "Little Women – Chapter 13"},
        {"doc_name": "Little Women – Chapter 31"},
    ]
    embeddings = [get_embedding(doc) for doc in documents]
    embedding_dim = int(embeddings[0].shape[0]) if embeddings else EMBEDDING_DIM
    backend = (
        "openai"
        if OPENAI_API_KEY and embedding_dim == EXPECTED_OPENAI_EMBED_DIM
        else "deterministic"
    )
    return {
        "documents": documents,
        "metadata": metadata,
        "embeddings": embeddings,
        "embedding_backend": backend,
        "embedding_dim": embedding_dim,
        "source": "sample",
    }


def _should_rebuild_vector_store(data: Dict[str, Any]) -> bool:
    backend = data.get("embedding_backend", "unknown")
    if backend == "openai":
        return False
    if not OPENAI_API_KEY:
        return False
    embeddings = data.get("embeddings")
    if not embeddings:
        return True
    sample = embeddings[0]
    if isinstance(sample, np.ndarray) and sample.shape[0] == EXPECTED_OPENAI_EMBED_DIM:
        return False
    if isinstance(sample, list) and len(sample) == EXPECTED_OPENAI_EMBED_DIM:
        return False
    return True


def load_vector_store() -> None:
    global _vector_store_loaded
    if _vector_store_loaded:
        return
    data: Dict[str, Any]
    try:
        data = _load_pickled_vector_store()
    except Exception:
        try:
            data = _build_vector_store_from_gutenberg()
        except Exception:
            data = _default_vector_store_data()

    if _should_rebuild_vector_store(data):
        try:
            data = _build_vector_store_from_gutenberg()
        except Exception:
            data = _default_vector_store_data()

    vector_store["documents"] = data["documents"]
    vector_store["metadata"] = data["metadata"]
    vector_store["embeddings"] = data["embeddings"]
    vector_store_info["backend"] = data.get("embedding_backend", "unknown")
    vector_store_info["embedding_dim"] = data.get(
        "embedding_dim",
        len(data["embeddings"][0]) if data.get("embeddings") else EMBEDDING_DIM,
    )
    vector_store_info["source"] = data.get("source", "unknown")
    _vector_store_loaded = True


def ensure_vector_store() -> None:
    if not _vector_store_loaded:
        load_vector_store()


def search_vectors(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    ensure_vector_store()
    if not vector_store["embeddings"]:
        return []

    query_embedding = get_embedding(query).reshape(1, -1)
    embeddings_matrix = np.vstack(vector_store["embeddings"])
    similarities = cosine_similarity_matrix(query_embedding, embeddings_matrix)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    results: List[Dict[str, Any]] = []
    for idx in top_indices:
        snippet = vector_store["documents"][idx]
        preview = snippet[:300] + ("..." if len(snippet) > 300 else "")
        results.append(
            {
                "title": vector_store["metadata"][idx]["doc_name"],
                "text": preview,
                "score": float(similarities[idx]),
            }
        )
    return results


def synthesize_vector_answer(query: str, results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No supporting documents were retrieved."

    context = "\n\n".join(
        f"Source: {result['title']}\nSnippet: {result['text']}" for result in results
    )

    if not context.strip():
        return "Retrieved documents were empty."

    if not OPENAI_API_KEY:
        return (
            "OpenAI API key not configured, so here's the top matching context:\n\n"
            + context
        )

    answer = call_openai(
        [
            {
                "role": "system",
                "content": (
                    "You are a literary assistant. Answer succinctly using ONLY the provided context. "
                    "If the context is insufficient, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nContext:\n{context}",
            },
        ]
    )

    normalized = answer.strip().lower()
    if normalized.startswith("openai api key not configured") or normalized.startswith("error:"):
        return "Top matching context:\n\n" + context

    return answer

__all__ = [
    "vector_store",
    "vector_store_info",
    "ensure_vector_store",
    "search_vectors",
    "synthesize_vector_answer",
]
