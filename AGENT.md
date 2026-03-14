# Agent (Task 1)

## Overview

`agent.py` is a minimal CLI agent that accepts one question from command-line arguments, sends it to an OpenAI-compatible chat completions API, and prints a single JSON object to stdout.

Task 1 contract:

- output includes `answer` and `tool_calls`;
- `tool_calls` is always an empty array for this stage;
- no secrets are hardcoded in source code.

## Configuration

The agent reads environment variables:

- `LLM_API_KEY` — API key for the LLM provider.
- `LLM_API_BASE` — base URL for OpenAI-compatible API (for example, OpenRouter).
- `LLM_MODEL` — model identifier.

For local convenience, `agent.py` loads `.env.agent.secret` first, then `.env`. Existing shell env vars are not overwritten.

## Run

```bash
uv run agent.py "What does REST stand for?"
```

Example output:

```json
{"answer":"Representational State Transfer.","tool_calls":[]}
```

## Error handling

- Usage and runtime errors are written to stderr.
- On error, process exits with non-zero code.
- On success, exits with code 0.

## Testing

A regression test runs `agent.py` via subprocess and verifies the JSON contract (`answer` + `tool_calls`).  
The test uses `LLM_MOCK_RESPONSE` env variable so it is deterministic and does not require network access.
