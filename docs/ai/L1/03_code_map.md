# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                        |
| --------------------- | --------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts. |
| `README.md`           | Setup, run modes, vendor table, env, troubleshooting.                 |
| `ARCHITECTURE.md`     | System shape and component boundaries.                                |
| `AGENTS.md`           | Coding-agent handbook + How to Load / Git Conventions / Doc Commands. |
| `Dockerfile`          | Backend-only image (`:8000`).                                         |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`. |

## `server/` — FastAPI backend (:8000)

| Path                              | Responsibility                                                              |
| --------------------------------- | --------------------------------------------------------------------------- |
| `src/server.py`                   | FastAPI app, CORS, route handlers (`/get_config`, `/vendors`, `/startAgent`, `/stopAgent`), error mapping, uvicorn entrypoint. |
| `src/agent.py`                    | `Agent` class: `AsyncAgora` client, `start()`/`stop()`, `_sessions`.        |
| `src/vendors.py`                  | `CATEGORY`, one `build_<vendor>()` per vendor, `REGISTRY`, `build_vendor()` / `required_env()` / `needs_key()` / `available()`. |
| `scripts/run_fake_server.py`      | Boots `server.app` with a `FakeAgent` for the local FastAPI smoke test.     |
| `tests/test_vendors.py`           | Builds every registered vendor with dummy creds; asserts config shape + missing-creds error. |
| `tests/test_agent_construction.py`| Builds the real `AgoraAgent`, fakes the SDK session, asserts shape.         |
| `tests/test_agent_config.py`      | Smoke: `Agent()` constructs without creds; default vendor is `openai`.      |
| `tests/conftest.py`               | `fake_env` fixture + `FakeAgent`; no cloud, no real creds.                  |
| `.env.example`                    | Env template (do not add `PORT`).                                           |
| `requirements*.txt`               | Runtime + dev (pytest) deps.                                                |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config (key-less; no vendor creds needed).
- `GET /vendors` — list selectable realtime MLLM vendors for the in-UI dropdown.
- `POST /startAgent` — start the realtime agent session (validates vendor creds here).
- `POST /stopAgent` — stop by `agent_id`.

## `web/` — Next.js client (:3000)

| Path                                      | Responsibility                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------- |
| `next.config.ts`                          | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root. |
| `src/services/api.ts`                     | Browser API client: `getConfig`, `getVendors`, `startAgent`, `stopAgent`. |
| `src/lib/conversation.ts`                 | Transcript normalization, timestamp/UID mapping, visualizer state.     |
| `src/lib/agora.ts`                        | Agora RTC/RTM helpers.                                                 |
| `src/components/LandingPage.tsx`          | Conversation entry: vendor fetch, config fetch, agent start, RTM login, teardown. |
| `src/components/ConversationComponent.tsx`| RTC join, mic publish, transcript/metrics/state listeners.             |
| `src/components/Quickstart*.tsx`          | Pre-call (including vendor dropdown), transcript, metrics, layout panels. |
| `scripts/verify-api-contracts.ts`         | Asserts rewrites + client paths + response envelope (no network).      |
| `scripts/verify-local-proxy.ts`           | Stub backend; proxies `/api/*` through the rewrite map.                |
| `scripts/verify-local-fastapi.ts`         | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.       |
| `scripts/doctor.ts`                       | Web prerequisite check.                                                |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
