# RAGFlow

RAGFlow is a retrieval-augmented generation (RAG) engine: users curate document collections, parse them into retrievable units, and serve them to LLM-powered agents and chats.

Glossary for RAGFlow's product vocabulary and its Vietnamese localization. Each product term fixes the canonical Vietnamese rendering used across all locale files; every translator must reuse these exact renderings.

## Language

### Core resources

**Dataset**:
The primary user-created resource: a named collection of documents plus its configuration (embedding model, chunking method, permissions). Formerly called "Knowledge Base"; the UI now says Dataset everywhere. A curated collection of documents a user builds for retrieval-augmented generation.
Vietnamese: _Tập dữ liệu_ (legacy rendering: _Cơ sở kiến thức_).
_Avoid_: Knowledge base, KB, corpus, bộ dữ liệu

**Document**:
A single file inside a Dataset, with its own parsing status and metadata.
_Avoid_: File (except when referring to the raw uploaded file itself)

**Chunk**:
One retrievable unit of parsed document content. Counted per document; produced by the chosen chunking method. One text segment produced by splitting a parsed document.
Vietnamese: _khối_ (chunking as verb: _phân khối_).
_Avoid_: Segment, piece, đoạn kiến thức, đoạn văn bản, phân đoạn

**Chunking method**:
The strategy that splits a parsed document into chunks (General, Q&A, Paper, Manual, …).
Vietnamese: _Phương thức phân khối_
_Avoid_: Parser, category

**Parsing** / **Parse**:
Running a Document through its chunking method to produce chunks. Statuses: pending, parsing, cancelled, success, fail. Extracting structured content from an uploaded document.
Vietnamese: _Phân tích cú pháp_
_Avoid_: Indexing, processing, phân tích tài liệu, xử lý (for this specific step)

**Embedding model**:
The model that vectorizes chunks for retrieval; bound per Dataset and switchable only under similarity constraints.
Vietnamese: _Mô hình nhúng_
_Avoid_: Vector model

**Embedding**:
Vector representation of text produced by an embedding model.
Vietnamese: _nhúng_
_Avoid_: embedding vector, vector hóa

**Metadata**:
User-defined structured fields attached to Documents or Datasets, optionally auto-generated during parsing.
Vietnamese: _Siêu dữ liệu_
_Avoid_: Meta data, Data meta

**Pipeline**:
A configurable ingestion workflow (parse → chunk → …) that a Dataset can link to instead of a built-in chunking method.
Vietnamese: _Pipeline_ (kept as loanword)
_Avoid_: Data flow, workflow (for this concept)

**Knowledge graph**:
An extraction artifact over a Dataset's chunks: entities, relationships, communities.
Vietnamese: _Đồ thị tri thức_
_Avoid_: Graph, mind map

### Document versioning

**Duplicate-name Upload**:
An upload whose filename matches an existing document in the same dataset.
_Avoid_: Silent duplicate (the old behavior this term replaces)

**Conflict**:
A duplicate-name upload for which the caller must choose an outcome before anything is stored.
_Avoid_: Collision, clash

**Keep Both**:
Resolving a conflict by storing the incoming file as a new document under an auto-renamed name.
_Avoid_: Rename, auto-rename

**Replacement Upload**:
Resolving a conflict by storing the incoming bytes as a new version of the existing document.
_Avoid_: Overwrite, update-in-place

**Document Version**:
An immutable record of a document's content at one point in time; its bytes can never be modified after creation.
_Avoid_: Revision, snapshot

**Current Version**:
The document version whose bytes are used for parsing, download, and display by default.
_Avoid_: Head, live version

**Restore**:
Making a past Document Version the Current Version again by recording it as a new immutable version (v(N+1)) that reuses its bytes and re-runs parsing. History retains both the original and the restore entry.
_Avoid_: Rollback, revert, recover

**Version Origin**:
Whether a Document Version was created by an `upload` (initial or replacement) or by a `restore`. Stored per version so the timeline can show it without heuristics.
_Avoid_: Source, type

### Duplicate detection

**Exact Duplicate**:
Two Documents in the same Dataset whose `content_hash` (`xxhash128` of Current Version bytes) is identical and non-empty. Byte-identical content regardless of filename.
Vietnamese: _bản sao chính xác_
_Avoid_: identical document, hash duplicate

**Near Duplicate**:
Two Documents in the same Dataset whose Current Version texts have cosine similarity ≥ threshold when embedded with the Dataset's `embd_id` model. Semantic duplicate, not byte-identical.
Vietnamese: _bản sao gần đúng_
_Avoid_: similar document, embedding duplicate

**Duplicate Scan**:
A read-only operation over a single Dataset that groups enabled Documents' Current Versions into exact groups (by `content_hash`) and optionally near groups (by embedding cosine). Scoped to one Dataset, never deletes or merges.
Vietnamese: _quét trùng lặp_
_Avoid_: dedup scan, duplicate detection job

