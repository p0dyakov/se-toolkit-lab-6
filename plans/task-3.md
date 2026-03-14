# Task 3 Plan — The System Agent

## Goal

Extend the Task 2 documentation agent with a system-level tool `query_api` so it can answer runtime/data questions from the deployed backend, not only wiki/source questions.

## `query_api` design

- Tool name: `query_api`
- Arguments:
  - `method` (string, required)
  - `path` (string, required, starts with `/`)
  - `body` (string, optional; JSON text for request body)
- Auth:
  - Read `LMS_API_KEY` from environment
  - Send `Authorization: Bearer <LMS_API_KEY>`
- Base URL:
  - Read `AGENT_API_BASE_URL` from environment
  - Default: `http://localhost:42002`
- Return payload (stringified JSON):
  - `{ "status_code": <int>, "body": <json|string> }`

## Prompt and routing strategy

System prompt rules:

- Use `read_file`/`list_files` for docs and source navigation.
- Use `query_api` for live state and endpoint behavior checks.
- For debugging questions, first inspect failing API response, then read source for root cause.

## Safety and reliability

- Keep existing path-sandbox protections for file tools.
- Validate HTTP method and path in `query_api`.
- Bound tool loop by max call count.

## Initial benchmark diagnosis

Attempted local benchmark execution requires missing local secrets (`AUTOCHECKER_*` and local deployment setup), so initial full score is blocked in this environment snapshot.  
Iteration plan:

1. Implement `query_api` + prompt routing.
2. Add regression tests for `read_file` and `query_api` usage.
3. Run `run_eval.py` after local/VM env files are configured.
4. Tune prompt/tool descriptions until 10/10 local pass.
