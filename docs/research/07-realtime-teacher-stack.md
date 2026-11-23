# 07 — Real-time AI Teacher: Stack, Architecture, Latency, and Cost

**Status:** Research brief · 23 November 2026
**Applies to:** Kiku (Flask 2.x / SQLAlchemy / SQLite prototype, single VPS), Korean today, Amharic/Ethiopian languages next.
**Question:** the learner presses a button and *talks* to a teacher that answers, drills on the spot, corrects, and writes terms into the personal dictionary.

**Method.** Read `05-tech-and-ai.md` and `04-competitive-teardown.md` first and did not re-derive their conclusions. Every number below was re-checked against vendor pricing/docs or independent benchmarks in November 2026. Tags: **[D]** vendor documentation, **[V]** vendor marketing claim, **[M]** independent measurement, **[U]** unverified / inferred / region- or account-dependent. Marketing latency is treated as a floor, not a fact.

**One-paragraph answer.** Build the teacher as a **tool-calling voice agent whose brain is a realtime speech model, whose hands are six Flask endpoints, and whose memory is the existing `Item` / `ReviewCard` / FSRS tables**. For Korean and Amharic in one codebase, **Gemini 3.8 Live** is the only realtime speech-to-speech model that lists both languages, supports async tool calls and browser ephemeral tokens, and prices at $3/$12 per 1M audio tokens. Use **`gpt-realtime-2.1-mini`** as the Korean A/B and fallback. Do **not** put a WebSocket relay in front of the model for MVP; mint a 30-minute ephemeral token server-side and let the browser talk to the provider directly, with tool calls hitting Flask. Budget **$0.05–0.08 per realtime minute**, i.e. **$0.60–0.96 per 12-minute session** and **$2.50–3.00 per MAU** at 35% voice adoption, and ship in three phases: text-only teacher → push-to-talk → full duplex.

---

## 1. Speech-to-speech and realtime APIs

### 1.1 Comparison (November 2026)

Prices are USD, list, pay-as-you-go, excluding tax. For full-agent rows, "effective $/min" is for a **12-minute, 40-turn session with 8.4 minutes of speech**, so it includes the provider's history re-billing. STT-only/TTS-only rows are unit rates, not agent rates. Naive per-minute rate-card math understates every token-billed vendor by 2–4×.

| Product | Current model / ID | p50 voice→voice | Effective $/min | Korean | Amharic | Barge-in | Tool calls | Client token | Max session | Browser streams direct? |
|---|---|---|---|---|---|---|---|---|---|---|
| **OpenAI Realtime** | `gpt-realtime-2.1`, `gpt-realtime-2.1-mini` | **1.0 s** server VAD, 4.5 s semantic VAD default [M] | **$0.052** mini · **$0.164** full | ✅ strong | ❌ not in <50% WER list | ✅ | ✅ | ✅ 1-min `client_secret` | **60 min** [D] | ✅ WebRTC or WS |
| **Google Gemini Live** | `gemini-3.8-live`, `gemini-3.8-live-extended-thinking` | **1.06 s** p50 / 1.25 s p95 over 40 turns on 3.1 Flash [M]; 3.8 not independently measured [U] | **$0.071** (tunable to ~$0.05) | ✅ `ko-KR` | ✅ **`am` listed** | ✅ VAD interrupts; cancels pending tool calls | ✅ sync + **async (`NON_BLOCKING`) by default** | ✅ ephemeral, config-lockable | 15 min audio-only; 10 min connection; **unlimited with compression/resumption** [D] | ✅ WebSocket |
| **ElevenLabs Agents** | `eleven_v4_turbo` + Scribe v3 Live | ~1.0–1.3 s [U]; TTS ~100 ms [V] | **$0.083** + LLM | ✅ | ⚠️ TTS ✅ v4; ASR 25–50% WER | ✅ | ✅ server tools/webhooks | ✅ signed URL | 600 s default, max **7,200 s** [D] | ✅ widget/SDK |
| **Deepgram Voice Agent** | Nova-3 / Flux + Aura-2 or Flux TTS | ~1 s [V] | **$0.075** (BYO TTS $0.056) | ✅ | ⚠️ ASR ✅ (added 16 Nov 2026); **no Amharic voice** | ✅ | ✅ | ✅ temporary tokens | **2 h** [D] | ⚠️ WS; relay/SDK typical |
| **AssemblyAI** | `assemblyai-stt-3-7-realtime-agent` | STT + TTS; no agent orchestration | $0.0075/min STT | ✅ | ❌ batch-only, **>50% WER** | via partner | via partner | ✅ temp token | 3 h auto-close | ⚠️ WS |
| **Cartesia** | Sonic 3.6 TTS + Ink-2/Ink-whisper STT | TTS TTFB 164 ms [M] | TTS $38–65/1M chars | ✅ TTS; Ink-2 ❌ (5 langs) | ❌ | via partner | via partner | ✅ access token | n/a | ✅ WS |
| **Azure Voice Live** | `gpt-realtime-2.1` / `-mini`, `microsoft-realtime-flash-1` | ~1 s [U] | **$0.06–0.08** Standard | ✅ | ✅ ASR `am-ET` + TTS 2 voices; **not in realtime multilingual model** | ✅ | ✅ | ✅ STS token | not documented; test | ✅ WS/SDK |
| **Hume EVI** | EVI 3 / 4 mini | — | was $0.04–0.07 | ✅ | ❌ | ✅ | ✅ | ✅ | — | **☠️ shut down 13 Nov 2026** [D] |
| **Speechmatics** | Melia 1 / Linden 1 (agent STT) | STT only | $0.40–0.80/hr realtime | ✅ | ❌ | via Linden | via partner | ⚠️ API key server-side | n/a | ⚠️ WS |
| **Soniox** | `stt-rt-v6` + TTS | STT + TTS; no agent | $0.12/hr STT; ~$0.70/hr TTS | ✅ | ❌ | ✅ turn detection | via partner | ⚠️ API key server-side | n/a | ⚠️ WS |
| **Gladia** | Solaria-1 | partials <103 ms [V] | €0.68/hr ≈ $0.013/min | ✅ | ✅ **real-time** | ✅ | via partner | ⚠️ API key server-side | n/a | ⚠️ WS |
| **LiveKit Agents** | framework + Cloud | your pipeline | $0.01/min agent + models | ✅ | ✅ if you pick an `am` STT/TTS | ✅ (turn detector) | ✅ | ✅ JWT room token | none | ✅ WebRTC |
| **Pipecat** | BSD-2 framework (+ Cloud) | your pipeline | $0.01/min hosted agent | ✅ | ✅ if components do | ✅ | ✅ | ✅ Daily/JWT | none | ✅ WebRTC |

**Sources:** OpenAI pricing/model docs; Gemini pricing/Live docs; ElevenLabs pricing; Deepgram pricing; AssemblyAI pricing; Cartesia pricing; Azure pricing/Voice Live; Hume changelog; Speechmatics/Soniox/Gladia pricing; LiveKit/Pipecat pricing. Latency: Apptycoons 180-turn OpenAI benchmark [M], virevolai 40-turn cross-vendor benchmark [M]. Full URLs in §9.

### 1.2 The language reality check (this decides the stack)

**Korean is well served by everyone.** OpenAI lists Korean among languages under 50% WER; Gemini lists `ko-KR`; Azure has `ko-KR` STT/TTS/pronunciation; Deepgram, AssemblyAI, ElevenLabs, Soniox, Speechmatics and Gladia all transcribe Korean. What is *not* published is any independent **L2-Korean** WER or naturalness benchmark per vendor. Vendor "Korean support" means native/clean read speech; learner speech with pauses, self-correction and English code-switching will be worse everywhere. **Plan to run your own 100-clip L2 Korean eval before choosing a primary.**

**Amharic is the constraint.** Only these actually list it:

| Capability | Who genuinely supports `am` | Caveat |
|---|---|---|
| Realtime speech-to-speech | **Gemini 3.8 Live** | One of 99 listed languages; no published Amharic WER. Must be tested, not assumed. |
| Streaming ASR | **Azure `am-ET`**, **Deepgram Nova-3 `am`** (since 16 Nov 2026), **Gladia Solaria-1 `am`** | Azure has the longest track record; Deepgram's model is 7 days old at time of writing; Gladia publishes no Amharic WER. |
| Batch ASR | AssemblyAI Universal-2, ElevenLabs Scribe, Whisper | AssemblyAI itself rates Amharic **">50% WER — Fair"**; unusable as a product signal. Scribe rates it 25–50%. |
| TTS | **Azure** (`am-ET-AmehaNeural`, `am-ET-MekdesNeural`), **Gemini TTS** (`am-ET`, Preview), **ElevenLabs v4/v4 Turbo** (claims 90+ incl. `am`), Meta MMS, AmhTTS, Addis Voice 2 | Azure is fastest and cheapest; Gemini sounds best of the big clouds but is slow; ElevenLabs v3 scored **111% CER** on Amharic in a blind benchmark — v4 is unverified; MMS is CC-BY-NC and needs romanization. |
| Pronunciation scoring | **nobody** | See §5. |

**Consequence:** for Korean you can choose on latency/cost/quality. For Amharic you choose Gemini Live (native audio) *or* a cascaded pipeline (Azure/Gladia/Deepgram ASR + Azure/Addis/Gemini TTS), and you must accept a thinner quality bar. Do not promise Amharic pronunciation scores in 2026.

### 1.3 Provider notes that change architecture

