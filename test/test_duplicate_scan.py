"""Unit test for document duplicate scan (exact hash + embedding)."""

from api.db.services.duplicate_scan_service import cosine_similarity, exact_duplicate_groups


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
