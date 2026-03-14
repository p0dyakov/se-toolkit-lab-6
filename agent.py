#!/usr/bin/env python3
"""Minimal CLI agent for Lab 6 Task 1."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx


def _load_env_files() -> None:
    for env_file in (".env.agent.secret", ".env"):
        path = Path(env_file)
        if not path.exists():
            continue

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _read_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    raise RuntimeError(f"Missing required environment variable: {name}")


def _request_answer(question: str) -> str:
    # Deterministic test hook for subprocess regression tests.
    mocked = os.environ.get("LLM_MOCK_RESPONSE", "").strip()
    if mocked:
        return mocked

    api_key = _read_required_env("LLM_API_KEY")
    base_url = _read_required_env("LLM_API_BASE").rstrip("/")
    model = _read_required_env("LLM_MODEL")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise and accurate assistant."},
            {"role": "user", "content": question},
        ],
        "temperature": 0,
    }

    with httpx.Client(timeout=55.0) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("LLM response has no choices")

    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    raise RuntimeError("LLM response contains empty assistant content")


def main() -> int:
    _load_env_files()

    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        return 1

    question = sys.argv[1].strip()
    if not question:
        print("Question must be a non-empty string", file=sys.stderr)
        return 1

    try:
        answer = _request_answer(question=question)
    except Exception as exc:
        print(f"Agent error: {exc}", file=sys.stderr)
        return 1

    output = {"answer": answer, "tool_calls": []}
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
