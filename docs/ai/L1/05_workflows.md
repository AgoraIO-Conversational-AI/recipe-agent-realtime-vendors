# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Add a realtime MLLM vendor

1. Add a `build_<vendor>(env)` function in `server/src/vendors.py` that constructs the vendor class with `turn_detection=TURN_DETECTION` and reads its required env vars from `env`.
2. Add the `REGISTRY` line: `"<name>": (build_<vendor>, ["REQUIRED_VAR", ...])`.
3. Add the vendor key block to `server/.env.example`.
4. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Change the agent prompt / greeting / model

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `server/src/agent.py`.
2. Model: set `REALTIME_MODEL` (env) to override the selected vendor's default.
3. Other MLLM options (VAD mode, additional fields): edit the relevant `build_<vendor>()` in `server/src/vendors.py`. See [vendor_registry](L2/vendor_registry.md).
4. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Switch the active vendor at runtime

- **In-UI:** the pre-call screen fetches `GET /api/vendors` and shows a dropdown; the selected vendor is sent as `vendor` in `POST /api/startAgent`. No backend restart needed.
- **By env:** set `REALTIME_VENDOR` in `server/.env.local` and restart; it becomes the dropdown default.

## Adjust session parameters (codec, scenario)

1. Edit the `parameters` dict in `Agent.start()` (`audio_scenario`, `data_channel`, `enable_metrics`, etc.). `output_audio_codec` is also accepted per-request via `parameters` on `POST /startAgent`.
2. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                 |
| ---------------------------- | ------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                |
| Backend logic / vendor config| `bun run verify:backend` + `cd server && pytest tests -v`           |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`    |
| Anything end-to-end (local)  | `bun run verify:local`                                              |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-realtime-vendors` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — vendor switchboard internals and how to add a vendor.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown.
