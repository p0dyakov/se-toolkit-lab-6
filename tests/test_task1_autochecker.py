import json
import os
import subprocess
import sys
from pathlib import Path


def test_task1_cli_json_output() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    agent_path = repo_root / "agent.py"

    env = os.environ.copy()
    env["LLM_MOCK_RESPONSE"] = "Autochecker compatibility response."

    result = subprocess.run(
        [sys.executable, str(agent_path), "What is REST?"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip())
    assert isinstance(payload, dict)
    assert "answer" in payload
    assert "tool_calls" in payload
    assert isinstance(payload["answer"], str)
    assert isinstance(payload["tool_calls"], list)
