# Document duplicate scan: exact hash + embedding, synchronous, dataset-scoped read-only

Dataset contents diverge by re-upload and near-copies; users need a read-only scan that surfaces exact (`xxhash128` of Current Version bytes) and near (embedding cosine ≥ threshold via the Dataset's `embd_id`) duplicate groups within one Dataset. We expose `GET /datasets/{id}/documents/duplicate-scan?mode=both&threshold=0.97` as a synchronous, paginated, read-only report scoped to enabled Documents' Current Versions; it never deletes or merges and has no persisted embedding cache.

## Considered Options

- Async job with polling / persisted embedding column — rejected: adds queue, state, and GC for a scan that is a single indexed `GROUP BY content_hash` plus a bounded `O(n²)` cosine over at most a few thousand docs; async can be added later if scan exceeds ~5s.
- Cross-dataset or tenant-wide scan — rejected: permission scoping and embedding-model heterogeneity (`validate_dataset_embedding_models`) make the contract surprising; one-dataset retains the tenant boundary already enforced by `KnowledgebaseService.accessible`.
- Auto-dedupe (delete/disable/merge on scan) — rejected: data loss at trust boundary; actions stay on existing `DELETE /documents` and status endpoints.
- Content-addressed blob store or embedding cache table — rejected: forces reference counting/GC and couples scan to storage; scan recomputes from Current Version bytes and can cache later (`ponytail: O(n²) scan, add cached doc embedding + ANN if dataset >5k docs`).

## Consequences

- Exact scan is one DB query (`content_hash` grouping); embedding scan encodes current bytes truncated to embedding window and clusters by threshold (order-preserving, keep first).
- Threshold is caller-supplied `threshold` (default 0.97, clamp 0.80–0.99); `mode` selects `exact|embedding|both`; disabled documents and historical versions are excluded.
- No migration; no new tables; both Python (`api/apps/restful_apis/document_api.py`) and Go (`internal/handler/document.go` + `internal/service/document`) serve the same contract.
