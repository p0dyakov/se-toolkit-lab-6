# Task 1 Plan — Call an LLM from Code

## Goal

Implement a minimal CLI agent (`agent.py`) that:

- accepts a question as the first CLI argument;
- calls an OpenAI-compatible chat completions API;
- prints valid JSON to stdout with required fields:
  - `answer` (string),
  - `tool_calls` (array, empty for Task 1).

## Provider and model

- Provider: OpenRouter (OpenAI-compatible API).
- Base URL: from `LLM_API_BASE` in environment.
- Model: from `LLM_MODEL` in environment.
- Auth key: from `LLM_API_KEY` in environment.

This keeps the implementation provider-agnostic and compatible with the lab's recommendation to use environment variables.

## Implementation steps

1. Create `agent.py` in project root.
2. Add lightweight env-file loading (`.env.agent.secret` then `.env`) without hardcoding secrets.
3. Parse CLI input and validate question presence.
4. Send request to `/chat/completions` with a minimal system prompt + user question.
5. Parse assistant message content into `answer`.
6. Emit one JSON object to stdout: `{"answer": "...", "tool_calls": []}`.
7. Keep all diagnostics on stderr and return non-zero exit code on failure.

## Testing strategy

Add one regression test that:

- runs `agent.py` as a subprocess;
- injects a deterministic mocked LLM response via environment variable;
- validates stdout is JSON and contains required fields/types.

This avoids flaky network dependency while preserving CLI contract coverage.

## Documentation updates

Create `AGENT.md` with:

- architecture summary for Task 1;
- required environment variables;
- how to run locally;
- expected output contract.
