import json
import os
from pathlib import Path
import sys
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


def test_system_agent_uses_read_file_for_framework_question(monkeypatch) -> None:
    scripted = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            _tool_call("call-1", "read_file", {"path": "backend/app/main.py"})
                        ],
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"answer":"The backend uses FastAPI.",'
                            '"source":"backend/app/main.py#app-fastapi"}'
                        )
                    }
                }
            ]
        },
    ]

    def fake_chat_completion(messages, tools):  # noqa: ANN001, ANN202
        return scripted.pop(0)

    monkeypatch.setattr(agent, "_chat_completion", fake_chat_completion)
    result = agent.run_agent("What framework does the backend use?")

    assert any(tc["tool"] == "read_file" for tc in result["tool_calls"])
    assert "FastAPI" in result["answer"]


def test_system_agent_uses_query_api_for_data_question(monkeypatch) -> None:
    scripted = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            _tool_call(
                                "call-2",
                                "query_api",
                                {"method": "GET", "path": "/items/"},
                            )
                        ],
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"answer":"There are 2 items in the database.","source":""}'
                        )
                    }
                }
            ]
        },
    ]

    def fake_chat_completion(messages, tools):  # noqa: ANN001, ANN202
        return scripted.pop(0)

    def fake_request(self, method, url, headers=None, **kwargs):  # noqa: ANN001, ANN202
        assert method == "GET"
        assert url.endswith("/items/")
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    monkeypatch.setattr(agent, "_chat_completion", fake_chat_completion)
    monkeypatch.setattr(httpx.Client, "request", fake_request)
    monkeypatch.setenv("LMS_API_KEY", "test-lms-key")
    monkeypatch.setenv("AGENT_API_BASE_URL", "http://localhost:42002")

    result = agent.run_agent("How many items are in the database?")

    assert any(tc["tool"] == "query_api" for tc in result["tool_calls"])
    query_result = next(tc for tc in result["tool_calls"] if tc["tool"] == "query_api")
    payload = json.loads(query_result["result"])
    assert payload["status_code"] == 200
