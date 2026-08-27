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
import json
from pathlib import Path

import pytest


def _load_mcp_server():
    server_path = Path(__file__).resolve().parents[3] / "mcp" / "server" / "server.py"
    spec = importlib.util.spec_from_file_location("ragflow_mcp_server_chat", server_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, payload, *, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.fixture()
def mcp_server():
    return _load_mcp_server()


@pytest.fixture()
def connector(mcp_server):
    return mcp_server.RAGFlowConnector(base_url=mcp_server.BASE_URL)


@pytest.mark.asyncio
async def test_chat_completion_proxies_to_chat_completions_and_returns_data(connector):
    calls = {}

    async def _post(path, json=None, stream=False, files=None, api_key=""):
        calls["path"] = path
        calls["json"] = json
        calls["api_key"] = api_key
        return _FakeResponse({"code": 0, "data": {"answer": "hello", "session_id": "s1", "reference": {"chunks": []}}})

    connector._post = _post  # type: ignore[method-assign]

    result = await connector.chat_completion(api_key="tok", chat_id="chat-1", question="hi")

    assert calls["path"] == "/chat/completions"
    assert calls["json"] == {"chat_id": "chat-1", "question": "hi", "stream": False}
    assert calls["api_key"] == "tok"
    payload = json.loads(result[0].text)
    assert payload["answer"] == "hello"
    assert payload["session_id"] == "s1"


@pytest.mark.asyncio
async def test_chat_completion_forwards_session_id_when_present(connector):
    async def _post(path, json=None, stream=False, files=None, api_key=""):
        assert json["session_id"] == "sess-xyz"
        return _FakeResponse({"code": 0, "data": {"answer": "follow", "session_id": "sess-xyz", "reference": {}}})

    connector._post = _post  # type: ignore[method-assign]

    result = await connector.chat_completion(api_key="tok", chat_id="c1", question="follow", session_id="sess-xyz")

    assert json.loads(result[0].text)["session_id"] == "sess-xyz"


@pytest.mark.asyncio
async def test_chat_requires_chat_id_and_question(connector):
    with pytest.raises(Exception, match="chat_id and question are required"):
        await connector.chat_completion(api_key="tok", chat_id="", question="hi")
    with pytest.raises(Exception, match="chat_id and question are required"):
        await connector.chat_completion(api_key="tok", chat_id="c1", question="")


@pytest.mark.asyncio
async def test_chat_completion_surfaces_backend_error(connector):
    async def _post(path, json=None, stream=False, files=None, api_key=""):
        return _FakeResponse({"code": 102, "message": "Chat not found!"}, status_code=200)

    connector._post = _post  # type: ignore[method-assign]

    with pytest.raises(Exception, match="Chat not found"):
        await connector.chat_completion(api_key="tok", chat_id="bad", question="hi")


def test_list_tools_includes_chat_completion(mcp_server):
    # ponytail: verify the tool is registered — fails if the 3-line addition is reverted
    src = Path(mcp_server.__file__).read_text()  # type: ignore[attr-defined]
    assert "ragflow_chat_completion" in src
    assert '"chat_id"' in src or "'chat_id'" in src
