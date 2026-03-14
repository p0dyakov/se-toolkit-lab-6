from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import agent


def _tool_call(tool_id: str, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": tool_id,
        "type": "function",
        "function": {"name": name, "arguments": __import__("json").dumps(args)},
    }


def test_documentation_agent_uses_read_file(monkeypatch) -> None:
    scripted = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            _tool_call(
                                "call-1",
                                "read_file",
                                {"path": "wiki/git-workflow.md"},
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
                            '{"answer":"Resolve markers, stage and commit.",'
                            '"source":"wiki/git-workflow.md#resolving-merge-conflicts"}'
                        )
                    }
                }
            ]
        },
    ]

    def fake_chat_completion(messages, tools):  # noqa: ANN001, ANN202
        return scripted.pop(0)

    monkeypatch.setattr(agent, "_chat_completion", fake_chat_completion)
    result = agent.run_agent("How do you resolve a merge conflict?")

    assert any(tc["tool"] == "read_file" for tc in result["tool_calls"])
    assert "wiki/git-workflow.md" in result["source"]


def test_documentation_agent_uses_list_files(monkeypatch) -> None:
    scripted = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            _tool_call("call-2", "list_files", {"path": "wiki"})
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
                            '{"answer":"The wiki contains many markdown pages.",'
                            '"source":"wiki"}'
                        )
                    }
                }
            ]
        },
    ]

    def fake_chat_completion(messages, tools):  # noqa: ANN001, ANN202
        return scripted.pop(0)

    monkeypatch.setattr(agent, "_chat_completion", fake_chat_completion)
    result = agent.run_agent("What files are in the wiki?")

    assert any(tc["tool"] == "list_files" for tc in result["tool_calls"])
    assert isinstance(result["answer"], str) and result["answer"]
