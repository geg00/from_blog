"""Vector helper routines used across multiple features."""

from __future__ import annotations

import numpy as np

try:  # Optional dependency: scikit-learn
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity  # type: ignore
except ImportError:  # pragma: no cover - dependency may be missing
    sklearn_cosine_similarity = None  # type: ignore


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return the cosine similarity matrix between two 2D arrays."""

    if sklearn_cosine_similarity is not None:
        return sklearn_cosine_similarity(a, b)

    a_norm = a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-8)
    b_norm = b / np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-8)
    return a_norm @ b_norm.T

__all__ = ["cosine_similarity_matrix"]
