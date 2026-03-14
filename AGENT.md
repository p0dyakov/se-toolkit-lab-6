# Agent (Tasks 1-2)

## Overview

`agent.py` is a CLI documentation agent. It accepts a user question, interacts with an OpenAI-compatible model, and returns a single JSON object.

Current output contract:

- `answer` (string, required)
- `source` (string, required for documentation answers; may be empty when not found)
- `tool_calls` (array, required; contains executed tool calls)

## LLM configuration

The agent reads all LLM config from environment variables:

- `LLM_API_KEY`
- `LLM_API_BASE`
- `LLM_MODEL`

For local convenience, it loads `.env.agent.secret` and then `.env` without overriding already exported variables.

## Agentic loop

The agent implements a tool-calling loop:

1. Send system + user messages with tool schemas.
2. If model returns tool calls:
   - execute tools,
   - append tool results as `tool` messages,
   - continue.
3. If model returns no tool calls:
   - parse final answer and source,
   - return JSON.
4. Hard stop after 10 tool calls.

## Tools

### `read_file(path)`

Reads file contents from repository root.

### `list_files(path)`

Lists directory entries (newline-separated) from repository root.

## Path security

Both tools enforce a repository-root sandbox:

- paths are resolved relative to project root;
- path traversal outside repo is rejected;
- `read_file` only reads files;
- `list_files` only lists directories.

## Run

```bash
uv run agent.py "How do you resolve a merge conflict?"
```

Example output:

```json
{
  "answer": "Edit the conflicted file, resolve markers, stage, and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Testing

- Task 1 regression test validates subprocess JSON contract.
- Task 2 tests mock LLM responses and validate tool usage (`read_file`, `list_files`) and source extraction.
