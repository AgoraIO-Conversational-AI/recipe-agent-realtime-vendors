# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the vendor registry API.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.
- Works **key-less** — no vendor credentials needed.

### `GET /vendors`

- No parameters.
- Returns `data`: `{ default: string, vendors: [{ name, needs_key, required_env }] }`.
- Used by the pre-call dropdown to populate the in-UI vendor switcher.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, vendor?: string, parameters?: object }`.
  - `vendor` selects the realtime MLLM; defaults to `REALTIME_VENDOR` (default `openai`).
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, vendor, status: "started" }`.
- 400 if vendor credentials are missing, or `channelName`/`rtcUid`/`userUid` invalid.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/vendors`      | `/vendors`          |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `getVendors() → { default: string; vendors: VendorOption[] }`
- `startAgent(channelName, rtcUid, userUid, vendor?) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope          | Required | Default                   |
| ----------------------- | -------------- | :------: | ------------------------- |
| `AGORA_APP_ID`          | backend        |    ✅    | —                         |
| `AGORA_APP_CERTIFICATE` | backend        |    ✅    | —                         |
| `REALTIME_VENDOR`       | backend        |          | `openai`                  |
| `REALTIME_MODEL`        | backend        |          | per-vendor default        |
| `OPENAI_API_KEY`        | backend (openai)|         | — (required when vendor=openai) |
| `GEMINI_API_KEY`        | backend (gemini)|         | — (required when vendor=gemini) |
| `XAI_API_KEY`           | backend (xai)  |          | — (required when vendor=xai) |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | backend (vertexai) | | — (required when vendor=vertexai) |
| `GOOGLE_PROJECT_ID`     | backend (vertexai) |      | — (required when vendor=vertexai) |
| `GOOGLE_LOCATION`       | backend (vertexai) |      | — (required when vendor=vertexai) |
| `AGENT_GREETING`        | backend        |          | built-in line             |
| `AGENT_BACKEND_URL`     | web (deploy)   |   ✅\*   | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |      | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## Vendor registry API (`vendors.py`)

| Function | Returns | Notes |
| -------- | ------- | ----- |
| `available()` | `List[str]` | Sorted list of registered vendor names |
| `required_env(name)` | `List[str]` | Required env var names for a vendor |
| `needs_key(name)` | `bool` | True for all current vendors (BYO-only) |
| `build_vendor(name, env?)` | vendor instance | Raises `ValueError` listing missing env vars |

## Related Deep Dives

- [vendor_registry](L2/vendor_registry.md) — every vendor builder, the REGISTRY, and extension patterns.
