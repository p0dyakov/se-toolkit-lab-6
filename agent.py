#!/usr/bin/env python3
"""CLI documentation agent for Lab 6 Tasks 1-2."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent
MAX_TOOL_CALLS = 10


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


def _llm_config() -> tuple[str, str, str]:
    api_key = _read_required_env("LLM_API_KEY")
    base_url = _read_required_env("LLM_API_BASE").rstrip("/")
    model = _read_required_env("LLM_MODEL")
    return api_key, base_url, model


def _chat_completion(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    api_key, base_url, model = _llm_config()

    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
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
    return data


def _extract_message(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("LLM response has no choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError("LLM response has invalid message payload")
    return message


def _resolve_safe_path(raw_path: str) -> Path:
    normalized = (raw_path or ".").strip().replace("\\", "/")
    target = (PROJECT_ROOT / normalized).resolve()
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError("Path traversal is not allowed") from exc
    return target


def _read_file(path: str) -> str:
    try:
        target = _resolve_safe_path(path)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not target.exists():
        return f"ERROR: File not found: {path}"
    if not target.is_file():
        return f"ERROR: Not a file: {path}"
    return target.read_text(encoding="utf-8", errors="replace")


def _list_files(path: str) -> str:
    try:
        target = _resolve_safe_path(path)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not target.exists():
        return f"ERROR: Directory not found: {path}"
    if not target.is_dir():
        return f"ERROR: Not a directory: {path}"
    entries = sorted(target.iterdir(), key=lambda p: p.name)
    return "\n".join(p.name for p in entries)


def _tools_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file inside the project repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path from the project root.",
                        }
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and folders in a repository directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative directory path from the project root.",
                        }
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_api",
                "description": "Call the deployed LMS backend API endpoint.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "description": "HTTP method, e.g. GET or POST.",
                        },
                        "path": {
                            "type": "string",
                            "description": "API path starting with /, e.g. /items/.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Optional JSON string request body.",
                        },
                    },
                    "required": ["method", "path"],
                },
            },
        },
    ]


def _query_api(method: str, path: str, body: str | None = None) -> str:
    normalized_method = method.strip().upper()
    if normalized_method not in {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    }:
        return json.dumps({"status_code": 400, "body": f"Unsupported method: {method}"})

    normalized_path = path.strip()
    if not normalized_path.startswith("/"):
        return json.dumps({"status_code": 400, "body": "Path must start with /"})

    api_base = os.environ.get("AGENT_API_BASE_URL", "http://localhost:42002").rstrip("/")
    lms_key = os.environ.get("LMS_API_KEY", "").strip()
    if not lms_key:
        return json.dumps({"status_code": 401, "body": "Missing LMS_API_KEY"})

    headers = {
        "Authorization": f"Bearer {lms_key}",
        "Accept": "application/json",
    }
    request_kwargs: dict[str, Any] = {}
    if body:
        try:
            request_kwargs["json"] = json.loads(body)
        except json.JSONDecodeError:
            request_kwargs["content"] = body
            headers["Content-Type"] = "application/json"

    url = f"{api_base}{normalized_path}"
    with httpx.Client(timeout=30.0) as client:
        response = client.request(normalized_method, url, headers=headers, **request_kwargs)
    try:
        parsed_body: Any = response.json()
    except json.JSONDecodeError:
        parsed_body = response.text
    return json.dumps({"status_code": response.status_code, "body": parsed_body})


def _execute_tool(name: str, args: dict[str, Any]) -> str:
    if name == "read_file":
        return _read_file(str(args.get("path", "")))
    if name == "list_files":
        return _list_files(str(args.get("path", ".")))
    if name == "query_api":
        return _query_api(
            method=str(args.get("method", "GET")),
            path=str(args.get("path", "")),
            body=str(args["body"]) if "body" in args and args["body"] is not None else None,
        )
    return f"ERROR: Unknown tool: {name}"


def _parse_final_response(content: str) -> tuple[str, str]:
    stripped = (content or "").strip()
    if not stripped:
        return "", ""
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            answer = str(parsed.get("answer", "")).strip()
            source = str(parsed.get("source", "")).strip()
            if answer:
                return answer, source
    except json.JSONDecodeError:
        pass
    return stripped, ""


def run_agent(question: str) -> dict[str, Any]:
    # Deterministic test hook for subprocess regression tests.
    mocked = os.environ.get("LLM_MOCK_RESPONSE", "").strip()
    if mocked:
        return {"answer": mocked, "source": "", "tool_calls": []}

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a system agent for this repository and LMS backend. "
                "Use list_files/read_file for wiki/source questions. "
                "Use query_api for live backend/data/runtime questions. "
                "For bug diagnosis, first query the API, then inspect source code. "
                "Answer using repository facts only. "
                "For the final response, return JSON with keys: answer, source. "
                "Source must be a file path and optional anchor."
            ),
        },
        {"role": "user", "content": question},
    ]
    tools = _tools_schema()
    tool_calls_log: list[dict[str, Any]] = []
    tool_calls_count = 0

    while True:
        data = _chat_completion(messages=messages, tools=tools)
        message = _extract_message(data)
        assistant_text = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            answer, source = _parse_final_response(str(assistant_text))
            return {"answer": answer, "source": source, "tool_calls": tool_calls_log}

        messages.append(
            {
                "role": "assistant",
                "content": assistant_text,
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:
            if tool_calls_count >= MAX_TOOL_CALLS:
                return {
                    "answer": "Tool call limit reached before final answer.",
                    "source": "",
                    "tool_calls": tool_calls_log,
                }

            function = tool_call.get("function", {})
            tool_name = str(function.get("name", ""))
            raw_args = function.get("arguments", "{}")
            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                parsed_args = {}
            if not isinstance(parsed_args, dict):
                parsed_args = {}

            result = _execute_tool(tool_name, parsed_args)
            tool_calls_log.append(
                {"tool": tool_name, "args": parsed_args, "result": result}
            )
            tool_calls_count += 1
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": result,
                }
            )


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
        response = run_agent(question=question)
    except Exception as exc:
        print(f"Agent error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
