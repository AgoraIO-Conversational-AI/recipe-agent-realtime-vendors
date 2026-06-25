---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.vendor-selection
    name: Realtime MLLM vendor registry, builders, and runtime selection
  - id: web.conversation-ui
    name: Conversation UI panels, controls, and vendor dropdown
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate and all vendor API keys stay in the Python backend.
  - id: mllm.with-mllm-only
    summary: A single realtime MLLM vendor via .with_mllm() replaces cascading STT/LLM/TTS; never call .with_stt/.with_llm/.with_tts.
  - id: vad.vendor-owned
    summary: turn_detection (server_vad) is set on each vendor builder, not on AgoraAgent(...).
  - id: creds.validated-at-start
    summary: Vendor credentials are validated in Agent.start() via build_vendor(), not in __init__, so /get_config stays key-less.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID, AGORA_APP_CERTIFICATE are always required; the selected vendor's key(s) are required at agent start; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, GET /api/vendors, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
  - id: vendor.registry
    summary: vendors.py holds CATEGORY, one build_<vendor>(env) per vendor, REGISTRY, and build_vendor()/required_env()/needs_key()/available(); this shape is shared across the sibling vendor recipes.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **realtime vendors** quickstart: a data-driven switchboard over every A4.1 realtime MLLM (voice-to-voice), behind a Next.js web client.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers who want to compare or swap realtime MLLM vendors (OpenAI, Gemini, xAI, Vertex AI) with minimal code change, using a Python FastAPI backend and Next.js web client.
- Reuse model: clone, bind project, set `REALTIME_VENDOR` + that vendor's key(s), run, then customize via the vendor registry or browser UI.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- A data-driven vendor registry (`vendors.py`) covering all four A4.1 realtime MLLM vendors, selectable via `REALTIME_VENDOR` env or in-UI dropdown (`GET /vendors`).
- A single realtime MLLM attached via `.with_mllm()` (no cascading vendors, no `llm/` service, no mock, no tunnel).
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status, and vendor dropdown.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `agent.vendor-selection` | `server/src/vendors.py` | Add a `build_<vendor>(env)` function and a `REGISTRY` line. | Run `verify:backend` + `pytest tests`; add env block to `.env.example`. |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call (including vendor dropdown), transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/vendors`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, all vendor keys, and agent lifecycle.
- A single realtime MLLM handles the full voice-to-voice pipeline; `turn_detection` (`server_vad`) is vendor-owned.
- Vendor credentials are validated in `Agent.start()` via `build_vendor()`; the server boots without them.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Vendor env | Per-vendor (see `required_env(name)` in `vendors.py` and `06_interfaces.md`) |
| Optional backend env | `REALTIME_VENDOR`, `REALTIME_MODEL`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `GET /api/vendors` | Returns `data.default`, `data.vendors[{name, needs_key, required_env}]`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, vendor?, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.vendor`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact model names, VAD timing, voice, and greeting text, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user/vendor and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env (including vendor table), and commands.
- `L1/02_architecture.md` — request flow and topology.
- `L1/05_workflows.md` — common modification workflows (add vendor, change model, etc.).
- `L1/06_interfaces.md` — route, rewrite, env, and vendor registry contracts.
- `L1/L2/vendor_registry.md` — full vendor builder details and extension patterns.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration including vendor selection.
