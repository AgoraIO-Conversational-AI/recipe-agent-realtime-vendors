# Agent Development Guide

For coding agents working in `recipe-agent-realtime-vendors`. This repository is
the **realtime vendors** recipe in the Agora Conversational AI recipes family:
the realtime MLLM leg is a per-vendor switchboard (one readable `build_<vendor>`
per vendor) selected via `REALTIME_VENDOR`. The MLLM replaces the cascade and is
attached with `.with_mllm()` only.

## How to Load

This repository uses progressive disclosure documentation. Docs live under
`docs/ai/` in three levels.

1. Read [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md) to identify the repo.
2. This repo declares `Recipe Role: base`; read [docs/ai/RECIPE.md](docs/ai/RECIPE.md) before changing reusable recipe contracts.
3. Load ALL 8 files in [docs/ai/L1/](docs/ai/L1/). They are small — load all upfront.
4. Follow L2 deep-dive links only when L1 isn't detailed enough. The index is at [docs/ai/L1/L2/_index.md](docs/ai/L1/L2/_index.md).

The sections below remain the canonical contributor handbook for hands-on work;
the `docs/ai/` tree is the structured summary used by AI agents.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. The realtime MLLM leg is built from the
  per-vendor builder registry in `server/src/vendors.py` and attached via `.with_mllm()`
  — it replaces the STT/LLM/TTS cascade. SDK: `agora-agents>=2.3.0`
  (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` service — single-process, MLLM is **BYO-only** (every vendor,
  including the default `openai`, requires its own API key).

## Pipeline

`<REALTIME_VENDOR>` MLLM via `.with_mllm()` (default `openai`) — voice-to-voice,
no separate STT/LLM/TTS. Turn detection is MLLM-owned (`server_vad`). No tools
(the realtime MLLM vendors are tool-less).

## Vendor registry

- `server/src/vendors.py` holds `CATEGORY = "REALTIME"`, one readable
  `build_<vendor>(env)` function per vendor (all four A4.1 realtime vendors:
  `openai`, `gemini`, `xai`, `vertexai`), a `REGISTRY: {name: (builder,
  [required_env])}`, and `build_vendor()` / `required_env()` / `needs_key()` /
  `available()`.
- `agent.py` reads `REALTIME_VENDOR` in `__init__` (no validation) and calls
  `build_vendor(selected)` for the MLLM leg **in `start()`** — where `selected`
  is the in-UI `vendor` (from `GET /vendors` + the pre-call dropdown) or
  `REALTIME_VENDOR`. BYO credential validation happens there, so `/get_config`
  stays key-less.
- The MLLM is attached with `.with_mllm()` only; never `.with_stt/.with_llm/.with_tts`.
- Each builder sets `turn_detection={"mode": "server_vad"}` (MLLM-owned).

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- The realtime vendor registry lives in `server/src/vendors.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000).
  The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI).
  Set `AGENT_BACKEND_URL` in the web deployment.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `REALTIME_VENDOR` | `openai` | which realtime MLLM vendor to build (see README Vendors table) |
| `REALTIME_MODEL` | per-vendor | optional model override for the selected vendor |
| _vendor creds_ | — | **required** for the selected vendor (BYO-only); `required_env(REALTIME_VENDOR)` |
| `AGENT_GREETING` | built-in | Optional opening line override |

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- The selected vendor's creds are validated in `agent.start()` via `build_vendor`
  — the server boots without them, but `/startAgent` returns 400 until they are set.
- Add or change realtime vendors by editing the relevant `build_<vendor>`
  function + its `REGISTRY` line in `vendors.py`; the framework
  (`build_vendor`/`required_env`/`needs_key`/`available`) is shared across the
  sibling vendor recipes — keep it identical.
- `turn_detection` is MLLM-owned (`server_vad`); do not set a top-level
  `turn_detection` on `AgoraAgent(...)` when using `.with_mllm()`.

## Anti-patterns

- Do not reintroduce `llm/` or the cascading STT/LLM/TTS vendors, and never call
  `.with_stt/.with_llm/.with_tts` — this recipe uses `.with_mllm()` only.
- Do not hardcode a single realtime vendor in `agent.py`; build it via `build_vendor`.
- Do not validate vendor credentials in `__init__` (it would break key-less
  `/get_config` and the managed docker smoke).
- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not add tools — the realtime MLLM vendors have no tool support.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   the relevant module README, and `server/.env.example` together.
5. If the change touches workflows, interfaces, gotchas, or security details,
   update the matching file under [docs/ai/L1/](docs/ai/L1/) and bump
   `Last Reviewed` in [docs/ai/L0_repo_card.md](docs/ai/L0_repo_card.md).

## Git Conventions

### Commit messages — conventional commits

- **Format:** `type: description` or `type(scope): description`
- **Types:** `feat:` (new feature), `fix:` (bug fix), `chore:` (maintenance, version bumps), `test:` (test additions/changes), `docs:` (documentation)
- **Scoped variant:** `feat(scope):`, `fix(scope):` — e.g. `fix(server): validate vendor creds`
- **Lowercase after prefix** — `feat: add feature`, not `feat: Add feature`
- **Present tense** — "add feature", not "added feature"

### Branch names

- **Format:** `type/short-description` — lowercase, hyphen-separated
- **Types match commit types:** `feat/`, `fix/`, `chore/`, `test/`, `docs/`
- **Examples:** `feat/add-vendor`, `fix/missing-creds-error`, `docs/progressive-disclosure`

### General rules

- **Repo-local `AGENTS.md` is the authoritative source for repo conventions.**
- **No AI tool names** — never mention claude, cursor, copilot, cody, aider, gemini, codex, chatgpt, or gpt-3/4 in commit messages or PR descriptions.
- **No Co-Authored-By trailers** — omit AI attribution lines.
- **No `--no-verify`** — let git hooks run normally.
- **No git config changes** — do not modify `user.name` or `user.email`.

## Doc Commands

| Command       | When to use                                                                  |
| ------------- | ---------------------------------------------------------------------------- |
| generate docs | No `docs/ai/` directory exists yet                                           |
| update docs   | Code changed since the `Last Reviewed` date in L0                            |
| test docs     | Verify docs give agents the right context (writes `docs/ai/test-results.md`) |
| fix docs      | Close findings from a docs review or test run                                |

See the [progressive disclosure standard](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/standard/progressive-disclosure-standard.md) and [workflows](https://github.com/AgoraIO-Community/ai-devkit/blob/main/docs/workflows/progressive-disclosure-docs.md) for the full specification.
