"""Pure helpers for document duplicate scan (no ES/DB deps)."""

import math


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def exact_duplicate_groups(docs):
    """Group docs by content_hash (enabled, Current Version)."""
    buckets = {}
    for d in docs:
        h = getattr(d, "content_hash", "") or ""
        if not h or not str(h).strip():
            continue
        buckets.setdefault(str(h), []).append(d)
    groups = []
    for h, lst in buckets.items():
        if len(lst) < 2:
            continue
        groups.append(
            {
                "content_hash": h,
                "doc_ids": [d.id for d in lst],
                "doc_names": [getattr(d, "name", "") or "" for d in lst],
                "count": len(lst),
            }
        )
    groups.sort(key=lambda g: g["content_hash"])
    return groups
