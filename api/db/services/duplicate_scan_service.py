"""Document Duplicate Scan: exact (content_hash) and near (embedding cosine) grouping over one Dataset."""

import logging
import math

from common import settings

logger = logging.getLogger(__name__)

NO_EMBEDDING_MODEL = "dataset has no embedding model, near-duplicate scan unavailable"

# ponytail: 8k chars ≈ 8k tokens for most embedding models; truncate to the window
EMBEDDING_WINDOW = 8192


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


def current_version_texts(docs, dataset_id):
    """Read each document's Current Version bytes, one text per doc in doc order."""
    from api.db.services.file2document_service import File2DocumentService

    texts = []
    for d in docs:
        txt = None
        try:
            bucket, loc = File2DocumentService.get_storage_address(doc_id=d.id)
            blob = settings.STORAGE_IMPL.get(bucket or dataset_id, loc) if loc else None
            if isinstance(blob, (bytes, bytearray)):
                txt = blob.decode("utf-8", errors="ignore")
            elif isinstance(blob, str):
                txt = blob
        except Exception:  # noqa: BLE001 - unreadable blob falls back to name/id, same as the route did
            txt = None
        if not txt or not str(txt).strip():
            txt = getattr(d, "name", "") or d.id
        texts.append(txt[:EMBEDDING_WINDOW])
    return texts


def near_duplicate_groups(docs, vectors, threshold):
    """Cluster docs whose Current Version vectors are cosine >= threshold (union-find, O(n^2))."""
    n = len(docs)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if cosine_similarity(vectors[i], vectors[j]) >= threshold:
                union(i, j)

    buckets = {}
    for idx in range(n):
        buckets.setdefault(find(idx), []).append(idx)

    groups = []
    for idxs in buckets.values():
        if len(idxs) < 2:
            continue
        idxs.sort()
        max_s = max(cosine_similarity(vectors[a], vectors[b]) for pos, a in enumerate(idxs) for b in idxs[pos + 1 :])
        groups.append(
            {
                "doc_ids": [docs[k].id for k in idxs],
                "doc_names": [getattr(docs[k], "name", "") or "" for k in idxs],
                "count": len(idxs),
                "max_similarity": round(float(max_s), 4),
                "threshold": threshold,
            }
        )
    groups.sort(key=lambda g: g["doc_ids"][0])
    return groups


def scan(docs, dataset_id, mode="both", threshold=0.97, embed=None):
    """Run a Duplicate Scan over a Dataset's enabled Current-Version docs.

    ``embed`` maps collected texts to vectors with the Dataset's embedding
    model; pass ``None`` when the dataset has none. Raises when ``mode ==
    "embedding"`` and encoding fails; otherwise degrades to a warning.

    Returns the response payload: exact_groups, near_groups, totals, mode,
    threshold, and ``warning`` when the near-duplicate half was unavailable.
    """
    exact = exact_duplicate_groups(docs) if mode in ("exact", "both") else []
    near = []
    warning = None
    if mode in ("embedding", "both"):
        if embed is None:
            warning = NO_EMBEDDING_MODEL
        else:
            try:
                texts = current_version_texts(docs, dataset_id)
                if len(texts) >= 2:
                    near = near_duplicate_groups(docs, embed(texts), threshold)
            except Exception as ex:
                logger.warning("duplicate scan embedding failed: %s", ex)
                if mode == "embedding":
                    raise
                warning = f"embedding scan unavailable: {ex}"
                near = []
    data = {
        "exact_groups": exact,
        "near_groups": near,
        "total_exact_groups": len(exact),
        "total_near_groups": len(near),
        "mode": mode,
        "threshold": threshold,
    }
    if warning:
        data["warning"] = warning
    return data
