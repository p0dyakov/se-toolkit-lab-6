# Agent Architecture (Tasks 1-3)

## What this agent does

`agent.py` is a CLI system agent for Lab 6. It accepts one natural-language question, calls an OpenAI-compatible LLM, executes tool calls, and prints one JSON object to stdout. The output contract is stable:

- `answer` — final text answer.
- `source` — file/section reference when documentation or source code was used (can be empty for pure runtime API answers).
- `tool_calls` — trace of executed tools with arguments and raw result payload.

## Configuration model

All runtime config is environment-driven:

- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` control the LLM backend.
- `LMS_API_KEY` authenticates backend API requests from the `query_api` tool.
- `AGENT_API_BASE_URL` selects API host for `query_api` (default `http://localhost:42002`).

No keys are hardcoded. For local development, `agent.py` loads `.env.agent.secret` and `.env` as convenience inputs, but exported shell variables always win.

## Agent loop

The agent uses a classic tool-calling loop:

1. Build `messages` with system + user prompt and tool schemas.
2. Send to LLM (`/chat/completions`).
3. If `tool_calls` are returned, execute each tool and append `tool` messages.
4. Repeat until the model returns normal content (final answer).
5. Stop after `MAX_TOOL_CALLS` (10) to avoid infinite loops.

This keeps behavior deterministic, debuggable, and safe for benchmark-style questions.

## Tools

### `read_file(path)`

Reads repository files. It enforces a project-root sandbox and blocks traversal outside the repo.

### `list_files(path)`

Lists directory entries under repository root with the same sandbox constraints.

### `query_api(method, path, body?)`

Sends authenticated HTTP requests to the LMS backend and returns a normalized JSON result:

```json
{"status_code": 200, "body": ...}
```

The tool validates HTTP method, requires a leading slash in `path`, and injects `Authorization: Bearer <LMS_API_KEY>`.

## Tool routing strategy in prompt

The system prompt instructs the model to:

- use `read_file` / `list_files` for documentation and source-code questions,
- use `query_api` for runtime/data questions,
- combine `query_api` + `read_file` for bug diagnosis tasks.

This separation is important for benchmark correctness because several questions explicitly require specific tool usage.

## Validation and regression coverage

Regression tests include:

- subprocess JSON contract test (Task 1),
- documentation tool usage tests (Task 2),
- system/data tool usage tests including `query_api` (Task 3).

Current implementation is structured for iterative prompt/tool tuning against `run_eval.py` and the hidden autochecker questions.
