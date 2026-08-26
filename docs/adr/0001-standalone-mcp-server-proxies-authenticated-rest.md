# Serving side lives in the standalone MCP server, proxying caller-authenticated REST

RAGFlow exposes its knowledge plane to external agents via MCP. We keep this serving side in
the standalone Python MCP server process (`mcp/server/server.py`) instead of mounting MCP into
the Quart app or extending the Go embedded JSON-RPC server. Every MCP tool is a thin proxy to an
existing authenticated REST route, forwarding the caller's own Bearer token, so permission
scoping is inherited from the REST API and implemented exactly once.

## Considered options

- Mounting an MCP blueprint inside the Quart app was rejected: it would duplicate a fully working
  streamable-HTTP/SSE server and create a third serving path alongside the Python standalone
  server and the Go embedded one.
- Extending the Go embedded MCP server to streamable HTTP was rejected: it serves the Go beta-API
  consumer surface and lacks session transports; converging the two is a separate refactor.
- Eager token validation at the transport layer was rejected: a bad token already fails cleanly at
  first backend call; probing per request adds latency and couples liveness.

## Consequences

- All knowledge-plane reads exposed as tools stay read-only; generation/completion endpoints and
  control-plane reads are deliberately not exposed.
- Binary assets are returned base64-encoded within size caps; graph payloads are size-capped.
- Host mode is the multi-caller posture (per-caller tokens); self-host mode remains the default
  single-tenant launch mode with a fixed credential.
