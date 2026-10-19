# Technical Architecture & AI Capabilities for an Adaptive Korean Learning App

**Status:** Research brief · October 2026
**Starting point:** Flask 2.0 / SQLAlchemy 1.4 / SQLite prototype with synchronous OpenAI calls and MP3s in `app/static/audio`.

---

## 1. Executive summary

1. **Buy speech, build feedback.** ASR is commodity ($0.003–$0.017/min); phoneme scoring is not. Azure supports Korean phoneme/word scoring, but **syllable aggregation and prosody are en-US only**; SpeechSuper adds Korean rhythm at $0.004–$0.008/request.
2. **ASR accuracy ≠ pronunciation accuracy.** ASR silently repairs learner errors; near-zero WER correlates weakly with human ratings.
3. **TTS is cheap if pre-generated.** Synthesize core curriculum once ($15–$80/1M chars); only dynamic sentences cost per request.
4. **LLMs generate candidates, not truth.** Constrain to DB item IDs, validate with Kiwi + rules + krdict, gate new patterns on native review, and compute romanization by rule.
5. **FSRS for *when*, Elo/BKT for *what*, bandit for *which*.** Deep KT needs data a solo dev won't have; simple models match DKT/SAKT on small datasets (AUC ≈ 0.76–0.77).
6. **Evolve, don't rewrite.** Flask + Postgres + Redis/RQ, FastAPI AI sidecar, PWA first; **$1.80–$7.35 per active learner/month**.

---

## 2. Speech: ASR and pronunciation assessment

| Provider | Korean | Granularity | Prosody / fluency | Price (Oct 2026) | Latency |
|---|---|---|---|---|---|
| **Azure Pronunciation Assessment** | `ko-KR` | phoneme, word, full text; syllable **en-US only** | fluency + completeness; **prosody en-US only** | $1.00/audio hr + $0.30/hr prosody | 0.3–0.8 s |
| **SpeechSuper** | Korean | phoneme, word, sentence, paragraph | fluency, rhythm, completeness | $0.004/word, $0.006/sentence, $0.008/paragraph; $20/mo min | 0.5–1 s |
| **OpenAI `gpt-transcribe`** | yes | text + word timestamps | no | $0.0045/min | 1–3 s |
| **OpenAI `gpt-4o-transcribe` / mini** | yes | text + words | no | ~$0.006 / $0.003/min | 1–3 s |
| **OpenAI `gpt-live-transcribe`** | yes | streaming text | no | $0.017/min | 0.3–0.5 s |
| **Google Chirp 3 (STT v2)** | `ko-KR` | text + words | no scoring | ~$0.016/min | 1–3 s |
| **Deepgram Nova-3 / AssemblyAI Universal-3.5** | both | text + words | no | $0.004–$0.0075/min | ~0.3 s |
| **WhisperKit (on-device)** | yes | text + words | no | free (device) | 0.46 s measured |

`gpt-4o-transcribe` and `whisper-1` are deprecated and leave the API **Feb 26, 2027**; don't build on them.

**Accuracy limits for L2 Korean.** Native Korean WER is ~14% for Whisper-large-v2 on child/read corpora and 5–8% on clean adult benchmarks; L2 speech degrades further. A 2025 study of 190 Korean EFL learners found Whisper Large-v3 and Azure produced **near-zero WER but weak correlation with human comprehensibility/accent ratings** — ASR silently repairs the errors you want to detect. A Korean-fine-tuned XLS-R phone recognizer reached **3.88% PER** on a 40-phone L2 test set, but only with supervised L2 data.

**Three-stage design:**

- **A. Comprehensibility:** `gpt-transcribe` or Azure STT → word diff, latency, pause count.
- **B. Pronunciation:** Azure PA for scripted minimal-pair/sentence drills; SpeechSuper where Korean rhythm/syllable feedback matters. Phoneme scores are *evidence*, not truth.
- **C. Prosody in-house:** pYIN F0, syllable-duration ratios, speech rate, pauses; DTW against a native reference; banded feedback ("phrase break too early"), not a fake 0–100.

