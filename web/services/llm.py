"""LLM-related helpers shared across application features."""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List

import numpy as np
import requests

from web.config import (
    EMBEDDING_DIM,
    HUGGINGFACE_API_TOKEN,
    HUGGINGFACE_API_URL,
    HUGGINGFACE_EMBEDDING_MODEL,
    OPENAI_API_KEY,
)

try:  # Optional dependencies
    import openai  # type: ignore
except ImportError:  # pragma: no cover - library may be missing
    openai = None  # type: ignore

try:  # Optional dependency for Hugging Face client
    from huggingface_hub import InferenceClient  # type: ignore
except ImportError:  # pragma: no cover - library may be missing
    InferenceClient = None  # type: ignore

_huggingface_client: Any | None = None

def is_openai_configured() -> bool:
    return openai is not None and bool(OPENAI_API_KEY)


def call_openai(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """Call the OpenAI API when configured, otherwise return an informative notice."""

    if openai is None or not OPENAI_API_KEY:
        fallback_responses = [
            "OpenAI API key not configured. Set OPENAI_API_KEY to enable live responses.",
            "Add your OPENAI_API_KEY environment variable to unlock full assistant replies.",
        ]
        return random.choice(fallback_responses)

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
    except Exception as exc:  # pragma: no cover - network dependent
        return f"Error: {exc}"


def deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    if not text.strip():
        return np.zeros(dim, dtype=np.float32)

    vector = np.zeros(dim, dtype=np.float32)
    for token in text.lower().split():
        seed = abs(hash(token)) % (2**32)
        rng = np.random.default_rng(seed)
        vector += rng.standard_normal(dim)
    norm = np.linalg.norm(vector)
    if norm:
        vector /= norm
    return vector


def get_embedding(text: str) -> np.ndarray:
    if openai is None or not OPENAI_API_KEY:
        return deterministic_embedding(text)

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception:  # pragma: no cover - network dependent
        return deterministic_embedding(text)


def fetch_huggingface_embeddings(
    texts: List[str], retries: int = 3, backoff_seconds: float = 5.0
) -> List[List[float]]:
    if not texts:
        raise ValueError("No texts provided for embedding generation.")
    if not HUGGINGFACE_API_TOKEN:
        raise RuntimeError(
            "Set HF_TOKEN, HUGGINGFACE_API_TOKEN, or HUGGINGFACEHUB_API_TOKEN to use Hugging Face embeddings."
        )

    hf_client_error: str | None = None
    if InferenceClient is not None:
        global _huggingface_client
        if _huggingface_client is None:
            try:
                _huggingface_client = InferenceClient(
                    token=HUGGINGFACE_API_TOKEN,
                )
            except Exception as exc:  # pragma: no cover - defensive
                hf_client_error = str(exc)
        if _huggingface_client is not None:
            try:
                result = _huggingface_client.feature_extraction(
                    texts,
                    model=HUGGINGFACE_EMBEDDING_MODEL,
                )
                array = np.asarray(result, dtype=np.float32)
                if array.ndim == 1:
                    array = array.reshape(1, -1)
                return array.tolist()
            except Exception as exc:  # pragma: no cover - network dependent
                hf_client_error = str(exc)
                # Fall through to raw HTTP fallback below.
    else:
        hf_client_error = "Install 'huggingface-hub' to enable Hugging Face embeddings."

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payload = {"inputs": texts, "options": {"wait_for_model": True}}
    last_error: str | None = hf_client_error

    for attempt in range(retries):
        try:
            response = requests.post(
                HUGGINGFACE_API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            last_error = str(exc)
        else:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if data and all(isinstance(val, (int, float)) for val in data):
                        return [data]
                    if data and all(isinstance(val, list) for val in data):
                        return data
                    if not data:
                        return []
                    last_error = "Unexpected list format received from Hugging Face API."
                elif isinstance(data, dict) and "embeddings" in data:
                    embedded = data.get("embeddings")
                    if isinstance(embedded, list):
                        if embedded and all(isinstance(val, (int, float)) for val in embedded):
                            return [embedded]
                        if embedded and all(isinstance(val, list) for val in embedded):
                            return embedded
                        if not embedded:
                            return []
                        last_error = "Unexpected embeddings format received from Hugging Face API."
                    else:
                        last_error = "Embeddings payload from Hugging Face API was not a list."
                else:
                    last_error = "Unexpected response format received from Hugging Face API."
            else:
                try:
                    error_payload = response.json()
                    if isinstance(error_payload, dict) and "error" in error_payload:
                        last_error = str(error_payload["error"])
                    else:
                        last_error = response.text.strip()
                except ValueError:
                    last_error = response.text.strip()

        if attempt < retries - 1:
            time.sleep(backoff_seconds)

    raise RuntimeError(last_error or "Failed to generate embeddings via Hugging Face API.")

__all__ = [
    "call_openai",
    "deterministic_embedding",
    "get_embedding",
    "fetch_huggingface_embeddings",
    "is_openai_configured",
]
