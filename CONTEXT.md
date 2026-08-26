# RAGFlow

RAGFlow is a retrieval-augmented generation (RAG) engine: users curate document collections, parse them into retrievable units, and serve them to LLM-powered agents and chats.

## Language

### Core resources

**Dataset**:
The primary user-created resource: a named collection of documents plus its configuration (embedding model, chunking method, permissions). Formerly called "Knowledge Base"; the UI now says Dataset everywhere.
_Avoid_: Knowledge base, KB, corpus

**Document**:
A single file inside a Dataset, with its own parsing status and metadata.
_Avoid_: File (except when referring to the raw uploaded file itself)

**Chunk**:
One retrievable unit of parsed document content. Counted per document; produced by the chosen chunking method.
_Vietnamese_: Khối; chunking (verb) = phân khối
_Avoid_: Segment, piece

**Chunking method**:
The strategy that splits a parsed document into chunks (General, Q&A, Paper, Manual, …).
_Vietnamese_: Phương thức phân khối
_Avoid_: Parser, category

**Parsing**:
Running a Document through its chunking method to produce chunks. Statuses: pending, parsing, cancelled, success, fail.
_Vietnamese_: Phân tích cú pháp
_Avoid_: Indexing, processing (for this specific step)

**Embedding model**:
The model that vectorizes chunks for retrieval; bound per Dataset and switchable only under similarity constraints.
_Vietnamese_: Mô hình nhúng
_Avoid_: Vector model

**Metadata**:
User-defined structured fields attached to Documents or Datasets, optionally auto-generated during parsing.
_Vietnamese_: Siêu dữ liệu
_Avoid_: Meta data, Data meta

**Pipeline**:
A configurable ingestion workflow (parse → chunk → …) that a Dataset can link to instead of a built-in chunking method.
_Vietnamese_: Pipeline (kept as loanword)
_Avoid_: Data flow, workflow (for this concept)

**Knowledge graph**:
An extraction artifact over a Dataset's chunks: entities, relationships, communities.
_Vietnamese_: Đồ thị tri thức
_Avoid_: Graph, mind map

## Vietnamese (vi) rendering policy

UI chrome and everyday words are translated fully. Domain terms above use the listed Vietnamese renderings consistently; product/brand tokens stay in English (Agent, RAPTOR, MinerU, PaddleOCR, Discord, GitHub). When English renames a concept (e.g. Knowledge Base → Dataset), Vietnamese follows the new name rather than preserving the legacy rendering.
