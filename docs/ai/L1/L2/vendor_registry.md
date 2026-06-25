# Deep Dive — Vendor Registry

> **When to Read This:** You are adding a new realtime MLLM vendor, changing an existing vendor's constructor or required env, debugging missing-credential errors, or reading how the in-UI switcher resolves to a vendor build. For the high-level picture, start at [02_architecture](../02_architecture.md).

The vendor registry (`server/src/vendors.py`) is the central switchboard. It holds every A4.1 realtime MLLM vendor as a self-contained, copy-pasteable builder function, a `REGISTRY` dict, and a small public API used by `agent.py` and `server.py`.

## Design principles

- **Sample code** — each `build_<vendor>(env)` function is intentionally readable and copy-pasteable. It shows the real SDK constructor, the `server_vad` turn detection, and exactly which env vars it reads.
- **Data-driven** — `REGISTRY` is the single source of truth for name→builder and name→required_env. Adding or removing a vendor means editing one `build_<vendor>` function and one `REGISTRY` line.
- **No validation in `__init__`** — `Agent.__init__` reads `REALTIME_VENDOR` but does not call `build_vendor`. Credential validation happens in `Agent.start()` so the server boots without keys.

## Module-level constants

```python
CATEGORY = "REALTIME"
TURN_DETECTION = {"mode": "server_vad"}  # owned by the MLLM vendor
```

`CATEGORY` is a metadata tag for the recipe family. `TURN_DETECTION` is shared by all vendor builders — each builder passes it as the `turn_detection` kwarg.

## Vendor builders

Each `build_<vendor>(env)` takes an `env` dict (defaults to `os.environ`) and returns an MLLM vendor instance. The optional `REALTIME_MODEL` override is handled by the internal `_model(env, default)` helper.

### OpenAI Realtime

```python
OpenAIRealtime(
    api_key=env["OPENAI_API_KEY"],
    model=_model(env, "gpt-4o-realtime-preview"),
    turn_detection=TURN_DETECTION,
)
```

Required env: `OPENAI_API_KEY`.

### Gemini Live

```python
GeminiLive(
    api_key=env["GEMINI_API_KEY"],
    model=_model(env, "gemini-2.0-flash-live-001"),
    turn_detection=TURN_DETECTION,
)
```

Required env: `GEMINI_API_KEY`.

### xAI Grok

```python
XaiGrok(
    api_key=env["XAI_API_KEY"],
    turn_detection=TURN_DETECTION,
)
```

Required env: `XAI_API_KEY`. No `model` kwarg — uses the SDK default.

### Vertex AI

```python
VertexAI(
    adc_credentials_string=env["GOOGLE_APPLICATION_CREDENTIALS_JSON"],
    project_id=env["GOOGLE_PROJECT_ID"],
    location=env["GOOGLE_LOCATION"],
    model=_model(env, "gemini-2.0-flash-live-001"),
    turn_detection=TURN_DETECTION,
)
```

Required env: `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION`.

## REGISTRY

```python
REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "openai":   (build_openai,   ["OPENAI_API_KEY"]),
    "gemini":   (build_gemini,   ["GEMINI_API_KEY"]),
    "xai":      (build_xai,      ["XAI_API_KEY"]),
    "vertexai": (build_vertexai, ["GOOGLE_APPLICATION_CREDENTIALS_JSON",
                                  "GOOGLE_PROJECT_ID", "GOOGLE_LOCATION"]),
}
```

## Public API

| Function | Signature | Returns |
| -------- | --------- | ------- |
| `available()` | `() → List[str]` | Sorted vendor names (keys of REGISTRY) |
| `required_env(name)` | `(str) → List[str]` | Required env var names for a vendor |
| `needs_key(name)` | `(str) → bool` | True for all current vendors (BYO-only) |
| `build_vendor(name, env?)` | `(str, dict?) → vendor` | Raises `ValueError` listing missing env vars |

`build_vendor` raises with the message pattern: `"REALTIME vendor '<name>' requires environment variable(s): VAR1, VAR2"`. This exact text is tested in `test_vendors.py`.

## How it is wired into the agent

In `Agent.start()` (`agent.py`):

```python
selected = (vendor or self.vendor).strip()   # vendor from request or REALTIME_VENDOR
mllm = build_vendor(selected)                # raises ValueError if creds missing

agora_agent = AgoraAgent(
    client=self.client,
    greeting=self.greeting,
    ...
).with_mllm(mllm)

session = agora_agent.create_async_session(
    channel=channel_name,
    agent_uid=str(agent_uid),
    remote_uids=[str(user_uid)],
    ...
)
agent_id = await session.start()
```

`agent.py` returns `vendor` (the resolved name) in the `startAgent` response data, so the caller knows which vendor was actually used.

## How to add a vendor

1. Import the new vendor class at the top of `vendors.py`.
2. Write a `build_<name>(env)` function following the existing pattern (use `TURN_DETECTION`, read all required env vars directly from `env[...]`).
3. Add one line to `REGISTRY`: `"<name>": (build_<name>, ["REQUIRED_VAR", ...])`.
4. Add the env var block to `server/.env.example`.
5. Run `cd server && pytest tests -v` — `test_vendors.py::test_every_vendor_constructs_and_emits_config` will cover the new vendor automatically.

## Test coverage

`tests/test_vendors.py` exercises:
- `test_every_vendor_constructs_and_emits_config` — builds every registered vendor with dummy creds and asserts `to_config()` returns a non-empty dict with the correct `vendor` key.
- `test_byo_vendor_missing_creds_raises` — asserts `ValueError` with the missing var name when creds are absent.

## Related L1

- [02_architecture](../02_architecture.md) · [05_workflows](../05_workflows.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