**OpenAI Realtime.** GA family is `gpt-realtime-2.1` and `-mini`; original `gpt-realtime` shuts down **20 Jan 2027**. 128k context, 60-minute hard session cap, WebRTC or WebSocket, ephemeral `client_secret` expires in **1 minute** but the session runs 60. Server VAD at 500 ms gave the best measured turn-end (p50 0.3 s) and 1.0 s voice-to-voice; **semantic VAD at default eagerness is a 4.5-second trap** — use `eagerness: high` or server VAD. Tool calls work over the same socket. Audio in is 24 kHz PCM16, not 16 kHz.

**Gemini 3.8 Live.** The strongest architectural fit for Kiku: `am` + `ko`, **asynchronous function calling is the default** (`NON_BLOCKING` with `SILENT` / `WHEN_IDLE` / `INTERRUPT` scheduling), so `create_drill` can write to Postgres while the teacher keeps talking. Ephemeral tokens can be **locked to the model and session config server-side**, so (where the API version supports it) the system prompt and tool list never ship to the client — verify this before relying on it (§2.3). Costs are the catch: audio input is billed at $3/1M (25 tokens/s) and **every turn re-sends the whole audio history**, so a long session grows super-linearly (an independent 40-turn test on 3.1 Flash measured **17.3× cost growth turn 40 vs turn 1**; 3.8 is unmeasured). Enable `context_window_compression` with a low `trigger_tokens` (~4k) and a small `target_tokens` (~1k): the database is the memory, the context window is only conversational glue. Audio-only sessions die at 15 min without compression; connections recycle at ~10 min, so implement `sessionResumption`.

**ElevenLabs.** Best voice *control* and a strong library, though not the top Korean naturalness in blind tests (Speko puts it 4th). v4 now claims Amharic. Agents are a **cascaded** stack (Scribe ASR → your LLM → ElevenLabs TTS + their turn model), not speech-to-speech, at **$0.08/min platform + LLM at cost**. That is ~$0.96 per 12-minute session before the LLM. ElevenLabs is the right *TTS* vendor for pre-generated curriculum and the wrong *primary brain* for a cost-sensitive tutor.

**Deepgram.** One WebSocket for STT + managed LLM + TTS at $0.075/min is the simplest hosted agent. Korean TTS is "Early Access" with **no text normalization** per a third-party language matrix [U], which matters for numbers/prices in drills. Amharic ASR landed 16 Nov 2026 but there is **no Amharic Deepgram voice**, so Amharic forces BYO TTS.

**Azure Voice Live.** The enterprise-safe option: OpenAI-compatible realtime plus Azure voices, `am-ET` included. But its multilingual realtime model only covers 15 locales and **does not include Amharic**; to get Amharic you must use an Azure-STT-backed configuration (e.g. `microsoft-realtime-flash-1` + `input_audio_transcription.model = "azure-speech"`, `language = "am-ET"`), not the native-audio path, and accept lower accuracy. That is the **Lite** tier (~$4/$12 per 1M native audio) plus Azure STT/TTS meters, not Standard. Pronunciation Assessment is a separate, better reason to have an Azure account.

**Hume is dead.** EVI and Octave were sunset on **13 Nov 2026**; account data deleted after. Do not evaluate it.

**Frameworks.** LiveKit Agents (WebRTC rooms + agent worker, $0.01/min hosted or Apache-2.0 self-host) and Pipecat (BSD-2 pipeline framework, $0.01/min Cloud) are for *cascaded* pipelines. They buy you jitter buffers, mobile audio, SIP, turn detection and observability — at the cost of a second runtime and a media server. Neither is needed for a browser-only, push-to-talk MVP.

### 1.4 What "supports Korean well" should mean for Kiku

Score each candidate on your own data, not the language list:

1. **L2 Korean WER** on 100 clips: 30 beginner, 40 intermediate, 30 with English code-switching.
2. **Proper-noun and number reading** (a drill says "3,000원", "2시 30분").
3. **Particle/honorific preservation** in the transcript — ASR that "repairs" 은/는 destroys the error signal.
4. **Turn-end behavior on mid-sentence pauses** — beginners pause inside sentences; aggressive VAD cuts them off.
5. **Amharic intelligibility** judged by 2 native speakers, not by WER alone (ejectives and gemination are invisible to WER).

---

## 2. Architecture options for Flask/SQLAlchemy on one VPS

### 2.1 Four options

| | (a) Browser ↔ provider direct, server-minted token | (b) Server relay / WS proxy | (c) LiveKit rooms + agent worker | (d) Pipecat pipeline |
|---|---|---|---|---|
| **Latency added** | **0–20 ms** | 40–120 ms + jitter | 30–80 ms (WebRTC, but better jitter handling) | 40–100 ms |
| **Complexity** | Low: 3–4 endpoints + JS | Medium: async WS bridge in a sync Flask app | High: media server + worker + room lifecycle | High: pipeline graph + transport |
| **Cost** | Provider only | Provider + VPS egress/CPU | +$0.01/min agent, +WebRTC | +$0.01/min or self-host |
| **Secrets** | Ephemeral token only; prompt/tools lockable (Gemini) | Keys stay server-side | Keys server-side | Keys server-side |
| **Observability** | Weaker; log tool calls + client events | **Best**: every frame/transcript | Good (LiveKit metrics) | Good (your code) |
| **Tool calls → Flask DB** | Browser receives `tool_call`, POSTs to Flask | Relay executes directly | Agent worker calls Flask | Pipeline processor calls Flask |
| **Abuse control** | Per-user token + quota; harder to cut mid-session | Easy to cut/limit/redact | Easy | Easy |
| **Mobile/browser audio** | WebRTC (OpenAI) or WS (Gemini); you own jitter/echo | same | **Best** | Good |
| **Best for** | **MVP, browser-only** | compliance/recording, debugging | scale, mobile, SIP | cost-optimized cascaded, multi-provider |

### 2.2 Recommendation

**MVP (now → ~6 months): option (a) + push-to-talk.** Direct browser WebSocket to Gemini Live with a server-minted, config-locked ephemeral token; six Flask tool endpoints; no relay, no LiveKit, no media server. Flask stays synchronous. If you need a streaming sidecar later, add **FastAPI + `uvicorn`** rather than making Flask async — `05-tech-and-ai.md` already recommends this strangler pattern.

**Scale (multi-provider, mobile, cost control): option (c) LiveKit Cloud + an agent worker, or (d) Pipecat self-hosted.** Use a cascaded pipeline (Deepgram/Gladia/Azure STT → `gpt-4.1-mini` → Cartesia/Azure TTS) for the 80% of sessions that are drills, and reserve native speech-to-speech for free conversation. LiveKit if you need mobile/SIP and want managed WebRTC; Pipecat if you want to own the pipeline and squeeze cost. Keep the same six tool contracts so the brain is swappable.

**Do not build (b) for MVP.** A Flask WebSocket proxy is the worst of both worlds on a single VPS: you pay the latency and the bandwidth, and you inherit reconnect/backpressure bugs, without the observability payoff unless you build a full event pipeline. Build it only when you need server-side recording/redaction for a compliance customer.

### 2.3 Token-minting Flask endpoint (sketch)

```python
# app/blueprints/teacher.py  — sketch only; not applied to the repo
from datetime import datetime, timedelta, timezone
from flask import Blueprint, abort, current_app, jsonify, request, url_for
from flask_login import current_user, login_required
from app import db
from app.models import TeacherSession          # new table, see §4.6

bp = Blueprint("teacher", __name__, url_prefix="/api/teacher")

SYSTEM_PROMPT = {  # kept server-side, not shipped as editable client config
    "ko": "You are Kiku's Korean teacher. ...",
    "am": "You are Kiku's Amharic teacher. ...",
}

@bp.post("/session")
@login_required
def create_session():
    lang = (request.get_json(silent=True) or {}).get("lang", "ko")
    if lang not in {"ko", "am"}:
        abort(400, "unsupported language")
    if not current_app.extensions["quota"].allow(current_user, minutes=12):
        abort(429, "daily voice minutes exhausted")

    session = TeacherSession(
        user_id=current_user.id, lang=lang,
        status="open", started_at=datetime.now(timezone.utc),
        max_minutes=12,
    )
    db.session.add(session)
    db.session.commit()

    # Google Gen AI SDK: token is locked to model + config, so the client
    # cannot swap the system prompt, tools, or model.
    token = current_app.extensions["genai"].auth_tokens.create(config={
        "uses": 1,
        "expire_time": datetime.now(timezone.utc) + timedelta(minutes=30),
        "new_session_expire_time": datetime.now(timezone.utc) + timedelta(minutes=1),
        "live_connect_constraints": {
            "model": "gemini-3.8-live",
            "config": {
                "response_modalities": ["AUDIO"],
                "system_instruction": SYSTEM_PROMPT[lang],
                "tools": [{"function_declarations": TOOL_DECLARATIONS[lang]}],
                "session_resumption": {},
                "context_window_compression": {
                    "trigger_tokens": 4000,
                    "sliding_window": {"target_tokens": 1000},
                },
                "input_audio_transcription": {},
                "output_audio_transcription": {},
            },
        },
    })

    return jsonify({
        "session_id": session.public_id,
        "token": token.name,                 # ~30 min message window
        "ws_url": current_app.config["GEMINI_LIVE_WS"],
        "tool_url": url_for("teacher.tool_call"),
        "expires_in": 1800,
        "max_minutes": 12,
        "lang": lang,
    })
```

> **Verify before shipping:** whether your Gemini API version accepts `system_instruction`, `tools` and `context_window_compression` inside `live_connect_constraints.config`. If it only permits model + modalities, send those fields in the first `setup` message over the socket and keep them server-generated; the token still prevents model/key swapping, but a determined client can edit its own setup. In that case either accept a server-side tool allow-list as the real boundary, or use a short-lived relay that opens the socket and forwards frames.

**OpenAI equivalent** (if you A/B or fall back):