Push-to-talk (3–8 s upload, 1.5–3 s score) is right for MVP; full-duplex WebRTC only for live tutoring.

---

## 3. TTS

| Provider | Korean | SSML / control | Speed | $/1M chars |
|---|---|---|---|---|
| **OpenAI `gpt-4o-mini-tts`** | 11 multilingual voices | natural-language `instructions` (tone, pace); no full SSML | prompt-level | ~$15 (token-based; ≈$0.015/min) |
| **OpenAI `tts-1` / `tts-1-hd`** | same | `speed` 0.25–4.0 | native | $15 / $30 |
| **ElevenLabs Flash v2.5 / v4** | Korean | audio tags (v3/v4), no SSML | request-level | $40 / $80 |
| **Azure Neural TTS** | 20+ `ko-KR` voices | full SSML: `prosody`, `break`, `phoneme`, lexicon | 0.5–2.0 | $15 Neural / $22 HD |
| **Google Chirp 3: HD** | `ko-KR` | SSML + IPA/X-SAMPA phoneme override + pace | configurable | $30 (1M/mo free) |
| **Naver Clova Voice Premium** | 100+ Korean voices | limited SSML, emotion/style | yes | ~$0.37–$0.49/1k chars (plans) |
| **Typecast** | Korean character voices | emotion/style presets | yes | ~$0.37–$0.62/1k effective |

**TTS strategy.** Pre-generate every lexeme, example, grammar pattern and dialogue line at publish time; normalize to −16 LUFS; store Opus + MP3 fallback. 3,000 items × ~40 chars ≈ 120k chars → **$2–$10 one-time**. Cache key `sha256(normalized_text|voice|model|speed|style|format)`, immutable, CDN-served.

**Dialogue and speed.** Render lines separately for replay, or use ElevenLabs multi-speaker / Azure two-voice SSML, inserting 250–400 ms silence when concatenating. Generate 1.0× and optionally 0.85×; time-stretch 0.7–1.1× client-side instead of paying for multiple renders.

**Korean pitfalls:** liaison, ㅎ aspiration, nasalization, tensification, loanwords, numbers/counters, hanja readings. Pre-pass G2P (`g2pk`/`g2pkk`) or Azure custom lexicon; native-speaker A/B on new patterns.

---

## 4. LLM-generated Korean: grounding and validation

**Failure modes:** particle allomorphs (은/는, 이/가, 을/를, 와/과, 으로/로), honorific/register mismatch, spacing, translationese, level-inappropriate vocabulary, and **hallucinated romanization** (Revised Romanization needs liaison/assimilation rules models ignore).

**Pipeline:**

```
prompt + retrieved item IDs
 → LLM (strict json_schema, temp 0.2–0.4)
 → Pydantic/JSON Schema validation
 → Hangul & syllable-block validation (U+AC00–U+D7A3)
 → Kiwi morphology + POS checks
 → deterministic grammar rules (particles, endings, register, spacing)
 → krdict lookup (lemma, POS, level, pronunciation)
 → frequency-band check
 → romanization by rule engine (never LLM)
 → dedupe (hash + embedding)
 → native review for new patterns → publish
```

**Morphology.** Use **Kiwi (`kiwipiepy`)**: Sejong tags, ~87% web / ~94% written accuracy, fast, pip-installable, with spacing and sentence splitting. KoNLPy wraps Kkma/Komoran/Okt/Hannanum/MeCab-ko but is slower with JVM dependencies; keep it for comparison. MeCab-ko is fastest but fragile to install.

**Deterministic checks (best effort/return):** particle selection by batchim and irregular stems; conjugation tables for ~200 common stems; register consistency (`습니다` vs `아/어요` vs `다`); honorific agreement; spacing vs Kiwi, flagging only high-confidence diffs; native vs Sino-Korean numerals/counters; romanization by rule engine + override table; profanity/age filter.

**Reference APIs.**

