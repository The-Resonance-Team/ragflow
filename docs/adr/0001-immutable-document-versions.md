# Immutable document versions

Dataset-document uploads used to destroy information silently: a same-named upload was auto-renamed into a duplicate (`file(1).txt`), and doc-id-addressed uploads overwrote the stored blob in place, making previous bytes unrecoverable. We decided that every dataset upload records an immutable **Document Version** (v1 at first upload; blob written once under a per-document versioned key that is never mutated), and that a replacement upload resolves a name conflict by recording v(n+1), bumping the current-version pointer, and re-running parsing — never by overwriting bytes.

## Considered Options

- Reuse the workspace `FileCommit` machinery — rejected: it models page-edit diffs with a different lifecycle and would couple two domains.
- Record versions only from the first replacement onward — rejected: two write-path rules where one uniform invariant ("every stored blob is a version") is simpler.
- Content-addressed blob store (`.objects/{sha}`) — rejected: dedupes bytes but forces reference counting/GC onto every delete path; per-document versioned prefixes delete trivially.

## Consequences

- Every upload writes exactly one extra metadata row; identical-content replaces short-circuit via content-hash comparison rather than storing redundant versions.
- Deleting a document deletes its entire version prefix; there is no retention window.
- Legacy documents created before this change gain their first version row lazily, at the moment a replacement would otherwise orphan their bytes.