### Product surfaces

**Knowledge Base**:
Legacy name for a Dataset; both map to the same object.
Vietnamese: _cơ sở kiến thức_ (lowercase mid-sentence, legacy).

**Agent**:
A visual workflow program that orchestrates LLM calls on the canvas.
Vietnamese: keep **Agent** (loanword).
_Avoid_: tác nhân, đại lý

**Canvas**:
The visual editing surface where an Agent's operators are arranged.
Vietnamese: keep **canvas** (loanword).

**Operator**:
A single node type on the canvas (Begin, Generate Answer, Retrieval, …).
Vietnamese: _toán tử_

**Workflow**:
The end-to-end flow defined by an Agent on the canvas.
Vietnamese: _quy trình_
_Avoid_: luồng công việc, quy trình làm việc

**Skill**:
A reusable capability package an Agent or assistant can invoke.
Vietnamese: _kỹ năng_

**Memory**:
Persistent conversational or working context retained by an Agent.
Vietnamese: _bộ nhớ_
_Avoid__: ghi nhớ, trí nhớ

**Assistant**:
A chat-facing agent bound to datasets and model settings. Code name **Dialog** (`DialogService`, REST `/api/v1/chats`); UI and MCP surface call it **Chat assistant** or **Assistant** interchangeably — one concept, one Vietnamese rendering.
Vietnamese: _trợ lý_
_Avoid_: trợ lí, bot, Chat (as noun for the assistant itself)

**Session** (Assistant):
A single conversation thread under one Assistant, identified by `session_id` (`conversation_id` alias in REST, `id` in `ConversationService`). Stores ordered `message` history and per-turn `reference` citations. Created on first `chat_completion` when `session_id` is absent; continued when `session_id` is supplied.
_Avoid_: Conversation (code legacy), thread, chat session (ambiguous)

**Prompt**:
Instruction text sent to an LLM (system or user role).
Vietnamese: keep **prompt** (loanword).
_Avoid_: lời nhắc, nhắc nhở

**Retrieval**:
Fetching chunks relevant to a query from a dataset — ranked search where each chunk carries content plus a similarity score, always scoped to what the calling tenant may access.
Vietnamese: _truy hồi_
_Avoid_: truy xuất, thu hồi

**Template**:
A prebuilt Agent or configuration users start from.
Vietnamese: _mẫu_

**Tenant**:
An isolated account space owning models, datasets, and teams.
Vietnamese: keep **Tenant** (loanword).
_Avoid_: người thuê, đơn vị thuê

**Team**:
Users sharing access to a tenant's resources.
Vietnamese: _Nhóm_
_Avoid_: đội

**Token**:
Unit of LLM text accounting; also authentication tokens.
Vietnamese: keep **token** (loanword).

**MCP**:
Model Context Protocol integration surface.
Vietnamese: keep **MCP**.

### MCP serving

**Serving side** (MCP):
RAGFlow acting as an MCP server: external agents connect to it and invoke tools. The standalone Python MCP server (`mcp/server/server.py`) is this serving side. Original serving was read-only (retrieval, dataset reads); the assistant chat tool is generation but still tenant-scoped and read-side-effect-limited to adding `Session` messages.
_Avoid_: server mode (ambiguous with self-host/host)

**Client side** (MCP):
RAGFlow consuming external MCP servers from inside its own agents and chats.
_Avoid_: consumer mode

**Self-host mode** (MCP):
Single-tenant serving: one credential fixed at launch, callers are not individually authenticated.

**Host mode** (MCP):
Multi-tenant serving: every caller must present their own credential and sees only what it can access.

**API token** (MCP):
A caller credential issued by RAGFlow, presented as a Bearer header, identifying exactly one tenant. Forwarded per-request to the backing REST API so permission scoping is inherited.
_Avoid_: API key, host key

### Translation process

**Key parity**:
Property that every leaf key in `en.ts` exists in every other locale file with identical key path.
_Avoid_: full coverage, sync

**Placeholder preservation**:
Requirement that interpolation markers (`{{name}}` or `{variable_name}`) inside a translated string match the source string's set exactly.
_Avoid_: variable keeping

**Fallback**:
i18next behavior of showing the English string (or raw key) when a locale lacks a translation. Mixed-language screens are caused by missing keys, not by fallback misconfiguration.

## Vietnamese (vi) rendering policy

UI chrome and everyday words are translated fully. Domain terms above use the listed Vietnamese renderings consistently; product/brand tokens stay in English (Agent, RAPTOR, MinerU, PaddleOCR, Discord, GitHub). When English renames a concept (e.g. Knowledge Base → Dataset), Vietnamese follows the new name (Tập dữ liệu) rather than preserving the legacy rendering (Cơ sở kiến thức).
