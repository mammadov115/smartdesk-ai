"""
Pure utility functions — no Django imports, no side-effects.
Keep this module importable outside of a Django context (e.g. notebooks, scripts).
"""

import numpy as np

# Cosine-similarity floor for grouping two questions into the same cluster.
# 0.70 is a comfortable "same topic" threshold for text-embedding-3-small.
_SIM_THRESHOLD = 0.70


def cluster_by_cosine_similarity(messages: list[dict]) -> list[list[int]]:
    """
    Greedy cosine-similarity clustering on pre-computed embedding vectors.

    Args:
        messages: List of dicts that each contain an ``"embedding"`` key
                  (a list / array of floats with dimension 1536).

    Returns:
        A list of clusters sorted by size descending.  Each cluster is a
        list of *indices* into ``messages``.

    Complexity: O(n²) — acceptable for analytics workloads where n is at
    most a few thousand rows per user.
    """
    vectors = np.array([m["embedding"] for m in messages], dtype=np.float32)

    # Normalise rows to unit length so that dot product == cosine similarity.
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalised = vectors / norms  # shape (n, d)

    assigned = [False] * len(messages)
    clusters: list[list[int]] = []

    for i in range(len(messages)):
        if assigned[i]:
            continue
        # Similarity of every unassigned message against message i.
        sims = normalised @ normalised[i]  # shape (n,)
        cluster = [j for j in range(len(messages)) if not assigned[j] and sims[j] >= _SIM_THRESHOLD]
        for j in cluster:
            assigned[j] = True
        clusters.append(cluster)

    clusters.sort(key=len, reverse=True)
    return clusters
