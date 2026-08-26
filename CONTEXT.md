# RAGFlow Retrieval Exposure

Glossary for exposing RAGFlow's retrieval capability to external agents via MCP.

## Language

### Serving topology

**Serving side**:
RAGFlow acting as an MCP server: external agents connect to it and invoke read-only tools.
_Avoid_: server mode (ambiguous with self-host/host)

**Client side**:
RAGFlow consuming external MCP servers from inside its own agents and chats.
_Avoid_: consumer mode

### Launch modes

**Self-host mode**:
Single-tenant serving: one credential fixed at launch, callers are not individually authenticated.

**Host mode**:
Multi-tenant serving: every caller must present their own credential and sees only what it can access.

### Credentials

**API token**:
A caller credential issued by RAGFlow, presented as a Bearer header, identifying exactly one tenant.
_Avoid_: API key, host key

### Knowledge model

**Dataset**:
A named collection of ingested documents owned by a tenant.
_Avoid_: knowledge base, KB

**Document**:
One ingested source file inside a dataset.

**Chunk**:
The retrievable passage unit derived from a document; carries content plus a similarity score at retrieval time.

**Retrieval**:
Ranked search over chunks across datasets, always scoped to what the calling tenant may access.
