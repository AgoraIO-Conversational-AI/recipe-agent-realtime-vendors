# 08 · Security

> Trust boundaries, secret handling, and auth for the realtime vendors recipe.

## Trust boundaries

| Hop                          | Auth                                                                    |
| ---------------------------- | ----------------------------------------------------------------------- |
| Browser → agent backend      | None in local dev (the `/api/*` rewrite is same-origin).                |
| Agent backend → Agora cloud  | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.      |
| Agora cloud → realtime vendor| Selected vendor's key(s) (BYO), passed when the agent session starts.   |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` and all vendor API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, Vertex AI credentials) live only in `server/.env.local` and never reach the browser. The browser receives a short-lived Agora token, never the certificate or vendor keys.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- `build_vendor(name)` raises `ValueError` listing every missing env var for the selected vendor — validated at start, not at boot, so `/get_config` stays key-less.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is **backend-only** (`:8000`); it does not bundle secrets.
- The `vendor` field on `POST /startAgent` comes from the browser (in-UI switcher). The backend validates vendor credentials server-side — the browser cannot bypass key checks.

## Related Deep Dives

- None.
