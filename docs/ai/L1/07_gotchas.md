# 07 · Gotchas

> Non-obvious pitfalls specific to the realtime vendors recipe. Read before changing the agent, vendors, env, or verify scripts.

## Vendor credentials are validated at agent start, not boot

The server boots **without** vendor keys (so `doctor`/contract checks and `/get_config` work), but `POST /startAgent` returns **400** if the selected vendor's credentials are missing. `Agent.__init__` raises only for missing `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE`. Don't move vendor credential checks into `__init__`.

## `REALTIME_VENDOR` is read in `__init__`, not validated there

`Agent.__init__` reads `REALTIME_VENDOR` to set `self.vendor` (default `openai`) but does **not** call `build_vendor` yet. Validation (and the missing-creds `ValueError`) happens in `start()` when `build_vendor(selected)` is called.

## In-UI vendor switcher bypasses `REALTIME_VENDOR`

`POST /startAgent` accepts a `vendor` field from the browser. When set, it overrides `REALTIME_VENDOR` for that call. The pre-call dropdown populates from `GET /vendors`. If the selected vendor's keys are not set on the server, `startAgent` returns 400 with a clear message naming the missing vars.

## Turn detection is vendor-owned

`turn_detection={"mode": "server_vad"}` is set **inside each `build_<vendor>()` function** in `vendors.py`. **Do not** set a top-level `turn_detection` on `AgoraAgent(...)` when using `.with_mllm()` — it is ignored and misleading.

## No tools

The realtime MLLM vendors have no tool support in this SDK. Do not wire tool/function-calling here — use a cascading-vendor recipe if you need tools.

## Never call `.with_stt/.with_llm/.with_tts`

This recipe uses `.with_mllm()` only. The entire voice-to-voice pipeline is internal to the realtime MLLM. Calling `.with_stt`, `.with_llm`, or `.with_tts` introduces a cascade and breaks the recipe contract.

## No `llm/` service, no mock, no tunnel

Unlike the cascade recipe family, there is a single cloud MLLM. Do not reintroduce `llm/`, a mock LLM service, or a public tunnel.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid`, `vendor` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## UID normalization in transcripts

`normalizeTranscript` maps `uid === '0'` to the local UID. Token issuance also rejects zero/negative UIDs and generates a concrete one. Preserve both — speaker mapping and tokens depend on concrete UIDs.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — correct vendor wiring patterns.
