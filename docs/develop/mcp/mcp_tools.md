---
sidebar_position: 2
title: RAGFlow MCP Tools
sidebar_label: RAGFlow MCP Tools
slug: /mcp_tools
sidebar_custom_props: {
  categoryIcon: LucideToolCase
}
---
# RAGFlow MCP Tools

The MCP server exposes RAGFlow's knowledge plane and assistant chat to external agents as **tools**. Every tool is a thin, authenticated proxy to a REST route: the caller's own API token scopes what each tool can see, so an agent can never read past its tenant's permissions. Transport is **streamable HTTP** (`POST /mcp`); the legacy SSE transport (`/sse`) remains for backward compatibility but is not required for the chat tool.

## Core tools

- **ragflow_retrieval**: Fetches relevant chunks from specified `dataset_ids` and optional `document_ids` using the RAGFlow retrieve interface, based on a given question. Details of all available datasets, namely, `id` and `description`, are provided within the tool description for each individual dataset.
- **ragflow_chat_completion**: Asks a RAGFlow **Assistant** (Chat assistant / Dialog) and returns a grounded answer with citations. See [Assistant chat](#assistant-chat) below.
- **ragflow_list_datasets**: Lists all accessible datasets (id, name, description).
- **ragflow_list_chats**: Lists all accessible chat assistants (id, name, description) — use to discover `chat_id` for `ragflow_chat_completion`.

## Knowledge-plane read tools

| Tool | Reads |
|---|---|
| `ragflow_get_dataset` | One dataset's full details by ID |
| `ragflow_list_dataset_tags` / `ragflow_aggregate_dataset_tags` | Dataset tags / cross-dataset tag counts |
| `ragflow_list_metadata_facets` / `ragflow_get_metadata_summary` | Metadata keys-values across datasets / per dataset |
| `ragflow_list_documents` | Documents in a dataset (paged) — use it to discover `document_ids` for targeted retrieval |
| `ragflow_list_chunks` | Stored chunks of a document in insertion order (no similarity ranking) |
| `ragflow_get_knowledge_graph` / `ragflow_get_structure_graph` | Dataset knowledge graph / document structure graph (size-capped responses) |
| `ragflow_get_ingestion_summary` / `ragflow_list_ingestions` / `ragflow_get_ingestion_log` | Parsing status rollup, runs, and logs |
| `ragflow_list_commits` / `ragflow_get_commit` / `ragflow_list_commit_files` / `ragflow_diff_commits` / `ragflow_get_commit_file_content` | Dataset workspace snapshot commits |
| `ragflow_list_files` | Files under a folder in the file area |
| `ragflow_get_document_thumbnails` | Thumbnails for a set of documents |
| `ragflow_download_file` / `ragflow_get_chunk_image` | Raw bytes base64-encoded; assets above 5 MB are rejected |

Other generation endpoints (agent completions) and control-plane writes are not exposed.

## Assistant chat

`ragflow_chat_completion` proxies `POST /api/v1/chat/completions` (non-streaming) under the caller's token. The assistant's bound datasets and LLM settings apply exactly as in the RAGFlow UI.

**Input**

| Field | Type | Required | Notes |
|---|---|---|---|
| `chat_id` | string | yes | Assistant id from `ragflow_list_chats` |
| `question` | string | yes | User question |
| `session_id` | string | no | Existing Session to continue; omit to create a new Session. The tool returns the `session_id` to reuse for the next turn. |

Multi-turn: call once without `session_id`, capture `session_id` from the returned JSON, then pass it on every follow-up. The server stores history (`store_history_messages=true`), so the next turn sees prior turns and citations. To run a stateless one-shot, simply omit `session_id` each time.

**Output** (JSON text, truncated at ~1 MB)

```json
{
  "answer": "The grounded answer with <cite> markers ...",
  "reference": {"chunks": [...], "doc_aggs": [...]},
  "session_id": "abc123",
  "id": "msg-uuid"
}
```

`reference.chunks` holds the cited chunks (content + scores + `document_id`/`dataset_id`). Errors (unknown `chat_id`, unauthorized, `session_id` not in assistant) surface the backend message.

## Connecting from opencode

### Host mode (recommended for teams)

Server verifies each caller; each request must carry that caller's own RAGFlow API token.

```bash
# 1. Start the MCP server in host mode
uv run mcp/server/server.py --host=127.0.0.1 --port=9382 \
  --base-url=http://127.0.0.1:9380 --mode=host

# 2. Register with opencode (streamable HTTP, per-call Bearer)
opencode mcp add ragflow --transport http --url http://127.0.0.1:9382/mcp \
  --header "Authorization: Bearer <your-ragflow-api-key>"
```

opencode stores the header and sends it on every tool call. Requests without a valid `Authorization: Bearer …` or `x-api-key` are rejected with `401 Missing or invalid authorization header` before any tool runs; an invalid token later surfaces the REST error `You don't own the dataset …` / `Chat not found`.

### Self-host mode (single tenant)

The server holds one fixed token; callers are not individually authenticated.

```bash
uv run mcp/server/server.py --host=127.0.0.1 --port=9382 \
  --base-url=http://127.0.0.1:9380 --mode=self-host --api-key=ragflow-xxxxx

opencode mcp add ragflow --transport http --url http://127.0.0.1:9382/mcp
```

## Full tool catalogue

| Tool | Kind | Description |
|---|---|---|
| `ragflow_retrieval` | retrieval | Similarity-ranked chunks for a question |
| `ragflow_chat_completion` | generation | Ask an Assistant, returns answer + citations + session_id |
| `ragflow_list_datasets` | discovery | List datasets |
| `ragflow_list_chats` | discovery | List chat assistants |
| `ragflow_get_dataset` | read | Get dataset by ID |
| `ragflow_list_dataset_tags` | read | List tags of a dataset |
| `ragflow_aggregate_dataset_tags` | read | Aggregate tag counts |
| `ragflow_list_metadata_facets` | read | List flattened metadata facets |
| `ragflow_get_metadata_summary` | read | Get metadata summary of a dataset |
| `ragflow_list_documents` | read | List documents in a dataset |
| `ragflow_list_chunks` | read | List chunks of a document |
| `ragflow_get_knowledge_graph` | read | Get dataset knowledge graph |
| `ragflow_get_structure_graph` | read | Get document structure graph |
| `ragflow_get_ingestion_summary` | read | Dataset ingestion summary |
| `ragflow_list_ingestions` | read | List ingestion runs |
| `ragflow_get_ingestion_log` | read | Get ingestion log |
| `ragflow_list_commits` | read | List workspace commits |
| `ragflow_get_commit` | read | Get commit |
| `ragflow_list_commit_files` | read | List files in a commit |
| `ragflow_diff_commits` | read | Diff two commits |
| `ragflow_get_commit_file_content` | read | Get file content from a commit |
| `ragflow_list_files` | read | List files in folder |
| `ragflow_get_document_thumbnails` | read | Get document thumbnails |
| `ragflow_download_file` | base64 | Download file bytes (5 MB cap) |
| `ragflow_get_chunk_image` | base64 | Fetch chunk image (5 MB cap) |

For more information, see our Python implementation of the [MCP server](https://github.com/infiniflow/ragflow/blob/main/mcp/server/server.py).
