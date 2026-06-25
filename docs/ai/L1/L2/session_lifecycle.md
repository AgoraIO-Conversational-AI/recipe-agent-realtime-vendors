# Deep Dive — Session Lifecycle

> **When to Read This:** You are touching client-side join, token renewal, RTC/RTM wiring, vendor selection from the browser, transcript handling, or mid-call control. For the contracts these calls hit, see [06_interfaces](../06_interfaces.md).

The browser owns the full RTC/RTM client lifecycle; the backend owns tokens, vendor selection, and the agent session. The two meet only at `/api/*`.

## End-to-end flow

1. **Vendor list** — `LandingPage.tsx` calls `getVendors()` → `GET /api/vendors`. Backend returns `{ default, vendors: [{name, needs_key, required_env}] }`. The pre-call dropdown populates from this response.
2. **Config** — `LandingPage.tsx` calls `getConfig()` → `GET /api/get_config`. Backend mints a Token007 (RTC+RTM, 3600s) for a concrete non-zero UID and returns `{ app_id, token, uid, channel_name, agent_uid }`. This step is key-less.
3. **Join** — `ConversationComponent.tsx` joins the RTC channel with the returned token/UID, publishes the microphone, and logs in to RTM.
4. **Start agent** — `startAgent(channelName, rtcUid, userUid, vendor?)` → `POST /api/startAgent`. Backend calls `build_vendor(selected)` (raising 400 if credentials are missing), builds the MLLM, starts the async session, and returns `agent_id` + `vendor` (resolved).
5. **Converse** — user audio flows to the selected realtime vendor; agent voice returns into the channel. RTM delivers transcript + metrics.
6. **Stop** — `stopAgent(agentId)` → `POST /api/stopAgent`. The client also releases RTC/RTM media on end-call.

## Backend session bookkeeping

`Agent` (`server/src/agent.py`) keeps an in-memory map `self._sessions[agent_id] = session`.

- `stop(agent_id)` pops the session and calls `session.stop()`.
- If the session is missing (e.g. process restarted), it falls back to `self.client.stop_agent(agent_id)` — the stateless cloud path. This is why stop is robust across restarts but `_sessions` itself is **not** a durable store.

## Transcript handling (`web/src/lib/conversation.ts`)

- `normalizeTranscript(transcript, localUid)` — maps `uid === '0'` to the local UID and runs `normalizeTranscriptSpacing` on text.
- `normalizeTimestampMs(ts)` — promotes second-precision timestamps to ms.
- `getMessageList` / `getCurrentInProgressMessage` — split finalized vs in-progress turns (by `TurnStatus.IN_PROGRESS`).
- `mapAgentVisualizerState(agentState, isConnected, connectionState)` — maps SDK state → UIKit visualizer state (`joining`, `listening`, `analyzing`, `talking`, `ambient`, `disconnected`).

## Token renewal

Tokens expire at 3600s. The client re-fetches config / renews as needed in `LandingPage.tsx`; renewal uses the same `get_config` contract. Keep renewal client-side — the backend stays stateless about who is connected.

## What stays where

- **Client owns:** RTC join, mic publish, RTM login, transcript/metrics/state listeners, token renewal, vendor dropdown population, explicit end-call media release.
- **Backend owns:** token minting, vendor build (including credential validation), session start/stop.
- Do not move token or vendor-credential logic into the web app or add Route Handlers for it (see [07_gotchas](../07_gotchas.md)).

## Related L1

- [02_architecture](../02_architecture.md) · [03_code_map](../03_code_map.md) · [06_interfaces](../06_interfaces.md)
