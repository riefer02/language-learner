# 12 — Gemini Live adapter: status and what the key unlocks

**Status:** Implemented both sides · verified against the live API with a real key (no microphone test yet) · 26 November 2026
**Why:** the realtime brief (`07`) found Gemini Live is the only speech-to-speech
model that lists Amharic. OpenAI's realtime voice does not list it, and its
transcription endpoint rejects `am` outright, so Amharic is at the provider's
ceiling today.

## Getting a key

1. **aistudio.google.com** → sign in → accept the terms. AI Studio creates a
   default project and API key.
2. Copy the key to `.env` as `GEMINI_API_KEY=…` (never commit it).
3. Leave `TEACHER_PROVIDER=openai_realtime` until the browser transport lands.

Free tier includes `gemini-3.8-live` audio, so the Amharic quality test costs
nothing. Caveat: free-tier prompts and audio are used to improve Google
products. Paid tier opts out: $3 / 1M audio input, $12 / 1M audio output
(≈ $0.005/min in, $0.018/min out), prepay minimum $5.

## Verified against the live API (26 Nov, with a real key)

The first run corrected three assumptions made from the docs:

| Assumed | Actually accepted |
|---|---|
| `liveConnectConstraints` on the token body | **`bidiGenerateContentSetup`** — the other name is rejected as an unknown field |
| `speechConfig` at the top of the setup | inside **`generationConfig.speechConfig`** |
| `START_SENSITIVITY_MEDIUM` | enum values are `START_SENSITIVITY_HIGH/LOW`, `END_SENSITIVITY_*` — `MEDIUM` is invalid |

Confirmed working end to end from a script: token minted (200), WebSocket opened
with the token, `setup` accepted (`setupComplete`), a text prompt returned
**audio chunks** plus `outputTranscription` reading `ደህና አደሩ።`. The Amharic voice
works; the browser path is the only untested piece.

## What exists now

`app/services/teacher_gemini.py`:

- `build_session()` — the Live `setup` payload. Reuses the language-scoped
  teacher prompt and the same six tools; audio out, input/output transcription
  on, automatic activity detection at the learner-tuned 900 ms silence.
- `function_declarations()` — converts the shared OpenAI-shaped tool schemas
  into Gemini function declarations (shallow JSON schema only).
- `mint_ephemeral_token()` — posts to the Auth Tokens endpoint with
  `liveConnectConstraints`, so the session config is locked server-side and the
  browser never sees the API key. Returns `(token_name, expires_at)`.
- `GeminiLiveProvider` — `transport = "websocket"`, `create_handle()` returns
  `{transport, url, token, model, session_config, token_expires_at}`.

`teacher.py` selects the provider from `TEACHER_PROVIDER`; `create_session`
skips SDP validation for the websocket transport and returns the provider's
handle straight to the route, which merges it into the JSON body next to
`session_id`, `max_minutes`, and `expires_at`.

If `gemini_live` is selected today, the page refuses cleanly:
*"Gemini Live is configured, but the browser transport is not wired yet."*
Nothing hangs, and no WebRTC call is attempted with a session that has no SDP.

## Review fixes (same day)

- **Coach hint follows the provider.** With `TEACHER_PROVIDER=gemini_live`,
  `coach_reply()` calls `gemini_json_completion()` (`:generateContent`, JSON
  mime type, `GEMINI_TEACHER_TEXT_MODEL`) instead of OpenAI. Previously the
  translation and suggested line silently 503'd without an OpenAI key.
- **The prompt no longer ships to the browser.** The constrained token carries
  the full setup server-side; the client now sends `{setup: {model}}` only, which
  was verified against the live API (`setupComplete`).
- **Playback honours the chunk's own rate** (`mimeType: ...;rate=24000` parsed
  per chunk) instead of assuming 24 kHz.
- **`AudioWorklet` microphone tap** (`pcm-worklet.js`) with a
  `ScriptProcessorNode` fallback; batches 2048 frames (~40 ms) instead of
  posting every 128-frame quantum.
- **`goAway` ends the lesson cleanly** (finishes, loads the debrief) instead of
  leaving a dead socket.
- **Gemini tool calls are deduped** by call id, matching the OpenAI path.
- **CSP** now allows `wss://generativelanguage.googleapis.com` in `connect-src`;
  without it the browser would have blocked the socket outright.
- `teardown(keepState)` replaces the DOM-sniffing that decided whether to keep
  an error chip.

## What still needs a human

1. **A real microphone test.** The protocol is verified from a script; the
   browser path (permissions, AudioContext resume, PCM playback cadence, echo)
   needs one live call.
2. **Turn detection tuning.** `END_SENSITIVITY_LOW` + 900 ms is the starting
   point; expect to tune after hearing it.
3. **Session limits.** Gemini Live caps audio-only sessions at 15 minutes and
   recycles connections around 10; `sessionResumption` and context handling are
   not implemented. Our 15-minute cap lines up with theirs by accident.
4. **Barge-in.** `interrupted` stops playback locally; whether Gemini's own
   activity detection cancels the model turn needs the live test.
5. **Playback via `ScriptProcessorNode`** (deprecated but universal). Move to an
   `AudioWorklet` once the flow is proven.

## Honest status of the server code

Written against the published Live API shape, not yet exercised with a key.
The network call is isolated in `mint_ephemeral_token()`; if the endpoint or
payload shape has moved, the fix is confined there. The session builder and the
tool-schema conversion are covered by tests, so a wrong Auth Tokens call is a
small correction, not a rewrite.
