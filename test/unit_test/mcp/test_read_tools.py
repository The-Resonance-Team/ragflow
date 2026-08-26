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

import base64
import importlib.util
import re
from pathlib import Path

import pytest


def _load_mcp_server():
    server_path = Path(__file__).resolve().parents[3] / "mcp" / "server" / "server.py"
    spec = importlib.util.spec_from_file_location("ragflow_mcp_server_read_tools", server_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, payload=None, *, status_code=200, headers=None, content=b""):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


@pytest.fixture()
def mcp_server():
    return _load_mcp_server()


@pytest.fixture()
def connector(mcp_server):
    return mcp_server.RAGFlowConnector(base_url=mcp_server.BASE_URL)


def _registered_names(mcp_server):
    return [entry["name"] for entry in mcp_server._READ_TOOLS]


# ---------------------------------------------------------------- resolver --


def test_unknown_tool_resolves_to_none(mcp_server):
    assert mcp_server.resolve_read_tool_request("nonsense", {}) is None


def test_path_arguments_are_interpolated_and_removed_from_params(mcp_server):
    kind, path, params = mcp_server.resolve_read_tool_request("ragflow_list_chunks", {"dataset_id": "d1", "document_id": "doc1", "keywords": "ignored"})
    assert kind == "json"
    assert path == "/datasets/d1/documents/doc1/chunks"
    assert params == {}


def test_missing_path_argument_raises_value_error(mcp_server):
    with pytest.raises(ValueError, match="document_id"):
        mcp_server.resolve_read_tool_request("ragflow_list_chunks", {"dataset_id": "d1"})


def test_query_params_forwarded_with_bool_coercion(mcp_server):
    kind, path, params = mcp_server.resolve_read_tool_request(
        "ragflow_list_documents",
        {"dataset_id": "d1", "page": 2, "page_size": 5, "desc": True, "suffix": ["pdf"], "bogus": "x"},
    )
    assert kind == "json"
    assert path == "/datasets/d1/documents"
    assert params == {"page": 2, "page_size": 5, "desc": "true", "suffix": ["pdf"]}


def test_empty_values_are_not_forwarded(mcp_server):
    _, _, params = mcp_server.resolve_read_tool_request("ragflow_list_files", {"parent_id": "", "keywords": None, "page": 1})
    assert params == {"page": 1}


def test_diff_commits_from_and_to_are_query_params(mcp_server):
    kind, path, params = mcp_server.resolve_read_tool_request("ragflow_diff_commits", {"dataset_id": "d1", "from": "c1", "to": "c2"})
    assert path == "/datasets/d1/commits/diff"
    assert params == {"from": "c1", "to": "c2"}
    assert kind == "json"


def test_every_registered_tool_has_expected_shape(mcp_server):
    names = _registered_names(mcp_server)
    assert len(names) == len(set(names))
    for entry in mcp_server._READ_TOOLS:
        assert entry["kind"] in ("json", "base64")
        assert set(entry["required"]) <= set(entry["schema"])
        for placeholder in re.findall(r"{(\w+)}", entry["path"]):
            assert placeholder in entry["schema"]
            assert placeholder in entry["required"]


def test_registry_schemas_are_wellformed(mcp_server):
    schemas = {entry["name"]: mcp_server._input_schema(entry["schema"], entry.get("required")) for entry in mcp_server._READ_TOOLS}
    assert schemas["ragflow_get_dataset"]["required"] == ["dataset_id"]
    assert schemas["ragflow_get_dataset"]["type"] == "object"
    assert schemas["ragflow_download_file"]["properties"]["file_id"]["type"] == "string"
    assert "ragflow_retrieval" not in schemas


# ------------------------------------------------------------- proxy_json --/


async def _stub_get(monkeypatch, conn, responses):
    calls = []

    async def _get(path, params=None, api_key=""):
        calls.append({"path": path, "params": params, "api_key": api_key})
        return responses.pop(0) if responses else None

    monkeypatch.setattr(conn, "_get", _get)
    return calls


@pytest.mark.asyncio
async def test_proxy_json_strips_envelope(monkeypatch, connector):
    calls = await _stub_get(monkeypatch, connector, [_FakeResponse({"code": 0, "data": [1, 2], "total": 2})])

    payload = await connector.proxy_json(api_key="k", path="/datasets/d1")

    assert payload == {"data": [1, 2], "total": 2}
    assert calls[0]["path"] == "/datasets/d1"
    assert calls[0]["api_key"] == "k"


@pytest.mark.asyncio
async def test_proxy_json_surfaces_backend_error_message(monkeypatch, connector):
    await _stub_get(monkeypatch, connector, [_FakeResponse({"code": 100, "message": "You don't own the dataset d1."}, status_code=200)])

    with pytest.raises(Exception, match="You don't own the dataset"):
        await connector.proxy_json(api_key="k", path="/datasets/d1")


@pytest.mark.asyncio
async def test_proxy_json_without_api_key_fails_cleanly(monkeypatch, connector):
    calls = await _stub_get(monkeypatch, connector, [])

    with pytest.raises(Exception, match="Cannot process this operation"):
        await connector.proxy_json(api_key="", path="/datasets/d1")
    assert calls[0]["api_key"] == ""


@pytest.mark.asyncio
async def test_proxy_json_http_error_uses_message(monkeypatch, connector):
    await _stub_get(monkeypatch, connector, [_FakeResponse({"message": "unauthorized"}, status_code=401)])

    with pytest.raises(Exception, match="unauthorized"):
        await connector.proxy_json(api_key="bad-token", path="/datasets")


# ----------------------------------------------------------- proxy_base64 --/


@pytest.mark.asyncio
async def test_proxy_base64_encodes_payload_with_metadata(monkeypatch, connector):
    blob = b"PDF-bytes"
    response = _FakeResponse(
        headers={
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="report.pdf"',
        },
        content=blob,
    )
    await _stub_get(monkeypatch, connector, [response])

    payload = await connector.proxy_base64(api_key="k", path="/files/f1")

    assert payload["filename"] == "report.pdf"
    assert payload["size"] == len(blob)
    assert base64.b64decode(payload["content_base64"]) == blob


@pytest.mark.asyncio
async def test_proxy_base64_rejects_oversized_assets(monkeypatch, mcp_server, connector):
    big = b"x" * (mcp_server._MAX_BASE64_SOURCE_BYTES + 1)
    await _stub_get(monkeypatch, connector, [_FakeResponse(headers={"content-type": "application/octet-stream"}, content=big)])

    with pytest.raises(Exception, match="exceeding the"):
        await connector.proxy_base64(api_key="k", path="/files/f1")


@pytest.mark.asyncio
async def test_proxy_base64_surfaces_in_band_error_envelope(monkeypatch, connector):
    response = _FakeResponse({"code": 100, "message": "This file is empty."}, headers={"content-type": "application/json"})
    await _stub_get(monkeypatch, connector, [response])

    with pytest.raises(Exception, match="This file is empty."):
        await connector.proxy_base64(api_key="k", path="/files/f1")
