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

The MCP server exposes RAGFlow's knowledge plane to external agents as **read-only tools**. Every tool is a thin, authenticated proxy to a REST route: the caller's own API key scopes what each tool can see, so an agent can never read past its tenant's permissions.

## Core retrieval tools

- **ragflow_retrieval**: Fetches relevant chunks from specified `dataset_ids` and optional `document_ids` using the RAGFlow retrieve interface, based on a given question. Details of all available datasets, namely, `id` and `description`, are provided within the tool description for each individual dataset.
- **ragflow_list_datasets**: Lists all accessible datasets (id, name, description).
- **ragflow_list_chats**: Lists all accessible chat assistants.

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

Generation-oriented endpoints (chat/agent completions) and control-plane reads are deliberately not exposed.

## Connecting from opencode

```bash
opencode mcp add ragflow --transport http --url http://127.0.0.1:9382/mcp \
  --header "Authorization: Bearer <your-ragflow-api-key>"
```

Launch the server first in host mode:

```bash
uv run mcp/server/server.py --host=127.0.0.1 --port=9382 \
  --base-url=http://127.0.0.1:9380 --mode=host
```

For more information, see our Python implementation of the [MCP server](https://github.com/infiniflow/ragflow/blob/main/mcp/server/server.py).