| Source | Gives | Access | License / limits |
|---|---|---|---|
| **krdict (한국어기초사전)** | lemma, POS, pronunciation, level, senses, examples, translations | `krdict.korean.go.kr/api/search` XML/JSON | free key; **50k calls/day**; CC BY-SA 2.0 KR |
| **표준국어대사전** | broader lemmas, etymology, grammar | `stdict.korean.go.kr/api/search.do` | free key; attribution |
| **Naver Dictionary** | learner-friendly definitions | no official API; scraping violates ToS | don't scrape |
| **Papago NMT** | translation | paid Naver Cloud | QA only, not validation |
| **KLI/TOPIK lists** | ~5,000 leveled headwords | published datasets | curriculum spine |
| **`wordfreq`** | Korean corpus frequency | local package | MIT; good for banding |

**Structured output.** OpenAI strict `json_schema` (or Pydantic + `instructor`) with `additionalProperties: false` and required `korean`, `gloss`, `grammar_tags`, `level` (1–6), `distractors` (2–4), `source_item_ids`. Retrieved IDs constrain vocabulary.

**Evaluation harness.** 500–1,000 gold items stratified by TOPIK level and grammar point, rated by 2–3 natives on grammaticality, naturalness, level fit, translation fidelity and romanization. Track Krippendorff's α and gate releases on regression thresholds. Calibrate any LLM judge against ≥300 human labels; keep a frozen adversarial suite (particles, honorifics, translationese, spacing, romanization). The harness is the moat, not the prompts.

---

## 5. Adaptive learning engine

**FSRS (scheduling).** Use **`py-fsrs` 6.3.x** (FSRS-6, 21 params). State per card: stability, difficulty, due, last_review, state, reps, lapses. Defaults: `desired_retention=0.9`, steps 1 m/10 m, max interval 36,500 d, fuzzing on.

- Optimize per user only after ~400–1,000 countable reviews; otherwise global defaults (still better than SM-2). Re-optimize monthly or when reviews double.
- Desired retention 0.85–0.90 for language learners; 0.85 for casual users.
- **One card per (item, skill)**, not per lexeme: recognition, recall, listening, pronunciation, conjugation have independent memory state.
- **Leeches:** 4+ lapses or ≥8 reviews at <50% → intervene, don't drill: simplify (recognition not production), add audio/mnemonic, split components, or suspend.

**Knowledge tracing.**

| Model | Data needed | Strength | Weakness | Use |
|---|---|---|---|---|
| FSRS | per-card reviews | interval prediction | no skill transfer | scheduling |
| BKT | per-skill sequences | interpretable, 4 params | no transfer/forgetting | mastery |
| Elo / 1PL IRT | item responses | cheap, online, cold start | static ability | difficulty, placement |
| DKT / SAKT | 100k+ interactions | skill interactions | cold start, opaque | defer |

Published comparisons put logistic regression at ~0.77 AUC vs DKT/SAKT ~0.76 on 50k students; another large study had both ~0.81. Deep KT is not a free win at solo-dev scale.

**Recommended hybrid:**

1. **Item difficulty:** Elo with decaying K (`32` first 30 responses, then `16`, then `8`), initialized from frequency band, length, phoneme count and grammar complexity; shrink toward the level mean.
2. **Skill mastery:** BKT per grammar point/phoneme (`p_init .3`, `p_transit .1`, `p_slip .1`, `p_guess .25`) plus exponential forgetting (half-life 30–60 d).
3. **Selection:** contextual bandit over candidates filtered by FSRS due, prerequisites, target skill and level. Thompson sampling over Elo/BKT uncertainty or LinUCB; reward = correctness + engagement − over-drill. Guardrails: ~80–85% success, new-item cap, interleave skills, no repeats unless lapsed.
4. **Cold start / display:** 10–15 item adaptive placement (Elo) + self-reported level + content priors, starting at ~70% predicted success; show probability bands ("likely mastered", "shaky"), not precise percentages.

---

## 6. Pronunciation curriculum data

