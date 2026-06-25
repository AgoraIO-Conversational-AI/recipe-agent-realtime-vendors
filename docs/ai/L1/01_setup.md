# 01 · Setup

> Install dependencies, configure env, and run the realtime vendors recipe locally. This recipe is **BYO-only**: every vendor (including the default `openai`) requires its own API key.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)
- An API key for **your chosen realtime vendor** (see [Vendors table](#vendors))

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default                    | Notes                                                     |
| ----------------------- | :------: | -------------------------- | --------------------------------------------------------- |
| `AGORA_APP_ID`          |    ✅    | —                          | Agora Console → Project → App ID                          |
| `AGORA_APP_CERTIFICATE` |    ✅    | —                          | Agora Console → Project → App Certificate                 |
| `REALTIME_VENDOR`       |          | `openai`                   | Which realtime MLLM vendor to build (see Vendors table)   |
| `REALTIME_MODEL`        |          | per-vendor                 | Optional model override for the selected vendor           |
| `AGENT_GREETING`        |          | built-in line              | Optional opening utterance override                       |

### Vendors

| Vendor | `REALTIME_VENDOR` | Required env | Default model |
| ------ | ----------------- | ------------ | ------------- |
| OpenAI Realtime | `openai` | `OPENAI_API_KEY` | `gpt-4o-realtime-preview` |
| Gemini Live | `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash-live-001` |
| xAI Grok | `xai` | `XAI_API_KEY` | _(SDK default)_ |
| Vertex AI | `vertexai` | `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` | `gemini-2.0-flash-live-001` |

Fill credentials via the Agora CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then add the selected vendor's key(s) to server/.env.local
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## Run

```bash
bun run dev              # backend (:8000) + web (:3000) via concurrently
```

Open <http://localhost:3000> → select a vendor in the dropdown → **Start Conversation** → speak. Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA_APP_ID/CERTIFICATE present
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + fastapi smoke + proxy + web build
bun run clean            # remove venvs and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- None. For what each verify command asserts, see [05_workflows](05_workflows.md) and [06_interfaces](06_interfaces.md).
