# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens and the agent session, building the selected realtime MLLM from a data-driven vendor registry.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds selected MLLM via build_vendor(REALTIME_VENDOR)
                                 │  attached via .with_mllm() (replaces the cascade)
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → <REALTIME_VENDOR> (voice-to-voice, server_vad)
                                 │  agent speech → user's channel
                                 ▼
                              User hears realtime voice; RTM transcript + metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service, no mock vendor, no public tunnel — the MLLM is a single cloud-hosted vendor, selectable at runtime.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs. This step works key-less even though the recipe is BYO-only.
2. Browser joins the RTC channel, then `POST /api/startAgent` (with optional `vendor` field); backend calls `build_vendor(selected)` to construct the MLLM — which validates vendor credentials — and starts an async agent session.
3. Agora routes user audio to the selected realtime vendor; the model streams voice-to-voice back into the channel.
4. RTM delivers transcript + metrics to the web UI.
5. `POST /api/stopAgent { agentId }` ends the session.

## Why no `llm/` service

The realtime vendors recipe attaches a single realtime MLLM via `agora_agent` `.with_mllm()`. STT, reasoning, and TTS are all internal to the realtime model — no cascading STT→LLM→TTS vendors, no `.with_stt/.with_llm/.with_tts`. Trade-off: the recipe is **BYO-only**; every vendor (including the default `openai`) requires its own API key, validated at agent start.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`. Reads `REALTIME_VENDOR` at `__init__`; calls `build_vendor(selected)` in `start()`.
- **`vendors.py`** (`server/src/vendors.py`) — the data-driven switchboard. Holds `CATEGORY = "REALTIME"`, one readable `build_<vendor>()` function per vendor (openai, gemini, xai, vertexai), `REGISTRY`, and `build_vendor()` / `required_env()` / `needs_key()` / `available()`.
- **`GET /vendors`** (`server/src/server.py`) — serves the vendor list to the in-UI dropdown.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **MLLM-owned turn detection** — `server_vad` is set on each vendor builder in `vendors.py`; no top-level `turn_detection` on `AgoraAgent(...)`.
- **Creds validated at `start()`** — server boots without vendor keys; `/startAgent` returns 400 if the selected vendor's credentials are missing.
- **In-UI vendor switcher** — `POST /startAgent` accepts an optional `vendor` field; the browser fetches `GET /vendors` to populate the pre-call dropdown. No backend restart needed to switch vendors.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — vendor switchboard internals, builder contracts, and how to add a vendor.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
