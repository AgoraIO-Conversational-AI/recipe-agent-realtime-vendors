# recipe-agent-realtime-vendors — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI voice agent driven by a data-driven realtime MLLM switchboard. The MLLM vendor is selected at runtime via `REALTIME_VENDOR` or the in-UI dropdown; all four A4.1 realtime vendors are supported (openai, gemini, xai, vertexai).

## Identity

| Field          | Value                                                                      |
| -------------- | -------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-realtime-vendors`                  |
| Type           | `distributed-system` (single repo, two co-located processes)               |
| Language       | Python 3.10+ (FastAPI + uvicorn) backend + Next.js 16 / React 19 web       |
| Deploy Target  | `web/` as Next.js app, `server/` as a reachable FastAPI service            |
| Owner          | Agora Conversational AI DevEx                                              |
| Last Reviewed  | 2026-06-25                                                                 |
| Recipe Role    | `base`                                                                     |
| Recipe Version | `1.0.0`                                                                    |
| Recipe Status  | `experimental`                                                             |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                          | Audience       |
| ---------------------------------------- | -------------------------------------------------------------------------------- | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (REALTIME_VENDOR + per-vendor creds), commands  | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Two-process topology, vendor switchboard, `/api/*` rewrite proxy, MLLM lifecycle | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                        | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, Biome, JSON envelope, vendor-owned VAD           | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Add a route, add/change a vendor, change MLLM config, verify, deploy             | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, vendor registry API                 | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | BYO-only credential timing, in-UI switcher, no tools, `PORT` in env              | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate + vendor keys server-only, CORS, codec                 | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