**Inventory.** 19 consonants; 7 monophthongs + 13 diphthongs (21 vowel letters); maximal CGVC; only seven coda sounds surface (/p, t, k, m, n, ŋ, l/). The three-way laryngeal contrast (ㄱ/ㄲ/ㅋ, ㄷ/ㄸ/ㅌ, ㅂ/ㅃ/ㅍ, ㅈ/ㅉ/ㅊ, ㅅ/ㅆ) is the core L2 difficulty, then vowel contrasts and coda neutralization.

**English-L1 priorities:** ㅓ/ㅗ, ㅡ/ㅜ, ㅕ/ㅛ, ㅐ/ㅔ (largely merged in young Seoul speech — teach spelling, not sound), plain/tense/aspirated stops, unreleased codas, nasalization (ㄱ→ㅇ before ㄴ/ㅁ), lateralization (ㄴ→ㄹ), liaison, palatalization. **Minimal pairs:** 불/뿔/풀, 달/딸/탈, 개/깨, 자/짜/차, 벌/뻘, 골/꼴, 거리/고리, 그리/구리, 배/베, 밤/방/반, 살/쌀.

| Corpus | Size | License / access |
|---|---|---|
| **KsponSpeech** (AIHub) | 969 h, ~2,000 speakers; orthographic + phonetic | application; training domestic-only; eval CC BY-NC-ND 4.0 |
| **Zeroth-Korean** | ~100 h read | open |
| **Seoul Corpus** | ~27 h, 40 speakers | research |
| **Common Voice Korean** | crowdsourced | CC0 |
| **AIHub sets** | hundreds of hours | application; **commercial use needs review** |

AIHub corpora are not blanket-commercial; prefer vendor APIs plus consented recordings.

| Method | Gives | Effort | Shippable |
|---|---|---|---|
| Azure PA / SpeechSuper | phoneme/word, fluency/rhythm | 1 day | yes |
| GOP (Kaldi DNN) | phone posterior ratio | 2–4 wk | research |
| SSL posteriors (XLS-R/HuBERT) | phone evidence | 3–6 wk | with fine-tuning |
| DTW on SSL embeddings | coarse acoustic distance | 1 wk | yes |
| Formants (parselmouth) | F1/F2 for vowels | 2–3 d | ㅓ/ㅗ, ㅡ/ㅜ |
| MFA 3.0 | phone boundaries, durations | 3–5 d | batch |
| WhisperX | word timestamps | 1 day | word-level only |

**Forced alignment.** MFA 3.0 with `korean_mfa` acoustic model + dictionary achieves **14.78 ms mean boundary error** on Seoul Corpus, better than WhisperX/MMS for phone boundaries; CPU, 1–2 s/utterance.

**Ship in 90 days:** phoneme scores on 20–30 minimal pairs; word diff + "clear / try again" bands; F0/duration contour comparison; formant scatter for two vowel contrasts. No numeric "native-like" score — that is a trust risk.

---

## 7. Application architecture

| Option | Fit |
|---|---|
| **Flask + Postgres + Redis + RQ** | **90 days** — minimal rewrite, sync-first |
| **FastAPI + Next.js** | phase 2 — async/streaming, two apps to operate |
| **Django + DRF** | admin-heavy, async awkward |

**Recommendation: strangler, not rewrite.** Keep Flask as the web/app server but add auth and tenancy; move to Postgres (Neon/Supabase/RDS), Redis (Upstash) for cache + RQ, audio to S3/R2 with signed URLs, and a **FastAPI `ai-service`** sidecar for streaming ASR, LLM calls and scoring. Shared Postgres. After 90 days choose Next.js or Flask + HTMX — not both.

