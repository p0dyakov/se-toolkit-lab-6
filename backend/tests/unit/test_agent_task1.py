import json
import os
import subprocess
import sys
from pathlib import Path


def test_agent_task1_json_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    agent_path = repo_root / "agent.py"

    env = os.environ.copy()
    env["LLM_MOCK_RESPONSE"] = "Mocked answer for contract test."

    proc = subprocess.run(
        [sys.executable, str(agent_path), "What is REST?"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert isinstance(payload, dict)
    assert "answer" in payload
    assert "tool_calls" in payload
    assert isinstance(payload["answer"], str)
    assert isinstance(payload["tool_calls"], list)
    assert payload["tool_calls"] == []
