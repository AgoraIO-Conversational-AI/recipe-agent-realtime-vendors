# Progressive Disclosure — Test Results

> Test run for `recipe-agent-realtime-vendors` progressive disclosure docs.
> Date: 2026-06-25 · Standard: AgoraIO-Community/ai-devkit progressive-disclosure.

## Step 1 — Structural checks

| Check                                              | Result |
| -------------------------------------------------- | ------ |
| `L0_repo_card.md` ≤ 50 lines                       | Pass (36) |
| All 8 L1 files present                             | Pass |
| Each L1 has purpose blockquote + Related Deep Dives| Pass |
| L1 line counts in 80–200 target                    | **Below target** (37–92) — see note |
| L2 `_index.md` present                             | Pass |
| Each L2 opens with "When to Read This" callout     | Pass (2/2) |
| Relative links resolve (`docs/ai/` + AGENTS.md)    | Pass (42 checked, 0 broken .md file links; 2 directory refs match exemplar pattern) |
| AGENTS.md has How to Load / Git Conventions / Doc Commands | Pass |

**Note on L1 line counts:** files are table-dense and information-complete but
run 37–92 lines, under the 80–200 soft target. The standard favors tables over
prose and warns against bloat, so they were left concise rather than padded.
Accepted deviation; revisit if a section needs more depth.

## Step 2 — pytest run (throwaway venv `/tmp/v_rt_vendors`)

```
python3 -m venv /tmp/v_rt_vendors
pip install -r server/requirements.txt -r server/requirements-dev.txt
pytest server/tests -v
```

Result: **4 passed** (sandboxed; no cloud, no real creds).

| Test | Status |
| ---- | ------ |
| `test_agent_config.py::test_agent_constructs` | Pass |
| `test_agent_construction.py::test_start_constructs_real_agent_and_returns_shape` | Pass |
| `test_vendors.py::test_every_vendor_constructs_and_emits_config` | Pass |
| `test_vendors.py::test_byo_vendor_missing_creds_raises` | Pass |

Venv removed after run (`rm -rf /tmp/v_rt_vendors`).

## Step 3 — Question runs

Questions span the five standard categories. Each answer was checked against the
repo source before being marked Pass. "Level" is the lowest disclosure level
that fully answers the question.

### Setup & Build

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 1 | How do I install and run it locally? | `bun run setup` then `bun run dev` (backend :8000 + web :3000). | `L1/01_setup.md` ↔ `package.json` scripts | L1 | Pass |
| 2 | Which env vars are always required? | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, plus the selected vendor's key(s). | `L1/01_setup.md`, `06_interfaces.md` ↔ `agent.py`, `.env.example` | L1 | Pass |
| 3 | Is this zero-key? | No — BYO-only; every vendor including the default `openai` requires its own API key. | `L1/01_setup.md`, `07_gotchas.md` ↔ `README.md`, `agent.py` | L1 | Pass |

### Test & Run

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 4 | How do I run backend tests without cloud creds? | `cd server && pytest tests -v`; `conftest.py` fakes env + SDK session. | `L1/04_conventions.md`, `01_setup.md` ↔ `tests/conftest.py` | L1 | Pass (ran: 4 passed) |
| 5 | What's the narrowest gate for a web-only change? | `bun run verify:web`. | `L1/05_workflows.md` ↔ `package.json` | L1 | Pass |
| 6 | What does `verify:local:fastapi` do? | Spawns real FastAPI with `FakeAgent` and proxies routes through the rewrite map. | `L1/03_code_map.md`, `05_workflows.md` ↔ `web/scripts/verify-local-fastapi.ts` | L1 | Pass |

### Conventions

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 7 | What response shape do backend routes use? | `{ code, msg, data }`; `data` only when there's a payload. | `L1/04_conventions.md`, `06_interfaces.md` ↔ `server.py` | L1 | Pass |
| 8 | How are errors mapped to HTTP codes? | `ValueError→400`, `RuntimeError→500`, else 500 via `_to_http_error`. | `L1/04_conventions.md` ↔ `server.py` | L1 | Pass |
| 9 | What are the commit/branch conventions? | Conventional commits `type: description`; branches `type/short-description`; no AI tool names. | `AGENTS.md` Git Conventions | L1 | Pass |

### Development

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 10 | How do I switch the realtime MLLM vendor? | Set `REALTIME_VENDOR` env or use the in-UI dropdown (sends `vendor` in `POST /startAgent`). | `L1/05_workflows.md`, `06_interfaces.md` ↔ `server.py`, `agent.py` | L1 | Pass |
| 11 | Where is the `/api/*` boundary defined and what must I not add? | Rewrites in `web/next.config.ts` (now includes `/api/vendors`); never add `app/api/**/route.ts` for agent/token logic. | `L1/04_conventions.md`, `07_gotchas.md` ↔ `next.config.ts`, `verify-api-contracts.ts` | L1 | Pass |
| 12 | Where does token generation live? | `server/` (`generate_convo_ai_token` in `server.py`); App Certificate stays server-side. | `L1/02_architecture.md`, `08_security.md` ↔ `server.py` | L1 | Pass |

### Deep Dive

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 13 | How is turn detection configured and where? | `TURN_DETECTION = {"mode": "server_vad"}` is set inside each `build_<vendor>()` function in `vendors.py`; never on `AgoraAgent(...)`. | `L2/vendor_registry.md` ↔ `vendors.py`, `agent.py` | L2 | Pass |
| 14 | How do I add a new realtime MLLM vendor? | Add `build_<vendor>(env)` function + `REGISTRY` line in `vendors.py`; add env block to `.env.example`; run pytest. | `L2/vendor_registry.md`, `05_workflows.md` ↔ `vendors.py`, `test_vendors.py` | L2 | Pass |
| 15 | How does stop survive a backend restart? | `_sessions` is in-memory; missing session falls back to `client.stop_agent(agent_id)`. | `L2/session_lifecycle.md` ↔ `agent.py` | L2 | Pass |

## Step 4 — Analysis

- All 15 questions answered at the expected disclosure level (12 at L1, 3 at L2).
  No "correct but needed L2 unnecessarily" or "wrong/missing L2" cases.
- No missing-coverage findings; no broken .md file references.
- One soft deviation: L1 line counts below the 80–200 target (accepted; concise/table-dense).

## Step 5 — Summary

| Category       | Questions | Pass | Notes |
| -------------- | :-------: | :--: | ----- |
| Setup & Build  | 3 | 3 | — |
| Test & Run     | 3 | 3 | backend tests executed: 4 passed |
| Conventions    | 3 | 3 | — |
| Development    | 3 | 3 | — |
| Deep Dive      | 3 | 3 | resolved at L2 as designed |
| **Total**      | **15** | **15** | — |

## Step 6 — Fixes / Retest

No failing questions; no fixes required. Evidence executed during this run:

- `pytest tests -v` (throwaway venv `/tmp/v_rt_vendors`) → `4 passed`.
- Relative link check → `42 checked, 0 broken .md file links`.
