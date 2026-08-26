#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import importlib.util
from pathlib import Path

import pytest


def _load_mcp_server():
    server_path = Path(__file__).resolve().parents[3] / "mcp" / "server" / "server.py"
    spec = importlib.util.spec_from_file_location("ragflow_mcp_server_auth", server_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def mcp_server():
    return _load_mcp_server()


async def _drive_asgi(app, method, path, headers=None):
    """Invoke the ASGI app directly, bypassing any test-client shims."""
    received = {"status": None, "body": b""}
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            received["status"] = message["status"]
        elif message["type"] == "http.response.body":
            received["body"] += message.get("body", b"")

    await app(scope, receive, send)
    return received


def _bearer(value):
    return {"Authorization": f"Bearer {value}"}


# ------------------------------------------------- token header extraction --


def test_bearer_token_extracted(mcp_server):
    assert mcp_server._extract_token_from_headers({"authorization": "Bearer ragflow-abc123"}) == "ragflow-abc123"


def test_api_key_header_extracted(mcp_server):
    assert mcp_server._extract_token_from_headers({"x-api-key": "tok"}) == "tok"


def test_missing_token_returns_none(mcp_server):
    assert mcp_server._extract_token_from_headers({}) is None


def test_non_bearer_authorization_is_ignored(mcp_server):
    assert mcp_server._extract_token_from_headers({"authorization": "Basic dXNlcjpwYXNz"}) is None


# --------------------------------------------- host-mode middleware gating --


@pytest.mark.asyncio
async def test_host_mode_rejects_missing_token_with_401(mcp_server, monkeypatch):
    monkeypatch.setattr(mcp_server, "MODE", mcp_server.LaunchMode.HOST)
    app = mcp_server.create_starlette_app()

    get_response = await _drive_asgi(app, "GET", "/mcp")
    post_response = await _drive_asgi(app, "POST", "/mcp")

    assert get_response["status"] == 401
    assert post_response["status"] == 401
    assert b"Missing or invalid authorization header" in get_response["body"]


@pytest.mark.asyncio
async def test_host_mode_gates_sse_paths_too(mcp_server, monkeypatch):
    monkeypatch.setattr(mcp_server, "MODE", mcp_server.LaunchMode.HOST)
    monkeypatch.setattr(mcp_server, "TRANSPORT_SSE_ENABLED", True)
    app = mcp_server.create_starlette_app()

    sse_response = await _drive_asgi(app, "GET", "/sse")

    assert sse_response["status"] == 401


@pytest.mark.asyncio
async def test_host_mode_passes_present_tokens_through(mcp_server, monkeypatch):
    """Any well-formed token crosses the middleware; validity is enforced by the
    backend REST call inside tool invocation, not at the MCP door."""
    monkeypatch.setattr(mcp_server, "MODE", mcp_server.LaunchMode.HOST)
    app = mcp_server.create_starlette_app()

    # Without a started streamable session the request proceeds past auth into the
    # transport layer, which fails on the uninitialized task group — anything but
    # the middleware's own 401 proves the token crossed the gate.
    try:
        response = await _drive_asgi(app, "GET", "/mcp", headers=_bearer("not-a-valid-token-yet"))
        assert response["status"] != 401
    except RuntimeError as exc:
        assert "Task group is not initialized" in str(exc)


@pytest.mark.asyncio
async def test_self_host_mode_has_no_transport_gate(mcp_server, monkeypatch):
    monkeypatch.setattr(mcp_server, "MODE", mcp_server.LaunchMode.SELF_HOST)
    app = mcp_server.create_starlette_app()

    try:
        response = await _drive_asgi(app, "GET", "/mcp")
        assert response["status"] != 401
    except RuntimeError as exc:
        assert "Task group is not initialized" in str(exc)


# ------------------------------------------------ connector empty-key guard --


@pytest.mark.asyncio
async def test_connector_refuses_calls_without_api_key(mcp_server, monkeypatch):
    connector = mcp_server.RAGFlowConnector(base_url=mcp_server.BASE_URL)
    calls = []

    async def _get(path, params=None, api_key=""):
        calls.append(api_key)

    monkeypatch.setattr(connector, "_get", _get)

    with pytest.raises(Exception, match="Cannot process this operation"):
        await connector.proxy_json(api_key="", path="/datasets")

    assert calls == [""]
