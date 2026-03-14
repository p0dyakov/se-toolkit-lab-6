# Optional Task Plan — Advanced Agent Features

## Selected extensions

1. Retry logic with exponential backoff for LLM calls.
2. In-memory per-run cache for tool results.

## Why these two

- Retry/backoff improves reliability under transient provider failures (`429`, `5xx`, short network issues).
- Tool caching reduces repeated file/API calls in the same agent run and lowers latency/token churn in loops.

## Expected improvement

- Fewer failed runs caused by temporary LLM API instability.
- Faster responses on questions where the model repeats the same tool call.
- Cleaner traces by marking cache hits in `tool_calls`.

## Implementation steps

1. Update `_chat_completion` with bounded retries and exponential delays.
2. Add a cache dictionary in `run_agent`.
3. Extend `_execute_tool` to return `(result, cache_hit)` and use memoization by `(tool_name, args)`.
4. Add tests:
   - retry recovers from first `429`;
   - duplicate tool calls hit cache and execute once.
5. Update `AGENT.md` with optional architecture notes.
