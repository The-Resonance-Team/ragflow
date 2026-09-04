"""Unit test for document duplicate scan (exact hash + embedding)."""

import pytest

from api.db.services.duplicate_scan_service import NO_EMBEDDING_MODEL, cosine_similarity, exact_duplicate_groups, scan


class _Doc:
    def __init__(self, doc_id, name, content_hash, status="1"):
        self.id = doc_id
        self.name = name
        self.content_hash = content_hash
        self.status = status


def test_cosine_identical():
    assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-6
    assert abs(cosine_similarity([1, 1], [1, 1]) - 1.0) < 1e-6


def test_cosine_orthogonal():
    assert abs(cosine_similarity([1, 0], [0, 1]) - 0.0) < 1e-6


def test_cosine_zero_vector():
    assert cosine_similarity([0, 0], [1, 0]) == 0.0


def test_exact_groups_basic():
    docs = [
        _Doc("d1", "a.pdf", "abc"),
        _Doc("d2", "b.pdf", "abc"),
        _Doc("d3", "c.pdf", "xyz"),
        _Doc("d4", "d.pdf", "xyz"),
        _Doc("d5", "e.pdf", "unique"),
        _Doc("d6", "f.pdf", ""),  # empty hash ignored
        _Doc("d7", "g.pdf", None),  # None ignored
    ]
    groups = exact_duplicate_groups(docs)
    assert len(groups) == 2
    # sorted by content_hash
    assert groups[0]["content_hash"] == "abc"
    assert set(groups[0]["doc_ids"]) == {"d1", "d2"}
    assert groups[1]["content_hash"] == "xyz"
    assert groups[1]["count"] == 2


def test_exact_groups_no_duplicates():
    docs = [_Doc("d1", "a.pdf", "h1"), _Doc("d2", "b.pdf", "h2")]
    groups = exact_duplicate_groups(docs)
    assert groups == []


def test_exact_groups_empty():
    assert exact_duplicate_groups([]) == []


def test_exact_ignores_empty_hash():
    docs = [_Doc("d1", "a.pdf", ""), _Doc("d2", "b.pdf", ""), _Doc("d3", "c.pdf", "  ")]
    assert exact_duplicate_groups(docs) == []


def _dup_docs():
    return [_Doc("d1", "same text", "abc"), _Doc("d2", "same text", "abc"), _Doc("d3", "other text", "xyz")]


def test_scan_exact_only():
    data = scan(_dup_docs(), "kb-1", mode="exact", threshold=0.97, embed=None)
    assert data["total_exact_groups"] == 1
    assert data["near_groups"] == []
    assert "warning" not in data


def test_scan_both_without_embedding_model_warns():
    data = scan(_dup_docs(), "kb-1", mode="both", threshold=0.97, embed=None)
    assert data["warning"] == NO_EMBEDDING_MODEL
    assert data["total_exact_groups"] == 1
    assert data["near_groups"] == []


def test_scan_clusters_near_duplicates_via_injected_embed():
    vectors = {"same text": [1.0, 0.0], "other text": [0.0, 1.0]}

    def embed(texts):
        return [vectors[t] for t in texts]

    data = scan(_dup_docs(), "kb-1", mode="both", threshold=0.97, embed=embed)
    assert data["total_near_groups"] == 1
    group = data["near_groups"][0]
    assert set(group["doc_ids"]) == {"d1", "d2"}
    assert group["max_similarity"] > 0.99


def test_scan_embed_failure_warns_in_both_and_raises_in_embedding_mode():
    def broken_embed(_texts):
        raise RuntimeError("model down")

    docs = _dup_docs()
    data = scan(docs, "kb-1", mode="both", threshold=0.97, embed=broken_embed)
    assert "model down" in data["warning"]
    assert data["near_groups"] == []
    assert data["total_exact_groups"] == 1

    with pytest.raises(RuntimeError):
        scan(docs, "kb-1", mode="embedding", threshold=0.97, embed=broken_embed)
