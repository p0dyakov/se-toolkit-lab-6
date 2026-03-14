import json
import sys
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import agent


def _tool_call(tool_id: str, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": tool_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def test_llm_retry_backoff_recovers_after_rate_limit(monkeypatch) -> None:
    attempts = {"count": 0}

    def fake_post(self, url, headers=None, json=None):  # noqa: ANN001, ANN202
        attempts["count"] += 1
        request = httpx.Request("POST", url)
        if attempts["count"] == 1:
            return httpx.Response(429, request=request, json={"error": "rate limit"})
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": '{"answer":"ok","source":"x"}'}}]},
        )

    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("LLM_API_BASE", "https://example.test")
    monkeypatch.setenv("LLM_MODEL", "demo-model")
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    monkeypatch.setattr(agent.time, "sleep", lambda _seconds: None)

    data = agent._chat_completion(messages=[{"role": "user", "content": "ping"}], tools=[])

    assert attempts["count"] == 2
    assert data["choices"][0]["message"]["content"]


def test_tool_cache_avoids_duplicate_read_file_calls(monkeypatch) -> None:
    scripted = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [_tool_call("call-1", "read_file", {"path": "README.md"})],
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [_tool_call("call-2", "read_file", {"path": "README.md"})],
                    }
                }
            ]
        },
        {"choices": [{"message": {"content": '{"answer":"done","source":"README.md"}'}}]},
    ]
    calls = {"read_file": 0}

    def fake_chat_completion(messages, tools):  # noqa: ANN001, ANN202
        return scripted.pop(0)

    def fake_read_file(path: str) -> str:
        calls["read_file"] += 1
        return f"file-content:{path}"

    monkeypatch.setattr(agent, "_chat_completion", fake_chat_completion)
    monkeypatch.setattr(agent, "_read_file", fake_read_file)

    result = agent.run_agent("read twice")

    assert result["answer"] == "done"
    assert calls["read_file"] == 1
    assert len(result["tool_calls"]) == 2
    assert result["tool_calls"][0]["cache_hit"] is False
    assert result["tool_calls"][1]["cache_hit"] is True