```python
@bp.post("/session/openai")
@login_required
def create_openai_session():
    r = current_app.extensions["openai"].realtime.sessions.create(
        model="gpt-realtime-2.1-mini",
        voice="marin",
        modalities=["audio"],
        instructions=SYSTEM_PROMPT["ko"],
        tools=OPENAI_TOOLS,
        turn_detection={"type": "server_vad", "silence_duration_ms": 500},
    )
    # client_secret.value expires in 60 s; browser connects immediately
    return jsonify({"token": r.client_secret.value,
                    "session_id": r.id, "expires_at": r.client_secret.expires_at})
```

**Tool execution endpoint** — one endpoint, allow-listed dispatch, idempotency key:

```python
@bp.post("/tool")
@login_required
def tool_call():
    body = request.get_json(force=True)
    session = TeacherSession.by_public_id_or_404(body["session_id"])
    if session.user_id != current_user.id or session.is_closed:
        abort(403)

    handler = TOOL_HANDLERS.get(body["name"])
    if handler is None:
        abort(400, "unknown tool")

    # client retries are safe: (session_id, call_id) is unique
    result = handler(current_user, session, body.get("args", {}),
                     call_id=body["call_id"])
    return jsonify({"call_id": body["call_id"], "name": body["name"],
                    "result": result})
```

Tool latency budget: **≤ 80 ms p50** for reads (`get_due_items`, `lookup_dictionary`) and **≤ 150 ms** for writes (`create_drill`, `add_term_to_library`), measured server-side. Put an index on `review_card(user_id, due_at)` (already present) and keep `create_drill` to a single transaction.

### 2.4 Event flow: speak → respond → drill → FSRS → transcript

```
 ┌──────────┐  1. press-to-talk / open mic (16 kHz PCM, local Silero VAD)
 │ Browser  │──────────────────────────────────────────────────────────┐
 │  (PWA)   │                                                          │
 └────┬─────┘                                                          │
      │ 2. WSS audio frames + ephemeral token                          │
      ▼                                                                │
 ┌─────────────────────────────┐                                       │
 │ Gemini 3.8 Live             │  3. VAD detects end of turn           │
 │ (native audio, ko/am)       │     → model starts speaking           │
 └──────┬──────────────────────┘                                       │
        │ 4. tool_call: create_drill(target_item_ids=[...])            │
        ▼                                                              │
 ┌──────────┐  5. POST /api/teacher/tool  {call_id, name, args}       │
 │ Browser  │─────────────────────────────────────────────────────────▶│
 └──────────┘                                                          │
                                                                       ▼
                                                     ┌──────────────────────────────┐
                                                     │ Flask + SQLAlchemy           │
                                                     │  a. authz + quota            │
                                                     │  b. validate drill (Kiwi /   │
                                                     │     HornMorpho + rules)      │
                                                     │  c. INSERT drill, drill_items│
                                                     │  d. INSERT review_cards      │
                                                     │     (FSRS, due=now+10 min)   │
                                                     │  e. INSERT event             │
                                                     └──────────────┬───────────────┘
                                                                    │ 6. {drill_id, items[]}
 ┌──────────┐  7. tool_response (scheduling=WHEN_IDLE)               │
 │ Browser  │◀───────────────────────────────────────────────────────┘
 └────┬─────┘
      │ 8. send toolResponse back to Live session
      ▼
 ┌─────────────────────────────┐
 │ Gemini 3.8 Live             │  9. teacher speaks the drill prompt
 └──────┬──────────────────────┘
        │ 10. audio deltas + output transcription
        ▼
 ┌──────────┐  11. render drill card; queue FSRS cards in UI
 │ Browser  │      (optimistic; server is source of truth)
 └────┬─────┘
      │ 12. learner answers (audio) → model grades → grade_attempt
      │ 13. batched transcript flush every 1 s / on turn end
      ▼
 ┌──────────────────────────────┐
 │ POST /api/teacher/transcript │ → teacher_sessions.transcript (jsonb/text)
 │ POST /api/teacher/end        │ → end_session_summary, recompute FSRS
 └──────────────────────────────┘
```

**Critical ordering:** the drill must be **persisted before the teacher speaks it**. If the model says "here are three sentences" and the DB write fails, the learner hears a drill that does not exist and cannot review it. Treat `create_drill` as a **BLOCKING** tool for the first version; use `NON_BLOCKING` + `WHEN_IDLE` only for read-only lookups. Gemini 3.8 Live defaults tools to non-blocking, so set `behavior: "BLOCKING"` explicitly on writes, or accept that a cancelled call must be idempotent and may need compensation.

### 2.5 Security checklist for option (a)