```
                 ┌──────────────────────────────┐
                 │  PWA · MediaRecorder/WebAudio│
                 │  IndexedDB (Dexie) review Q  │
                 └──────────────┬───────────────┘
                                │ HTTPS / WSS
                 ┌──────────────▼───────────────┐
                 │  API gateway: auth, limits,  │
                 │  flags, cost budgets         │
                 └───┬──────────┬───────────┬───┘
                     │          │           │
          ┌──────────▼──┐  ┌────▼─────┐  ┌──▼────────────┐
          │ Flask web   │  │ FastAPI  │  │ Event ingest  │
          │ content,    │  │ AI svc   │  │ (PostHog +    │
          │ review,     │  │ ASR/TTS/ │  │ append-only)  │
          │ billing     │  │ LLM/PA   │  └──────┬────────┘
          └──────┬──────┘  └────┬─────┘         │
                 │              │               │
       ┌─────────▼──────────────▼───────────────▼──────┐
       │ Postgres 16 + pgvector · Redis (cache/queue)  │
       └───────┬───────────────────────┬───────────────┘
               │                       │
     ┌─────────▼────────┐    ┌─────────▼──────────────┐
     │ RQ workers       │    │ Object storage (R2/S3) │
     │ TTS, batch PA,   │    │ audio, signed URLs,    │
     │ FSRS optimize    │    │ lifecycle rules        │
     └─────────┬────────┘    └────────────────────────┘
               │
  ┌────────────▼─────────────────────────────────────────┐
  │ Vendors: Azure · OpenAI · SpeechSuper · krdict       │
  │ Secrets · cost/latency telemetry                     │
  └──────────────────────────────────────────────────────┘
```

**Mobile.** PWA first: one codebase, no store review, `MediaRecorder`, Dexie + Workbox offline drills. iOS limits background audio/push/storage; move to **Expo** if >30% of WAU are iOS and push/offline drives churn.

**Realtime / offline / events / flags.** Push-to-talk HTTP first, WebSocket for partial transcripts, WebRTC (LiveKit/Pipecat) only for a tutor. Append-only review events with client UUIDv7 queued in IndexedDB and replayed idempotently. One `events` table (`name`, `props jsonb`, timestamps, `session_id`, `schema_version`), batched and mirrored to PostHog. DB-backed percentage flags by user hash; Unleash/Flagsmith later.

---

## 8. Data model outline

- **Content:** `items(id, type, surface, normalized, level, freq_rank, metadata jsonb, content_hash, status)`; `item_relations(parent_id, child_id, relation)` for prereq/contains/contrasts; `senses`, `grammar_points(pattern, level, prerequisites)`, `audio_assets(content_hash, voice, model, storage_key, duration_ms, loudness, license)`.
- **Learning:** `review_cards(user_id, item_id, skill, stability, difficulty, due, state, reps, lapses, leech)`; `review_logs`; immutable `attempts(item_id, skill, modality, response, correct, score, latency_ms, audio_asset_id, model_version)`; `phone_scores(attempt_id, phone, expected, observed, score, start_ms, end_ms)`; `skill_mastery(theta, mastery_prob, alpha, beta)`; `sessions`, `session_items`.
- **Search/ops:** `embeddings(item_id, model, vector(1536))` with HNSW; `consents`; `api_usage(vendor, operation, units, cost_usd)` for unit economics.

`items.type ∈ {lexeme, grammar, sentence, minimal_pair, dialogue_line}`; `skill ∈ {recognize, recall, listen, pronounce, conjugate}`.

---

## 9. Cost model

**Per monthly active learner:** 400 study minutes, 160 speech minutes, 1,200 reviews, 150 LLM calls, 20k dynamic TTS chars.

| Line | Low | High | Basis |
|---|---|---|---|
| ASR + pronunciation | $1.00 | $3.00 | transcript $0.72 + Azure PA $2.67, or SpeechSuper ~$2.40 |
| TTS (dynamic) | $0.30 | $1.60 | 20k chars at $15–$80/1M |
| LLM + embeddings | $0.11 | $1.55 | 150 calls + small embedding spend |
| Storage + egress | $0.10 | $0.40 | 160 MB audio, 30-day lifecycle |
| Infra share | $0.30 | $0.80 | $60–$150/mo ÷ 150–300 users |
| **Total** | **$1.81** | **$7.35** | |

