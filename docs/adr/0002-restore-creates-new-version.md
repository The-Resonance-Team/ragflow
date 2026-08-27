# Restore creates a new immutable version

Restoring a past document version must not move the current-version pointer in place. It records a new immutable version v(N+1) whose blob is a copy of the chosen version's bytes under a fresh versioned key `versions/{doc}/v(N+1)/{name}`, bumps the pointer, and resets parsing. Creating a new row (with `origin='restore'`) keeps the “every version row maps to exactly one immutable blob” invariant from ADR-0001, lets download address either the historical bytes or the restored current bytes independently, and makes recovery from a restore a normal restore of vN.

## Considered Options

- Move pointer only (no new row, reuse old `location`) — rejected: two versions would share one storage key, breaking the delete-CASCADE assumption and making “was this version uploaded or restored?” ambiguous.
- Snapshot table of version metadata separate from blob pointer — rejected: second concept for what ADR-0001 already calls a version.

## Consequences

- A restore that targets the already-current bytes short-circuits as a noop (no new row, no re-parse) rather than recording a redundant identical version.
- Version origin (`upload` vs `restore`) is stored, not inferred, so the timeline query stays trivial and future origins (if any) extend the same column.