- Mint tokens only after login; bind token to `user_id`, `lang`, model, prompt, tools, and max minutes.
- One concurrent session per user; reject a second token while one is open (prevents token farming and cost blowups).
- Per-user daily voice-minute cap and a global kill switch (env flag) that stops token minting.
- Browser never sees provider API keys; only the ephemeral token (Gemini ~30 min, OpenAI ~1 min).
- `tool_call` validates session ownership, tool allow-list, argument schema, and idempotency; never trust `user_id` from the client.
- Store transcripts only with consent; store **no raw audio** by default (matches `SpeechAttempt`'s existing "raw audio is never stored" stance).
- Strip PII from logs; redact emails/phone numbers in transcripts before persistence.
- Age gate; no open-ended romantic/personal roleplay with minors; no voice cloning of the learner.

---

## 3. Latency budget

### 3.1 Hop-by-hop

Push-to-talk (PTT) means the endpoint is the button release; full duplex means the model's VAD decides.

| Hop | PTT (ms) | Full duplex (ms) | Notes |
|---|---|---|---|
| Local VAD / endpointing | 0 (button) | **150–500** | Silero VAD at 16 kHz; 300 ms silence is a good beginner default. Server/semantic VAD can be 1–4 s — avoid. |
| Capture + encode + uplink | 20–60 | 20–60 | Opus or PCM16; 16 kHz mono; same-region provider. |
| STT finalization | 80–200 | 80–200 | Streaming partials already done; only the final commit is on the critical path. |
| LLM TTFT | 250–500 | 250–500 | `gpt-realtime-2.1-mini` measured 0.51–0.57 s from speech-stop to first audio (model time); Gemini similar. Reasoning effort / "extended thinking" doubles it. |
| Tool round-trip (if any) | 30–80 read · 60–150 write | same | Same VPS, SQLite/Postgres; add 100–150 ms if Flask is in another region. |
| TTS first byte | 90–300 | 90–300 | Cartesia 164 ms, ElevenLabs 206 ms, OpenAI 433 ms, Gemini 531 ms (Korean, US-East) [M]. Native speech-to-speech folds this into model time. |
| Downlink + jitter buffer | 40–100 | 40–100 | WebRTC handles this better than raw WS. |
| **Realistic total** | **510–1,240 (p50 ~750)** | **700–1,600 (p50 ~1,050)** | Independent tests: OpenAI 1.0 s, Gemini 3.1 Flash 1.06 s; production stacks report 1.1–1.3 s p50. |

### 3.2 What must be under 800 ms

For the interaction to feel like a teacher rather than a walkie-talkie:

- **Endpoint → first audio ≤ 800 ms p50, ≤ 1.4 s p95** on PTT.
- **Endpointing itself ≤ 300 ms** on full duplex; if VAD alone eats 500 ms, the model has 300 ms left and you lose.
- **Tool write ≤ 150 ms** or the teacher must say a filler ("자, 하나 더…") while it completes. Never leave >400 ms of silence after a tool call.
- **First syllable must be intelligible**; a 90 ms TTFB with a 300 ms playback buffer is worse than 200 ms TTFB with 80 ms buffer.

### 3.3 Concrete tactics

1. **Local VAD (Silero) in the browser**, not provider VAD, for PTT and for "did they stop talking?" Use 16 kHz mono PCM (Gemini/Deepgram native); OpenAI Realtime wants 24 kHz, so resample once at the edge, not per hop.
2. **Push-to-talk for MVP.** It removes 300–500 ms of VAD uncertainty and is *better* for beginners who pause mid-sentence. In PTT mode, **disable provider auto-VAD** (Gemini: `automatic_activity_detection.disabled` + explicit `activityStart`/`activityEnd`; OpenAI: `turn_detection: null` + `input_audio_buffer.commit`) so the button, not a silence timer, ends the turn.
3. **Stream tool results.** Send `tool_response` with `scheduling="WHEN_IDLE"` so the model finishes its current sentence, then speaks the drill. For `get_due_items`, prefetch at session start, not on the first drill.
4. **Pre-synthesize common phrases.** "다시 한 번 말해 볼까요?", "좋아요!", "조금 더 크게" are closed-set; cache Opus at −16 LUFS and play instantly. This removes TTS from the most common turns.
5. **Speculative drill prefetch.** When the session starts, generate 2 candidate drills in the background (one review-heavy, one new-item) so `create_drill` becomes a DB insert + validation, not an LLM call.
6. **Cap output length.** `max_response_output_tokens` (OpenAI) or a prompt rule "≤ 2 sentences, ≤ 12 seconds" prevents 40-second teacher monologues that wreck perceived latency and cost.
7. **Region pin.** Put the VPS and provider endpoint in the same region (e.g. `asia-northeast3` for Korean learners, `us-central1` for Amharic-first). Cross-Pacific adds 120–180 ms RTT.
8. **Warm the socket.** Open the WS on screen mount, not on button press; cold connect costs 300–800 ms.
9. **Don't chase vendor "100 ms" claims.** Those are model TTFB excluding network, turn detection and playback. Budget 1 s end-to-end and optimize the p95.

### 3.4 Instrumentation

Log per turn: `t_speech_end`, `t_stt_final`, `t_llm_first_token`, `t_tool_start/end`, `t_tts_first_byte`, `t_play_start`. Emit one `Event(name="teacher_turn")` with those deltas. Gate release on p50 ≤ 800 ms and p95 ≤ 1,400 ms; alert if p95 > 2 s for 10 minutes.

---

## 4. Drill generation and the pedagogy loop

### 4.1 Why "just chat" fails

A general voice model defaults to **conversation**, not **instruction**. It will answer questions, compliment the learner, and ask another question — the exact failure mode documented in `04-competitive-teardown.md`: "the AI asks a question every turn" and corrections are shallow. Three mechanisms fix it:

1. **The model does not choose the content.** Flask supplies the target items from the FSRS due queue; the model only realizes them.
2. **The model must call a tool to produce a drill.** A drill that exists only in audio is not reviewable and cannot be scheduled.
3. **Every generated sentence is validated before it is spoken.** Korean with Kiwi + rules + krdict; Amharic with HornMorpho + a curated lexicon + native review.

### 4.2 System prompt contract (per language, server-side)

```
ROLE
You are Kiku's {Korean|Amharic} teacher. You are warm, brief, and concrete.
You teach {learner_name}, level {CEFR} / TOPIK {n}, L1 {english|...}.

HARD RULES
1. Speak the target language ≥80% of the time. Max 2 sentences per turn.
2. Never introduce a lexical item, grammar pattern, or idiom that is not in
   TOOL RESULTS or in <allowed_items>. If the learner asks for a new word,
   call lookup_dictionary. If it is not found, do NOT guess a gloss; say you
   will save it for review, and call add_term_to_library only with a gloss the
   learner or the dictionary supplied.
3. To drill, you MUST call create_drill. Never improvise a drill in audio only.
4. Correct at most 2 errors per turn, and only errors tagged in <error_taxonomy>.
   Prefer an implicit recast, then one explicit correction at the end.
5. Do not invent romanization. Read it from the item or say nothing.
6. Ask exactly one question at a time. Wait for the answer.
7. If the learner is silent >4 s, offer a hint, then the answer, then move on.
8. Never claim a score you did not receive from grade_attempt.
9. End every session by calling end_session_summary.

SESSION SHAPE (12 min)
0:00 warm-up (2 turns, free chat, 1 target item)
1:30 review drill (get_due_items → create_drill, 4–6 items)
7:00 new item (lookup_dictionary → create_drill, 2–3 items)
10:30 production (roleplay or free answer using today's items)
11:30 end_session_summary
```

**Level gating.** Store `cefr` on the user (derived from placement + Elo) and map to `Item.level` (1–6). The prompt gets `max_new_items=2`, `max_tokens_per_sentence`, and a banned list (e.g. no `-습니다` for a `haeyo`-only learner until level 3). Enforce server-side: `create_drill` rejects any `source_item_id` not in the learner's allowed set or above `max_level`. The server also force-closes at `max_minutes` and synthesizes a summary if the model never called `end_session_summary`; never trust the model to end the session.

### 4.3 Tool / JSON schemas

These are deliberately small. `additionalProperties: false` everywhere; the server re-validates with Pydantic. **Portability note:** OpenAI strict mode accepts this JSON Schema directly; Gemini's `FunctionDeclaration` uses an OpenAPI subset and may reject `additionalProperties` / `$ref`, and its REST enums are upper-case (`OBJECT`, `STRING`). Keep one canonical schema in Python, generate the provider-specific dialect at startup, and never hand-maintain two copies.

**`get_due_items`** — read-only, prefetch at session start.

```json
{
  "name": "get_due_items",
  "description": "Return up to N FSRS-due items for this learner, ordered by overdue-ness. Never invent items.",
  "parameters": {
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "minimum": 1, "maximum": 12},
      "skills": {"type": "array", "items": {"enum": ["recognize","recall","listen","pronounce","conjugate"]}},
      "item_types": {"type": "array", "items": {"enum": ["lexeme","grammar","sentence","minimal_pair","dialogue_line"]}},
      "max_level": {"type": "integer", "minimum": 1, "maximum": 6}
    },
    "required": ["limit"],
    "additionalProperties": false
  }
}
```

Returns `{items:[{item_id, surface, gloss, romanization, level, skill, due_at, lapses}], count}`. Implementation: `ReviewCard` join `Item` where `user_id=:u and due_at<=now()` order by `due_at`, with a cap of 12 and a ban on leeches (lapses ≥ 4) unless `skill="recognize"`.

**`lookup_dictionary`** — the only way the model may introduce a new word.

```json
{
  "name": "lookup_dictionary",
  "description": "Look up a term in the curated dictionary. Returns canonical spelling, gloss, POS, level, and whether it already exists as an Item.",
  "parameters": {
    "type": "object",
    "properties": {
      "term": {"type": "string", "minLength": 1, "maxLength": 80},
      "language": {"enum": ["ko", "am"]},
      "include_examples": {"type": "boolean", "default": true}
    },
    "required": ["term", "language"],
    "additionalProperties": false
  }
}
```

Korean: krdict API + local `Item`/`DictionaryEntry` table; reject if not found and not in the curated list. Amharic: local curated lexicon (see §4.4); there is no equivalent free learner dictionary API, so return `found:false` rather than guessing. If the language-neutral schema is live, read `DictionaryEntry`/`DictionarySense`; otherwise read `Item`.

**`create_drill`** — write, BLOCKING, idempotent on `(session_id, call_id)`.

```json
{
  "name": "create_drill",
  "description": "Persist a graded drill and create/refresh FSRS cards. Call before speaking the drill.",
  "parameters": {
    "type": "object",
    "properties": {
      "language": {"enum": ["ko", "am"]},
      "goal": {"enum": ["recognition","production","listening","pronunciation","conjugation","roleplay"]},
      "level": {"type": "integer", "minimum": 1, "maximum": 6},
      "target_item_ids": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "maxItems": 5},
      "prompt_en": {"type": "string", "maxLength": 200},
      "items": {
        "type": "array", "minItems": 3, "maxItems": 8,
        "items": {
          "type": "object",
          "properties": {
            "kind": {"enum": ["say","choose","fill_blank","translate","repeat","minimal_pair"]},
            "target": {"type": "string", "maxLength": 120},
            "gloss": {"type": "string", "maxLength": 120},
            "options": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "answer": {"type": "string", "maxLength": 120},
            "audio_required": {"type": "boolean"},
            "source_item_id": {"type": "integer"}
          },
          "required": ["kind", "target", "answer", "source_item_id"],
          "additionalProperties": false
        }
      },
      "register": {"enum": ["haeyo", "hapshida", "banmal", "polite_am"]},
      "expected_seconds": {"type": "integer", "minimum": 30, "maximum": 300}
    },
    "required": ["language", "goal", "level", "target_item_ids", "items"],
    "additionalProperties": false
  }
}
```

Server contract:
- Every `target_item_id` and every item's `source_item_id` must belong to the learner's allowed set; otherwise `422`. This is the whitelist that stops the model inventing vocabulary.
- Validate each `target` / `answer` (see §4.4); reject the whole drill if any item fails.
- Insert `Drill` + `DrillItem` rows, then upsert `ReviewCard(user, item, skill)` with `due_at = now + 10 min` for new cards, leaving existing FSRS state intact.
- Return `{drill_id, items:[{index, item_id, surface, audio_url|null}], expires_at}`.

**`grade_attempt`**

```json
{
  "name": "grade_attempt",
  "description": "Record one learner answer, update FSRS, and return a short correction.",
  "parameters": {
    "type": "object",
    "properties": {
      "session_id": {"type": "string", "maxLength": 40},
      "drill_id": {"type": "string", "maxLength": 40},
      "item_index": {"type": "integer", "minimum": 0, "maximum": 20},
      "transcript": {"type": "string", "maxLength": 500},
      "latency_ms": {"type": "integer", "minimum": 0},
      "self_report": {"enum": ["again", "hard", "good", "easy"]},
      "error_tags": {"type": "array", "items": {"enum": [
        "particle","verb_ending","honorific","register","word_order",
        "vocabulary","spacing","pronunciation_segment","pronunciation_prosody",
        "gemination","ejective","none"
      ]}, "maxItems": 3}
    },
    "required": ["session_id", "drill_id", "item_index", "transcript"],
    "additionalProperties": false
  }
}
```

Server derives correctness (exact/normalized match + acceptable variants), maps to FSRS rating (`again=1, hard=2, good=3, easy=4`), writes `ReviewLog`, and returns `{correct, score, expected, feedback_target, next_due}`. The model may only phrase `feedback_target` in the target language; it may not invent the score.

**`add_term_to_library`**

```json
{
  "name": "add_term_to_library",
  "description": "Add a confirmed term to the learner's personal dictionary and optionally create a card.",
  "parameters": {
    "type": "object",
    "properties": {
      "language": {"enum": ["ko", "am"]},
      "surface": {"type": "string", "minLength": 1, "maxLength": 80},
      "gloss": {"type": "string", "minLength": 1, "maxLength": 160},
      "pos": {"type": "string", "maxLength": 20},
      "example": {"type": "string", "maxLength": 200},
      "source": {"enum": ["learner_request", "teacher_introduced", "dictionary"]},
      "create_card": {"type": "boolean", "default": true}
    },
    "required": ["language", "surface", "gloss"],
    "additionalProperties": false
  }
}
```

Server: dedupe on `(language, normalized surface)`; on the language-neutral schema attach a `ItemForm` + `ItemGloss` and a learner `TermCard`; on the legacy schema create `Item` with `item_type="lexeme"`, `level` from frequency band or learner level, and a `ReviewCard(skill="recognize")` due in 10 min. Return `{item_id, created:true|false}`; the card is what makes the term reviewable.

**`end_session_summary`**

```json
{
  "name": "end_session_summary",
  "description": "Close the session with a 2-strength/1-fix debrief and next focus.",
  "parameters": {
    "type": "object",
    "properties": {
      "session_id": {"type": "string", "maxLength": 40},
      "items_practiced": {"type": "integer", "minimum": 0},
      "accuracy": {"type": "number", "minimum": 0, "maximum": 1},
      "strengths": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
      "fixes": {"type": "array", "items": {"type": "string"}, "maxItems": 1},
      "new_terms": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
      "next_session_focus": {"type": "string", "maxLength": 120}
    },
    "required": ["session_id", "items_practiced", "accuracy", "next_session_focus"],
    "additionalProperties": false
  }
}
```

Server computes `accuracy` from `ReviewLog` for the session and **overrides** the model's number; the model's prose is stored as the human-readable debrief.

### 4.4 Validation per language

**Korean — mature pipeline, reuse `05-tech-and-ai.md`.**

```
LLM JSON → Pydantic → Hangul block check (U+AC00–U+D7A3) → Kiwi morph/POS
→ deterministic particle/ending/register/spacing rules → krdict lemma+level
→ frequency band → dedupe → (new pattern? native review) → publish
```

- **Kiwi (`kiwipiepy`)** is the workhorse: Sejong tags, fast, pip-installable, ~87% web / ~94% written morphological accuracy (per `05`).
- **krdict** gives lemma, POS, pronunciation, level, examples; free key, 50k calls/day, CC BY-SA 2.0 KR.
- Deterministic checks catch the errors models actually make: 은/는 vs 이/가 by batchim and information structure, 을/를, 와/과, 으로/로, irregular stems, `습니다` vs `아/어요` vs `다`, honorific agreement, native vs Sino-Korean numerals, spacing.
- **Never** let the model produce romanization; compute it by rule (`g2pk`/`g2pkk` + Revised Romanization tables).

**Amharic — thinner, be honest.** There is no krdict equivalent. Use:

- **HornMorpho 5.3.6** (GPL-3.0) for morphological analysis/generation: lemma, root, POS, segmentation, features; supports Amharic, Tigrinya, Oromo, Tigre. Rule-based FST, no context-sensitive POS.
- **A curated 1,000–2,000-item lexicon** authored/validated by a native speaker for the first curriculum. This is the real moat; do not generate Amharic vocabulary freely.
- **Normalization** for orthographic variants (ሀ/ሐ/ኀ, ሰ/ሠ, አ/ዐ), Ge'ez numerals, punctuation.
- **Gemination and ejectives are the hard part.** HornMorpho can mark gemination in analysis, but a text-only LLM will omit it; TTS will then mispronounce. For generated Amharic, require a `gemination` field or restrict to phrases from the curated set.
- **No reliable grammar checker.** Gate new patterns on native review; ship only reviewed templates for the first 6 months.

### 4.5 Error taxonomy and the teaching loop

Tag every correction with one of: `particle`, `verb_ending`, `honorific`, `register`, `word_order`, `vocabulary`, `spacing`, `pronunciation_segment`, `pronunciation_prosody`, `gemination`, `ejective`.

```
teach  →  drill  →  check  →  schedule
  │         │          │          │
  │         │          │          └─ FSRS card per (item, skill); due in 10 min,
  │         │          │             then 1 d / 3 d / 7 d per rating
  │         │          └─ grade_attempt: transcript + latency + error tags
  │         └─ create_drill: 3–8 items, target IDs from get_due_items
  └─ lookup_dictionary / add_term_to_library, gated by level
```

**Guardrails against hallucinated vocabulary**

1. **Whitelist, not blacklist.** `create_drill` only accepts `source_item_id`s from the DB. New words require `lookup_dictionary` + `add_term_to_library`, which validates and persists.
2. **Server-side sentence validation** before TTS. Reject on any failed check; ask the model once to repair with the validator's error message, then fall back to a curated template.
3. **Level gate** on `Item.level` and grammar prerequisites. A2 learners do not get `-더라` because the model thinks it is colorful.
4. **Native-review queue** for any new grammar pattern, idiom, or Amharic sentence type. Nothing ships to learners unreviewed.
5. **Frozen adversarial suite**: particles, honorifics, counters, spacing, romanization, gemination, ejectives. Run on every prompt/model change.
6. **Trace every spoken sentence** to a `drill_item_id`. If it cannot be traced, it should not be spoken.

### 4.6 Data-model deltas (no code changes here)

A language-neutral refactor is already in progress in the working tree (`app/models_language.py`: `Language`, `Script`, `ItemForm`, `ItemGloss`, `DictionaryEntry`, `DictionarySense`, `TermCard`, `Course`/`Deck`). **Map the teacher onto that schema; do not add a second `Item.language` column on top of it.** If that refactor has not landed when you build, the minimal stopgap is `Item.language` (`ko`|`am`) + a `(language, surface, gloss, item_type)` unique constraint instead of today's `(korean, english, item_type)`.

Still needed for the teacher, on either schema:

- `Drill(id, user_id, session_id, language, goal, level, prompt, created_at)`
- `DrillItem(id, drill_id, idx, kind, target, gloss, answer, source_item_id)`
- `TeacherSession(id, public_id, user_id, lang, status, started_at, ended_at, max_minutes, transcript_json, summary_json)`
- `ToolCallLog(id, session_id, call_id unique, name, args_json, result_json, latency_ms, created_at)` — idempotency + debugging.
- Reuse `ReviewCard`, `ReviewLog`, `SpeechAttempt`, `Event` as-is. FSRS stays keyed by `(user_id, item_id, skill)` and must not be fragmented per language.

---

## 5. Pronunciation assessment

### 5.1 Providers

| Provider | Korean | Amharic | Granularity | Prosody | Price | Honest caveat |
|---|---|---|---|---|---|---|
| **Azure Pronunciation Assessment** | ✅ `ko-KR` | ❌ | phoneme, word, full text; **syllable en-US only** | **prosody en-US only** | $1.00/audio hr (S1) + prosody add-on (~$0.30/hr per `05`) | Best breadth/price for Korean; phoneme names only en-US/zh-CN; no Amharic. |
| **SpeechSuper** | ✅ | ❌ | phoneme, word, sentence, paragraph (scripted) | fluency, rhythm, completeness | $0.004/word · $0.006/sentence · $0.008/paragraph; **$20/mo minimum**, quarterly invoice | Korean phoneme demo exists; semi/unscripted only English/Mandarin. |
| **ELSA API** | ❌ English only | ❌ | word/phoneme, stress, intonation, fluency | ✅ English | $0.008–0.025 per 15 s | No `language` parameter; ARPAbet only. Not usable. |
| **SoapBox / Read Aloud** | ❌ | ❌ | English phoneme/word | English | not public | English/children only; SoapBox acquired, no self-serve. |
| **Google** | STT only | STT only | none | none | STT $0.016/min | No pronunciation score API; confidence ≠ pronunciation. |
| **Speechace** | ❌ | ❌ | en/fr/es | ✅ | $40–125/mo | No Korean. |
| **TonePerfect** | ✅ `ko-KR` | ❌ | phoneme expected-vs-heard | limited | $10/2,500 credits | Niche; verify Korean reference model. |
| **Amharic** | — | **none** | — | — | — | No commercial scorer exists. |

### 5.2 Korean: what to ship

- **Scripted drills** (read a known sentence): Azure PA phoneme + word + fluency is the best value. At 5 s/clip, 300 clips/month ≈ **$0.42**.
- **Minimal pairs** (불/뿔/풀, 달/딸/탈): Azure phoneme scores on the target syllable; require the *contrast*, not a 0–100 "nativeness" score.
- **Prosody:** Azure cannot do Korean prosody. Compute in-house: pYIN F0, syllable-duration ratios, speech rate, pause count; DTW against a native reference. Report bands ("phrase break too early"), never a fake number.
- **Rhythm:** SpeechSuper if Korean rhythm feedback is a paid differentiator; $0.006/sentence × 300 = $1.80/month. Keep it as a second scorer, not the primary.
- **ASR-diff is not pronunciation.** ASR silently repairs learner errors (documented in `05`); use it for comprehensibility and word-level misses, never as the pronunciation score.

### 5.3 Amharic: the fallback, stated plainly

Nothing commercial scores Amharic pronunciation. Options, in order of effort:

1. **ASR-diff + normalization (ship first, 2–3 days).** Transcribe with Azure `am-ET`, Gladia or Gemini; normalize orthographic variants; align to the target with edit distance. Report **word-level "clear / try again"**, not phonemes. This catches missing/extra words and gross vowel errors; it cannot hear ejectives or gemination.
2. **Forced alignment + prosody (1–2 weeks).** MFA 3.0 has no documented Amharic acoustic model (verify; treat as unavailable). Fallback: use a multilingual model (XLS-R/wav2vec2) for frame posteriors, or a lightweight energy/F0 segmentation, then compare **duration ratios, F0 contour shape, and pause placement** to a native reference via DTW.
3. **GOP-lite (1–2 months, if volume justifies).** Fine-tune XLS-R on Amharic read speech (FLEURS, Common Voice, Horn-ASR) and compute phone posterior ratios for the 7 vowels + ejective/plain/geminate contrasts. Needs L2-Amharic labelled data to calibrate; without it, scores are not trustworthy.
4. **Human review** for the first cohort: 2 native raters on 100 clips to calibrate any automatic signal.

**Say this in the UI:** "Amharic pronunciation feedback is experimental; we score words and rhythm, not individual sounds." That is more trustworthy than a fake phoneme score.

### 5.4 Scoring rubric advice

- Score **intelligibility first**, then targeted contrasts, then fluency. Do not average into one "pronunciation %".
- Use 3 bands (`clear` / `almost` / `try again`) with the **one sound to fix** and a replay.
- Calibrate thresholds on L2 learners, not natives; a native reference will make beginners feel incompetent.
- Show what the ASR heard; offer retry / type / skip; never block progress on a score.
- Keep raw audio ≤72 h, derived scores only with consent (matches `05` §10).

---

## 6. TTS quality and control

### 6.1 Korean

Independent blind listening (Speko, Aug 2026) and TTFB (US-East):

| Model | Naturalness Elo | TTFB | Notes |
|---|---|---|---|
| **Gemini 3.1 Flash TTS** | **1917** (best) | 531 ms p50 / 780 ms p95 | Best naturalness; slow for live turns; token-billed. |
| **Cartesia Sonic 3.5** (3.6 current, untested by Speko) | 1859 | **164 / 267 ms** | Best latency/quality trade; Korean prosody improved Jan 2026. |
| **Inworld TTS-2** | 1722 | **85 / 93 ms** | Fastest; less battle-tested for Korean curriculum. |
| **ElevenLabs v3 Conversational** | 1628 | 206 / 242 ms | Great control; Korean pronunciation errors reported (particles, `~였다`). |
| **OpenAI gpt-4o-mini-tts** | 1498 | 433 / 614 ms | Voices optimized for English; **deprecated, shutdown 6 Jan 2027**. |
| **Azure Neural** | 1438 | 1–3 s (batch); streaming | 16 Korean voice IDs, 3 with SSML styles; best control/price. |

Kiku-specific: for **pre-generated curriculum**, use Gemini 3.1 Flash TTS or Azure (whichever A/B wins on your 50-sentence set) and cache Opus. For **live drill prompts**, native realtime audio (Gemini/OpenAI) is already the teacher's voice; don't add a second TTS hop. If you cascade, use Cartesia Sonic 3.6 or ElevenLabs Flash/v4 Turbo.

Korean pitfalls to test: liaison (연음), ㅎ aspiration, nasalization, tensification, `값`, numbers + counters, English loanwords, hanja readings, and **spacing/punctuation** (a comma changes prosody). Pre-pass G2P (`g2pk`/`g2pkk`) or use Azure custom lexicon / Google IPA override.

### 6.2 Amharic

| Option | Quality evidence | Latency | Price | Streaming | Verdict |
|---|---|---|---|---|---|
| **Azure `am-ET-AmehaNeural` / `MekdesNeural`** | Blind MOS 3.49 composite; 11.16% WER (ASR judge) | **1.05 s** | $15/1M chars | ✅ | **Default.** Reliable, cheap, fast enough for pre-gen. |
| **Gemini TTS `am-ET` (Preview)** | 3.84 composite; 11.02% WER; best naturalness of mainstream | **8.94 s** | token-billed | ✅ PCM | Best sound, too slow for live; good for pre-gen if you can wait. |
| **ElevenLabs v4 / v4 Turbo** | Claims `am`; **no independent Amharic eval**; v3 scored 111% CER / 148% WER (catastrophic) | ~100 ms model | $80 / $40 per 1M | ✅ | **Do not ship without a native A/B.** v3 failure is a warning. |
| **Addis Voice 2** | Vendor-run blind test: **4.25 composite**, 13.87% WER, best listening scores | 5.4 s | commercial, quote | ✅ | Best Amharic-specific quality; vendor benchmark, verify independently; slow. |
| **Meta MMS `mms-tts-amh`** | 3.03 composite; 7.86% CER; needs `uroman` Latin transliteration | ~7 s, batch | free, **CC-BY-NC 4.0** | ❌ | Prototype only; non-commercial license. |
| **AmhTTS (SpeechT5)** | Human MOS 3.71 naturalness / 4.02 intelligibility; native Ethiopic script | batch | open weights | ❌ | Good research baseline; single female speaker, weak numerals/gemination. |

**Amharic TTS is the weakest link.** Budget for a native reviewer to listen to every new drill template; do not let the LLM invent sentences and send them straight to TTS.

### 6.3 Price per 1M characters (list, Nov 2026)

| Provider / model | $/1M chars | Korean | Amharic | Streaming |
|---|---|---|---|---|
| Azure Neural | **$15** | ✅ | ✅ | ✅ |
| Azure Neural HD | $22 | ✅ | ⚠️ (HD not for `am-ET`) | ✅ |
| Google Chirp 3: HD | $30 | ✅ | ❌ (Gemini TTS only) | ✅ |
| Gemini 3.1 Flash TTS | token-billed (est. $10–25) **[U]** | ✅ | ✅ Preview | ✅ |
| Cartesia Sonic 3.6 | $38–65 | ✅ | ❌ | ✅ |
| ElevenLabs Flash/v4 Turbo | $40 | ✅ | ✅ (v4) | ✅ |
| ElevenLabs v4 / Multilingual v2 | $80 | ✅ | ✅ (v4) | ✅ |
| OpenAI gpt-4o-mini-tts | ~$15 equivalent | ✅ | ❌ | ✅ (deprecated) |
| Typecast | ~$70–90 | ✅ (specialist) | ❌ | ✅ |
| Meta MMS | free (CC-BY-NC) | — (not evaluated) | ✅ | ❌ |
| Addis Voice 2 | quote | ❌ | ✅ | ✅ |

**Caching math.** 5,000 items × 40 chars = 200k chars. At Azure $15/1M = **$3 one-time**; at ElevenLabs v4 $80/1M = **$16**. Cache key `sha256(normalized_text|voice|model|speed|format)`, immutable, serve Opus from R2/S3, normalise to −16 LUFS. Dynamic session speech is the only recurring TTS cost, and native realtime audio eliminates it.

---

## 7. Cost model

### 7.1 Assumptions

- **Session:** 12 minutes connected, 40 turns, 4.2 min learner speech, 4.2 min teacher speech, 3.6 min silence.
- **Voice adoption:** 35% of MAU use voice; the rest are text-only.
- **Usage:** 8 voice sessions/month (96 min) for a voice-active learner; 200 text-teacher turns/month for everyone.
- **Fixed per voice learner:** pronunciation $0.40, dynamic non-session TTS $0.20, storage/egress $0.10.
- **Infra:** $250/mo at 1k MAU, $900/mo at 10k (single VPS + Postgres + Redis + object storage + observability).
- **Excluded:** Stripe (~3% + $0.30), CAC, content/native review, taxes.
- Prices are list; volume/commitment discounts are upside.

### 7.2 Session math (the part vendor calculators hide)

Every token-billed realtime API **re-sends the conversation history each turn**. For a 12-minute, 40-turn session:

| Stack | STT | LLM | TTS | Transport/host | **$/session** | **$/conn-min** |
|---|---|---|---|---|---|---|
| **Cascaded (Deepgram + gpt-4.1-mini + Cartesia + LiveKit Cloud)** | $0.040 | $0.013 | $0.160 | $0.126 | **$0.34** | **$0.028** |
| Cascaded, self-hosted worker | $0.040 | $0.013 | $0.160 | $0.006 | **$0.22** | **$0.018** |
| **OpenAI `gpt-realtime-2.1-mini`** | incl. | incl. | incl. | — | **$0.62** | **$0.052** |
| **Gemini 3.8 Live** (compression 4k/1k) | incl. | incl. | incl. | — | **$0.55–0.85** | **$0.046–0.071** |
| **Azure Voice Live Standard** (`gpt-realtime-2.1-mini` + Azure speech) | incl. | incl. | incl. | — | **$0.72–0.96** | **$0.060–0.080** |
| **Deepgram Voice Agent Standard** | incl. | incl. | incl. | — | **$0.90** | **$0.075** |
| **ElevenLabs Agents** | incl. | +$0.03 | incl. | — | **$0.99** | **$0.083** |
| **OpenAI `gpt-realtime-2.1`** | incl. | incl. | incl. | — | **$1.97** | **$0.164** |

Token math behind the two realtime rows (learner 4.2 min, teacher 4.2 min):

- **OpenAI:** audio in 10 tok/s → 2,520 learner tokens; cumulative over 40 turns ≈ 51,700 → × $10/1M = $0.517. Audio out 20 tok/s → 5,040 → × $20/1M = $0.101. **$0.62.** Full model: ×$32/$64 = **$1.97**. Prefix caching ($0.30/1M cached audio) could cut input ~30×, but do not budget on it.
- **Gemini:** 25 tok/s both ways → 12,600 total audio tokens; cumulative over 40 turns ≈ 258,000 input → × $3/1M = $0.775; output 6,300 → × $12/1M = $0.076. **$0.85.** A 4k trigger / 1k target bounds per-turn input at ~4k, giving 40 × 4k = 160k input → $0.48 + $0.076 = **~$0.56**. (An 8k trigger barely binds and saves little.)

A naive "rate card × minutes" would quote OpenAI mini at $0.023/min and Gemini at $0.0225/min. Both are ~2–3× too low for a real 12-minute lesson. **Model your own turn count.**

**Gemini-specific caveat:** 3.8 Live's proactive audio is reported as always-on, and Google bills input for the whole time the session is listening. If that includes silence, add ~40% to the input line (18,000 vs 12,600 audio tokens). VAD-gated mic helps only if the server stops billing when no frames arrive — **measure this in the spike** with `response.done` usage fields before trusting the $0.56 figure.

### 7.3 Per active voice learner per month (8 sessions, 96 min)

| Stack | Realtime (8 × session) | + fixed extras | **Total / voice learner** |
|---|---|---|---|
| Cascaded self-host | $1.76 | $0.70 | **$2.46** |
| Cascaded LiveKit Cloud | $2.72 | $0.70 | **$3.42** |
| OpenAI mini | $4.96 | $0.70 | **$5.66** |
| Gemini Live (mid estimate) | $6.40 | $0.70 | **$7.10** |
| Azure Voice Live Std (mid) | $6.72 | $0.70 | **$7.42** |
| Deepgram Agent | $7.20 | $0.70 | **$7.90** |
| ElevenLabs Agents | $7.92 | $0.70 | **$8.62** |
| OpenAI full | $15.76 | $0.70 | **$16.46** |

Text-only learner (phase 1): **$0.12–0.25/month** at 200 turns with `gpt-4.1-mini` + strict schema + caching.

### 7.4 Per MAU at 1k / 10k (35% voice adoption)

| Stack | 1k MAU total | 1k $/MAU | 10k MAU total | 10k $/MAU | Gross margin @ $14.99 (10k) |
|---|---|---|---|---|---|
| **Cascaded self-host** | **$1,241** | **$1.24** | **$10,810** | **$1.08** | **92.8%** |
| Cascaded + LiveKit Cloud | $1,577 | $1.58 | $14,170 | $1.42 | 90.5% |
| **OpenAI mini** | **$2,361** | **$2.36** | **$22,010** | **$2.20** | **85.3%** |
| **Gemini Live** | **$2,865** | **$2.87** | **$27,050** | **$2.71** | **82.0%** |
| Azure Voice Live Std | $2,977 | $2.98 | $28,170 | $2.82 | 81.2% |
| Deepgram Agent | $3,145 | $3.15 | $29,850 | $2.98 | 80.1% |
| ElevenLabs Agents | $3,397 | $3.40 | $32,370 | $3.24 | 78.4% |
| OpenAI full | $6,141 | $6.14 | $59,810 | $5.98 | 60.1% |

Math at 1k: 350 voice learners × per-learner total + 650 text learners × $0.20 + $250 infra. Example, OpenAI mini: 350 × $5.66 = $1,981 + $130 + $250 = **$2,361**. At 10k: 3,500 × $5.66 = $19,810 + $1,300 + $900 = **$22,010**. At 10k, infra falls to $0.09/MAU but model cost dominates.

### 7.5 Cost levers that actually move the number

1. **Session length cap.** 12 min, not 30. Cost scales ~quadratically with turns for history-rebilling APIs.
2. **Model tiering.** Realtime mini for drills, full model only for free conversation (weekly, paid tier).
3. **Context compression** on Gemini; `max_response_output_tokens` on OpenAI; "2 sentences" prompt rule.
4. **VAD-gated mic.** Do not stream silence to a proactive-audio model; silence is billed.
5. **Pre-synthesized common phrases** and cached curriculum audio.
6. **Text-first fallback.** When a learner is silent or the drill is recognition-only, switch to text mode at ~1/10 the cost.
7. **Kill switch + per-user cap.** One runaway session should not cost $20.

---

## 8. Recommendation

### 8.1 Build this now

| Layer | Choice | Why |
|---|---|---|
| **Realtime brain (primary)** | **Gemini 3.8 Live**, browser WebSocket, config-locked ephemeral token | Only realtime speech-to-speech with **both `ko` and `am`**, async tools, 30-min token, $3/$12 audio. |
| **Realtime brain (A/B / fallback)** | **`gpt-realtime-2.1-mini`** | Better Korean track record, server VAD is fast (1.0 s), 60-min sessions; use if Gemini Korean naturalness or turn-taking loses your eval. |
| **Orchestration (MVP)** | **No framework.** Direct WS + 6 Flask tool endpoints + client-side VAD | Lowest latency, least infra, solo-dev operable. |
| **Orchestration (scale)** | **LiveKit Cloud + agent worker**, or **Pipecat** self-hosted | WebRTC, mobile, observability, provider swappability. |
| **Text teacher** | `gpt-4.1-mini` (not nano) with strict `json_schema` | Nano is cheap but tool-call reliability is the product; upgrade only after eval. |
| **ASR (cascaded/Amharic mode)** | Azure `am-ET` / `ko-KR`; Deepgram Nova-3 or Gladia Solaria-1 as second | Azure has the longest Amharic track record; Gladia/Deepgram are cheaper per minute. |
| **TTS (pre-gen)** | Gemini 3.1 Flash TTS for Korean; **Azure `am-ET`** for Amharic | Best Korean naturalness; Amharic reliability/latency/price. |
| **TTS (live, cascaded)** | Cartesia Sonic 3.6 (Korean) / Azure (Amharic) | 164 ms Korean TTFB; no Amharic in Cartesia. |
| **Pronunciation** | **Azure PA `ko-KR`** + in-house F0/duration; SpeechSuper second scorer | Only production-grade Korean phoneme API with broad locale support; prosody must be built. |
| **Amharic pronunciation** | ASR-diff + duration/F0; label "experimental" | No vendor exists; do not fake phoneme scores. |
| **Validation** | Kiwi + krdict + rules (Korean); HornMorpho + curated lexicon + native review (Amharic) | The moat is the validator, not the prompt. |
| **Scheduling** | Existing `py-fsrs` / `ReviewCard`; one card per (item, skill) | Already built; drill writes must reuse it. |

**What not to build now:** a WebSocket relay, a LiveKit cluster, a custom TTS, a pronunciation model, a separate vector DB, or an Amharic grammar checker. Each is a 2–8 week distraction from the loop that matters.

### 8.2 Three-phase rollout

**Phase 1 — text-only teacher (2–3 weeks).**
Ship a chat teacher with the six tools, no audio. It proves `get_due_items → create_drill → grade_attempt → add_term_to_library` and the validator. Metrics: drill validity ≥95%, tool-call success ≥99%, session completion ≥60%. Cost: ~$0.20/MAU.

**Phase 2 — push-to-talk (4–6 weeks).**
Browser records a turn (MediaRecorder or AudioWorklet, 16 kHz PCM), sends to the realtime model or a batch STT → LLM → TTS path. Button release is the endpoint. Add Silero VAD, replay, transcript display, "type instead". Metrics: p50 ≤900 ms, p95 ≤1.6 s, ASR false-negative <3%, 5-minute session completion ≥50%. Cost: ~$2.50–3.50/MAU.

**Phase 3 — full duplex (6–10 weeks).**
Continuous mic, barge-in, async tool calls, session resumption, per-turn latency telemetry, mobile WebRTC (LiveKit if needed). Metrics: interruption handling ≥95%, p50 ≤1.1 s, cost ≤$4/MAU, no cost blowups >$0.30/session. Only then add Amharic voice; keep Amharic text-only longer if ASR/TTS quality fails the native review.

### 8.3 Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Gemini Korean/Amharic quality is worse than the language list implies** | Medium | High | 100-clip L2 eval before commit; keep OpenAI mini adapter; Amharic text-first. |
| **Amharic TTS/ASR/PA gaps** | High | High | Azure default, Gemini/Addis fallback, native reviewer, "experimental" label, no pronunciation score. |
| **Cost blowup from long sessions / history re-billing** | High | High | 12-min cap, context compression, VAD gating, per-user daily minutes, kill switch, alert at $0.30/session. |
| **Vendor lock-in** | Medium | Medium | Provider-neutral tool schemas + event log; one adapter per provider; store transcripts in your DB, not theirs. |
| **Ephemeral token abuse** | Medium | High | Auth-only minting, one concurrent session, config-locked token, per-user quota, anomaly alerts. |
| **Hallucinated Korean/Amharic** | High | High | Whitelist item IDs, validate before TTS, native review, adversarial suite, rollback. |
| **Voice is personal data (GDPR/PIPA/COPPA)** | Medium | High | No raw audio by default; consent for transcripts; 24–72 h retention; age gate; DPAs. |
| **Realtime API deprecations** | High | Medium | Pin snapshots; abstract model IDs; `gpt-realtime` and `tts-1` already have 2027 shutdown dates. |
| **Latency regressions after model updates** | Medium | Medium | Per-turn telemetry + weekly synthetic session; alert on p95. |

### 8.4 Two-day spike (do this before committing)

**Day 1 — measure, don't build.**
- Mint a Gemini ephemeral token from a throwaway Flask route; connect a plain HTML page; 30 scripted Korean turns.
- Instrument `speech_end → first audio` per turn. Run server VAD and Gemini's VAD; record p50/p95.
- Declare 4 tools (no DB): `get_due_items` returns fixed JSON, `create_drill` echoes, `grade_attempt` echoes, `add_term_to_library` echoes.
- Repeat the same 10 Korean prompts on `gpt-realtime-2.1-mini`; blind-listen with one native speaker.

**Day 2 — wire the loop.**
- Replace `create_drill` with a real SQLAlchemy transaction: `Drill` + `DrillItem` + `ReviewCard` (FSRS due +10 min). Render the drill card in the UI.
- Add barge-in: speak over the teacher, confirm audio stops and the tool call cancels.
- Run 5 learners (3 beginner, 2 intermediate) for 10 minutes each; log tool latency and drill validity.
- Write a one-page decision memo: primary provider, p50/p95, 3 worst transcripts, 3 worst drills, native-review notes.

**Go/no-go:** p50 ≤900 ms PTT, tool write ≤150 ms, drill validity ≥90%, zero untraceable spoken sentences, native reviewer accepts ≥85% of Korean items. If Gemini fails Korean, ship OpenAI mini and keep Gemini for Amharic only.

### 8.5 What would change this recommendation

- Gemini's Korean naturalness or turn-end loses a blind A/B to OpenAI mini by >15%.
- Gemini Amharic ASR produces unusable transcripts on 50 native clips (likely if speakers code-switch).
- OpenAI ships Amharic in Realtime at a comparable price.
- Azure Voice Live adds Amharic to its multilingual realtime model and matches Gemini's tool ergonomics.
- A cascaded pipeline with Cartesia + Deepgram beats native speech-to-speech on your Korean eval at half the cost (possible; re-test quarterly).

---

## 9. Sources

All accessed **23 November 2026** unless noted. [M] = independent measurement, [D] = vendor documentation, [V] = vendor claim, [U] = unverified.

**OpenAI**
1. [D] API pricing (realtime/audio tables) — https://developers.openai.com/api/docs/pricing
2. [D] GPT-Realtime-2.1 model card — https://developers.openai.com/api/docs/models/gpt-realtime-2.1
3. [D] Realtime conversations, 60-min session cap — https://developers.openai.com/api/docs/guides/realtime-conversations
4. [D] Create realtime session / ephemeral `client_secret` (1-min expiry) — https://developers.openai.com/api/reference/resources/realtime/subresources/sessions/methods/create
5. [D] Text-to-speech deprecations (`tts-1`, `gpt-4o-mini-tts` shutdown 6 Jan 2027; 57 languages) — https://developers.openai.com/api/docs/guides/text-to-speech
6. [M] Apptycoons, 180-turn Realtime latency benchmark, 29 Oct 2026 — https://apptycoons.com/research/voice-agent-latency-benchmark
7. [M] virevolai long-session benchmark (Gemini 1,064 ms, OpenAI 1,253 ms; 17.3× Gemini cost growth) — https://github.com/virevolai/voice-benchmarks

**Google**
8. [D] Gemini Developer API pricing (3.8 Live $3/$12 per 1M audio) — https://ai.google.dev/gemini-api/docs/pricing
9. [D] Live API capabilities, 99 languages incl. Amharic, session limits — https://aistudio.google.com/docs/live-api/capabilities
10. [D] Session management, compression/resumption — https://aistudio.google.com/docs/live-api/session-management
11. [D] Ephemeral tokens, config locking — https://aistudio.google.com/docs/live-api/ephemeral-tokens
12. [D] Tool use, async function calling, scheduling — https://aistudio.google.com/docs/live-api/tools
13. [D] Gemini-TTS languages (`am-ET` Preview, `ko-KR` GA) — https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
14. [D] Cloud STT v2 languages (`am-ET` chirp_3) — https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages

**ElevenLabs**
15. [D] API pricing (v4 $0.08/1k, v4 Turbo $0.04/1k, Flash $0.04/1k) — https://elevenlabs.io/pricing/api
16. [D] ElevenAgents pricing ($0.08/min, 600 s default, max 7,200 s) — https://elevenlabs.io/pricing/agents
17. [D] Models overview and language lists — https://elevenlabs.io/docs/overview/models
18. [D] Eleven v4 languages incl. Amharic — https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4
19. [D] Scribe v3/v2 language WER tiers (Amharic 25–50%) — https://elevenlabs.io/docs/overview/capabilities/speech-to-text
20. [D] Conversation flow / max duration — https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow

**Deepgram / AssemblyAI / Cartesia**
21. [D] Deepgram pricing (Voice Agent $0.075/min; Nova-3 $0.0048) — https://deepgram.com/pricing
22. [D] Deepgram models & languages (Amharic added 16 Nov 2026; Korean improved Aug 2026) — https://developers.deepgram.com/docs/models-languages-overview/
23. [D] Deepgram changelog, 36 new Nova-3 languages incl. Amharic — https://developers.deepgram.com/changelog/2026/11/16
24. [D] Deepgram Voice Agent 2-hour session cap — https://developers.deepgram.com/docs/voice-agent-feature-overview
25. [D] AssemblyAI pricing (STT-3.7-Realtime-Agent $0.45/hr) — https://www.assemblyai.com/pricing
26. [D] AssemblyAI supported languages / Amharic >50% WER — https://www.assemblyai.com/docs/pre-recorded-audio/supported-languages
27. [D] Cartesia pricing (Sonic $38–65/1M; Ink 3 credits/s) — https://www.cartesia.ai/pricing
28. [D] Cartesia pricing docs / changelog (Ink-2 5 languages; Sonic 3.6 44) — https://docs.cartesia.ai/pricing , https://docs.cartesia.ai/changelog/2026

**Azure**
29. [D] Azure Speech pricing ($1/audio hr; Neural TTS $15/1M) — https://azure.microsoft.com/en-us/pricing/details/speech/
30. [D] Voice Live API overview and model/pricing tiers — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live
31. [D] Voice Live language support (Korean; Amharic not in multilingual realtime model) — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-language-support
32. [D] Pronunciation Assessment (33 locales, prosody en-US only) — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment
33. [D] Azure language/voice support (`am-ET` STT + TTS, `ko-KR`) — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support

**Others**
34. [D/U] Hume changelog, EVI/TTS sunset 13 Nov 2026 — https://dev.hume.ai/changelog (summarised at https://techpilot.ai/tools/hume-ai/, 10 Nov 2026)
35. [D] LiveKit pricing ($0.01/agent-min; WebRTC $0.0005/min) — https://livekit.com/pricing
36. [D] Pipecat Cloud overview/pricing ($0.01/agent-min) — https://docs.pipecat.ai/pipecat-cloud/introduction
37. [D] Soniox pricing ($0.12/hr realtime) and languages (no Amharic) — https://soniox.com/pricing , https://docs.soniox.com/stt/concepts/supported-languages
38. [D] Speechmatics pricing (Linden 1 $0.30/hr realtime) and languages (Korean yes, no Amharic) — https://www.speechmatics.com/pricing , https://docs.speechmatics.com/speech-to-text/languages
39. [D] Gladia pricing (€0.68/hr realtime) and languages (Amharic + Korean on Solaria-1) — https://www.gladia.io/pricing , https://docs.gladia.io/chapters/language/supported-languages

**Pronunciation**
40. [D] SpeechSuper pricing ($0.004/$0.006/$0.008; $20 min) and Korean support — https://www.speechsuper.com/pricing.html , https://docs.speechsuper.com/
41. [D] ELSA API (English only; $0.008–0.025/15 s) — https://elsaspeak.com/en/elsa-api/
42. [M] TonePerfect comparison of pronunciation APIs, 30 Oct 2026 — https://api.toneperfect.app/best-pronunciation-assessment-api/

**TTS quality**
43. [M] Speko Korean TTS benchmark, Aug 2026 (Gemini 1917, Cartesia 1859, ElevenLabs 1628) — https://speko.com/benchmarks/tts-multilingual/ko
44. [M, vendor-run] Addis AI Amharic TTS benchmark, 12 Aug 2026 — https://addisassistant.com/benchmarks/addis-voice-2-amharic
45. [D] Meta MMS Amharic TTS (CC-BY-NC 4.0) — https://huggingface.co/facebook/mms-tts-amh
46. [M] AmhTTS, WiNLP 2026 (MOS 3.71/4.02) — https://aclanthology.org/2026.winlp-main.7.pdf

**Amharic NLP**
47. [D] HornMorpho 5.3.6 (GPL-3.0; Amharic/Tigrinya/Oromo/Tigre) — https://github.com/hltdi/HornMorpho
48. [D] EthioNLP Ethiopian Language Survey — https://github.com/EthioNLP/Ethiopian-Language-Survey

**Korean NLP**
49. [D] krdict API (free key, 50k/day, CC BY-SA 2.0 KR) — https://krdict.korean.go.kr/api/search
50. [D] Kiwi (`kiwipiepy`) — https://github.com/bab2min/kiwipiepy

---

### Appendix A — Provider decision matrix (weighted for Kiku)

Weights: Korean quality 25, Amharic coverage 25, latency 15, cost 15, tool ergonomics 10, ops simplicity 10.

| Provider | KR | AM | Lat | Cost | Tools | Ops | **Score** |
|---|---|---|---|---|---|---|---|
| Gemini 3.8 Live | 8 | **10** | 9 | 7 | **10** | 8 | **8.70** |
| OpenAI Realtime mini | **9** | 2 | 9 | 8 | 8 | 9 | **7.00** |
| Azure Voice Live | 8 | 7 | 7 | 7 | 8 | 7 | **7.35** |
| Deepgram Agent | 8 | 5 | 8 | 6 | 8 | 8 | **6.95** |
| ElevenLabs Agents | 8 | 6 | 7 | 4 | 8 | 9 | **6.85** |
| Cascaded + LiveKit | 9 | 8 | 7 | **9** | 9 | 4 | **7.95** |
| Cascaded + Pipecat | 9 | 8 | 7 | 9 | 9 | 5 | **8.05** |

Gemini wins on the language constraint and tool model; the cascaded pipeline is the cost/quality challenger and the scale answer. OpenAI mini is the Korean insurance policy.

### Appendix B — Migration notes for the current app

- `tts-1` and `gpt-4o-transcribe` are on shutdown paths (6 Jan 2027 and 26 Feb 2027). `tts-1` → `gpt-realtime-2.1-mini` (Realtime API) or Azure/Google TTS; `gpt-4o-transcribe` → `gpt-transcribe`/`gpt-live-transcribe` for batch, or Azure for streaming.
- `gpt-4.1-nano` chat can stay for text drills, but the teacher's tool-calling loop should use `gpt-4.1-mini` until eval proves nano.
- If the `models_language.py` refactor lands, write Amharic through `Language` + `ItemForm`/`ItemGloss` + `DictionaryEntry`/`TermCard`; only if it stalls, add `Item.language` and a language-aware unique constraint before the first Amharic row. Do not do both.
- `SpeechAttempt` already stores transcript + match score + provider/model; extend `provider` values (`azure_pa`, `speechsuper`, `asr_diff`) rather than adding a new table.
- `Event` is the right place for `teacher_turn`, `drill_created`, `tool_error`, `session_cost`; do not create a parallel analytics pipeline.
