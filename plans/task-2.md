# Task 2 Plan — The Documentation Agent

## Goal

Upgrade `agent.py` from simple Q/A to a tool-using documentation agent that can:

- discover files via `list_files(path)`,
- read content via `read_file(path)`,
- run an agentic loop with OpenAI-compatible tool calling,
- return structured JSON with:
  - `answer` (required),
  - `source` (required),
  - `tool_calls` (required and populated when tools are used).

## Agent loop design

1. Build messages with system + user prompt.
2. Send to LLM with tool schemas.
3. If LLM returns `tool_calls`:
   - execute each tool,
   - append tool results to messages,
   - repeat.
4. If LLM returns final text:
   - parse answer and source from final response,
   - return JSON output.
5. Stop after max 10 tool calls.

## Tool schemas

- `read_file(path: string)`:
  - reads a file from repo root;
  - returns content or error string.
- `list_files(path: string)`:
  - lists directory entries from repo root;
  - returns newline-separated entries or error string.

## Security constraints

- Resolve paths relative to project root.
- Reject path traversal (`../`) and any resolved path outside project root.
- Never read or list outside repository.

## Testing strategy

Add 2 regression tests with mocked LLM tool-call responses:

1. Merge conflict question:
   - expects `read_file` in `tool_calls`,
   - expects source path containing `wiki/git-workflow.md`.
2. Wiki listing question:
   - expects `list_files` in `tool_calls`.

Use deterministic mocked LLM responses to avoid flaky external dependency.

## Documentation updates

Update `AGENT.md`:

- describe tool schemas and path sandboxing,
- explain agentic loop and stop conditions,
- explain JSON output contract for Task 2.
