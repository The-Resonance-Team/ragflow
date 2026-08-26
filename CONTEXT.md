# RAGFlow UI Translation

Glossary for RAGFlow's product vocabulary and its Vietnamese localization. Each product term fixes the canonical Vietnamese rendering used across all locale files; every translator must reuse these exact renderings.

## Language

### Product surfaces

**Dataset**:
A curated collection of documents a user builds for retrieval-augmented generation.
Vietnamese: _Cơ sở kiến thức_. _Avoid_: tập dữ liệu, bộ dữ liệu.

**Knowledge Base**:
Legacy name for a Dataset; both map to the same object.
Vietnamese: _cơ sở kiến thức_ (lowercase mid-sentence).

**Chunk**:
One text segment produced by splitting a parsed document.
Vietnamese: _khối_. _Avoid_: đoạn kiến thức, đoạn văn bản, phân đoạn.

**Agent**:
A visual workflow program that orchestrates LLM calls on the canvas.
Vietnamese: keep **Agent** (loanword). _Avoid_: tác nhân, đại lý.

**Canvas**:
The visual editing surface where an Agent's operators are arranged.
Vietnamese: keep **canvas** (loanword).

**Operator**:
A single node type on the canvas (Begin, Generate Answer, Retrieval, …).
Vietnamese: _toán tử_.

**Workflow**:
The end-to-end flow defined by an Agent on the canvas.
Vietnamese: _quy trình_. _Avoid_: luồng công việc, quy trình làm việc.

**Skill**:
A reusable capability package an Agent or assistant can invoke.
Vietnamese: _kỹ năng_.

**Memory**:
Persistent conversational or working context retained by an Agent.
Vietnamese: _bộ nhớ_. _Avoid__: ghi nhớ, trí nhớ.

**Assistant**:
A chat-facing agent bound to datasets and model settings.
Vietnamese: _trợ lý_. _Avoid_: trợ lí, bot.

**Prompt**:
Instruction text sent to an LLM (system or user role).
Vietnamese: keep **prompt** (loanword). _Avoid_: lời nhắc, nhắc nhở.

**Retrieval**:
Fetching chunks relevant to a query from a dataset.
Vietnamese: _truy hồi_. _Avoid_: truy xuất, thu hồi.

**Embedding**:
Vector representation of text produced by an embedding model.
Vietnamese: _nhúng_. _Avoid_: embedding vector, vector hóa.

**Parse**:
Extracting structured content from an uploaded document.
Vietnamese: _phân tích cú pháp_. _Avoid_: phân tích tài liệu, xử lý.

**Template**:
A prebuilt Agent or configuration users start from.
Vietnamese: _mẫu_.

**Tenant**:
An isolated account space owning models, datasets, and teams.
Vietnamese: keep **Tenant** (loanword). _Avoid_: người thuê, đơn vị thuê.

**Team**:
Users sharing access to a tenant's resources.
Vietnamese: _Nhóm_. _Avoid_: đội.

**Token**:
Unit of LLM text accounting; also authentication tokens.
Vietnamese: keep **token** (loanword).

**MCP**:
Model Context Protocol integration surface.
Vietnamese: keep **MCP**.

### Translation process

**Key parity**:
Property that every leaf key in `en.ts` exists in every other locale file with identical key path. _Avoid_: full coverage, sync.

**Placeholder preservation**:
Requirement that interpolation markers (`{{name}}`) inside a translated string match the source string's set exactly. _Avoid_: variable keeping.

**Fallback**:
i18next behavior of showing the English string (or raw key) when a locale lacks a translation. Mixed-language screens are caused by missing keys, not by fallback misconfiguration.