At $14.99/month, gross margin is **51–88%** before Stripe (~3% + $0.30) and CAC. Target <$4 variable cost (~73%). Levers: pre-generate more, batch-score, cache LLM by content hash, Azure commitment tiers ($0.80/hr at 2,000 hr), on-device WhisperKit for free tier.

Early unit economics: CAC $30–$80, monthly churn 8–12%, lifetime 8–12 months, LTV $100–$160, LTV:CAC 1.8–3.5. AI cost is not the constraint; activation and month-2 retention are.

---

## 10. Safety and privacy

- **Voice is personal data.** Under GDPR it is biometric *special category* data only when used to identify someone; don't build speaker ID. Under the **2025 COPPA amendments (effective Apr 22, 2026)**, voiceprints are personal information; a child's audio has only a narrow exception (answer a specific request, no reuse/disclosure, prompt deletion).
- **Minors.** Age gate. Under-13: verifiable parental consent, no ads/social/open-ended chat/voice cloning, strict retention. 13–17: parental notice plus state laws (California AADC).
- **Retention.** Raw audio deleted 24–72 h after scoring by default; derived scores/transcripts only with consent. "Save recording" opt-in and revocable. Account deletion ≤30 days; backups 30–90 days. Publish the table.
- **Korea (PIPA).** Voice may be sensitive; separate consent, cross-border transfer disclosure, domestic representative if thresholds apply.
- **Keys & vendors.** Server-side secrets only, per-environment scope, quarterly rotation; signed short-lived audio URLs; strip metadata; redact transcripts in logs. DPAs, no-training terms, matching residency, documented subprocessors.
- **Product.** Korean output moderation, age-appropriate content, "AI-generated, may contain errors" disclosure, report path.

---

## 11. Build vs buy and the 90-day plan

| Capability | Decision | Why |
|---|---|---|
| ASR | **buy** | commodity |
| Pronunciation scoring | **buy now, build later** | ship in days; GOP-lite at volume |
| TTS | **buy + pre-generate** | caching collapses cost |
| LLM | **buy, wrap heavily** | validation + eval are the moat |
| FSRS / KT | **use `py-fsrs`; build BKT + Elo** | mature algorithm, ~300 LOC glue |
| Auth, billing, infra | **buy / managed** | Clerk or Supabase + Stripe, Neon, Upstash, R2 |
| Content | **license + author** | krdict (CC BY-SA), KLI lists, native review |

**MVP stack:** Flask 3 + Jinja/HTMX + Tailwind/Alpine; FastAPI sidecar with Pydantic v2, `openai`, `azure-cognitiveservices-speech`, `httpx`; Postgres 16 + pgvector, SQLAlchemy 2 + Alembic, Redis + RQ; `kiwipiepy`, `g2pk`/`g2pkk`, `wordfreq`, krdict client; Azure PA + `gpt-transcribe`, SpeechSuper as second scorer; `fsrs`, custom BKT/Elo, Thompson sampling; PWA with Dexie/Workbox/MediaRecorder; Sentry, PostHog, Stripe, R2, GitHub Actions.

| Days | Milestone | Deliverables |
|---|---|---|
| **1–14** | Foundation | Postgres migration, Alembic, auth, user model, event/content schemas, 300-item seed, eval harness |
| **15–30** | Core loop | FSRS, review UI, offline queue, audio pipeline, seed TTS, signed URLs |
| **31–45** | Speech | push-to-talk, Azure PA, phone scores, 20 minimal-pair drills, transcript fallback |
| **46–60** | Content quality | strict-schema generation, Kiwi + rules, krdict lookup, romanization engine, 200-item gold set + native review |
| **61–75** | Adaptive | Elo calibration, BKT mastery, bandit selection, leeches, placement test, cost/latency dashboards |
| **76–90** | Beta | 20–50 users, retention instrumentation, latency tuning, privacy/DPA review, pricing test, runbook |

**Gates:** day-7 retention >25%; median review latency <200 ms; speech feedback <3 s p95; variable cost <$4/MAU; <2% of generated items rejected after calibration.
