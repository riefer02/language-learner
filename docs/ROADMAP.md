# Kiku Execution Roadmap

**Status:** Active · started 19 October 2026
**Source of truth for scope:** [`KIKU_BLUEPRINT.md`](KIKU_BLUEPRINT.md)
**Current focus:** Phase 0 (stabilize) + first Phase 1 vertical slice (review loop)

---

## 1. How we work

- **One vertical slice at a time.** Every change must make a learner journey work end to end, not just add a layer.
- **Small, reversible commits.** No migration without a rollback path. No generated content without validation.
- **Tests before trust.** Any path that writes a file, spends money, schedules a review, or scores speech gets a test.
- **Documentation is part of done.** Update this roadmap and `PROJECT_STATUS.md` when a phase closes.
- **No dark patterns.** No loss-framed streaks, pay-to-repair, or shame copy.

### Workstreams and ownership

| Stream | Owns | Primary files |
|---|---|---|
| **Platform** | App factory, config, auth, rate limits, errors, migrations, deployment | `app/__init__.py`, `config.py`, `app/errors.py`, `app/utils/rate_limit.py`, `migrations/`, `run.py` |
| **AI services** | OpenAI client, translation, conversation generation, validation, retries, TTS | `app/services/`, `app/utils/schemas.py`, `app/utils/retries.py` |
| **Media** | Audio staging, commit/cleanup, orphan audit, object storage adapter | `app/utils/media.py`, `app/utils/audio_merge.py` |
| **Learning** | Content model, FSRS, planner, attempts, mastery, curriculum seed | `app/models.py`, `app/learning/`, `app/models_learning.py` |
| **Experience** | Templates, JS, CSS, accessibility, review UI, onboarding | `app/templates/`, `app/static/` |
| **Quality** | Tests, CI, lint, type checks, content eval harness | `tests/`, `.github/workflows/`, `requirements-dev.txt` |

### Definition of done (all changes)

- [ ] Works on a clean database (`flask db upgrade` from empty).
- [ ] Works without `OPENAI_API_KEY` for boot, migrations, and tests.
- [ ] No new orphan files after a simulated failure.
- [ ] Input and model output validated; rendered with `textContent`/autoescape.
- [ ] Test covering the happy path and at least one failure path.
- [ ] Accessibility check: keyboard, focus, labels, Korean `lang`.
- [ ] Docs/roadmap updated.

---

## 2. Phase 0 — Stabilize (weeks 1–2)

**Goal:** make the prototype safe, truthful, and testable. No new learner features until this closes.

| ID | Task | Stream | Acceptance | Status |
|---|---|---|---|---|
| P0-01 | Rotate exposed OpenAI key; remove live key from working tree | Platform | Old key revoked; `.env` ignored; `.env.example` documents required vars | [ ] user action |
| P0-02 | Lazy OpenAI client, no import-time side effects | AI | App boots, migrations and tests run without a key; first call fails with clear error | [x] |
| P0-03 | Explicit timeouts + retry policy | AI | Connect 5 s / read 30 s; `max_retries=0`; retry only 429/5xx/timeouts with backoff + jitter | [x] |
| P0-04 | Request/response schemas | AI | Translation and conversation inputs/outputs validated; 2–4 lines, speaker enum, length caps, Hangul check | [x] |
| P0-05 | Conversation XSS fix | Experience | LLM strings rendered with `textContent`; no `innerHTML` of model output | [x] |
| P0-06 | SQLite WAL, busy timeout, foreign keys | Platform | Pragmas set on connect; migration and media failure tests pass | [x] |
| P0-07 | Transactional media + cleanup | Media | TTS/merge failure leaves zero DB rows and zero files; media audit command | [x] |
| P0-08 | Migration baseline | Platform | `flask db upgrade` on empty DB creates all tables; existing DB upgrades cleanly | [x] |
| P0-09 | Rate limiter replacement | Platform | Thread-safe, bounded, per-endpoint, proxy-aware; `Retry-After`; tests | [x] |
| P0-10 | Error handling | Platform | API 404 stays 404; no raw exception leakage; request IDs | [x] |
| P0-11 | Security headers + optional auth gate | Platform | CSP, HSTS, frame/referrer headers; optional password gate; localhost warning | [x] |
| P0-12 | Tests + CI | Quality | pytest suite, ruff, migration-on-empty-DB, orphan-file check; GitHub Actions | [x] |
| P0-13 | README/status truth pass | Docs | README matches features; status links blueprint | [x] |
| P0-14 | Orphan audio audit | Media | Dry-run report; `--delete` behind explicit flag; no accidental deletion | [x] |

**Exit criteria:** all P0 tasks closed except user key rotation; `pytest` green; `flask db upgrade` works from empty; a failed conversation leaves no rows/files; no `innerHTML` of model output.

---

## 3. Phase 1 — Learning core (weeks 3–6)

**Goal:** a new learner can sign up (or use local mode), speak Korean in under two minutes, complete a 10-minute review session, and see one can-do artifact.

| ID | Task | Stream | Acceptance | Status |
|---|---|---|---|---|
| P1-01 | Postgres-ready config; SQLite local fallback | Platform | Same models run on SQLite/Postgres; Alembic baseline | [ ] |
| P1-02 | User/profile/enrollment models + auth | Platform | User-scoped data; local demo user for dev; session auth | [~] local user + user-scoped cards done; auth pending |
| P1-03 | Content schema: items, senses, grammar, audio, scenes | Learning | Seed 300 items, 20 scenes; content hash + status | [~] 30 items seeded; scenes pending |
| P1-04 | FSRS review engine | Learning | One card per (item, skill); due queue; grade route; tests | [~] FSRS-6 engine + server grade route done; JSON API and round-trip persistence tests pending |
| P1-05 | Daily planner | Learning | 2/10/25-minute plans; review-first; 5–10 new cap | [~] 10-new/day cap + review-first queue done; duration modes pending |
| P1-06 | Today / Review / You screens | Experience | Mobile-first; keyboard/IME; Korean `lang`; can-do artifact | [~] Today + Review done; You/can-do pending |
| P1-07 | Onboarding + first spoken sentence | Experience | Goal/time/experience; local record/playback; account after win | [x] local onboarding + recording; real accounts pending |
| P1-08 | Hangul bootcamp days 1–7 | Learning/Experience | Read-aloud checks; typing; batchim/liaison drills | [x] 7 lessons, 88 interactive drills; timed typing/fluency coaching next |
| P1-09 | Can-do + progress model | Learning | Skill map, retention, artifacts; no XP hero metric | [~] skill breakdown + recent reviews; can-do artifacts and retention pending |
| P1-10 | Alpha instrumentation | Quality | Activation, D1/D7, review latency, error rate | [~] Event table + `flask metrics` done; latency/error dashboards pending |

**Exit criteria:** 20 alpha users; first spoken sentence < 2 min; 10-minute session end to end; p95 review < 200 ms; no orphan files; 30-day retention instrumentation live.

---

## 4. Phase 2 — Speech + scenes (weeks 7–12)

| ID | Task | Acceptance | Status |
|---|---|---|---|
| P2-01 | Push-to-talk capture + waveform + retry | Works on iOS Safari/Chrome; cancel/retry/type/skip | [~] MediaRecorder capture + playback done; waveform/retry UX pending |
| P2-02 | Word-level intelligibility (`gpt-transcribe`) | Show "what I heard"; false-negative logging | [~] transcript + transcript-match done; false-negative logging pending |
| P2-03 | Phoneme evidence (Azure PA / SpeechSuper) | Per-phoneme scores as evidence, not a global grade | [ ] next |
| P2-04 | Sound Gym (perception + production) | 20–30 minimal pairs; 5–8 voices; F0/duration contour | [~] 11 pairs + 8 prompts + browser TTS; native audio/contours pending |
| P2-05 | Scene engine (goal state machine) | Persona, goal, target chunks, success criteria, fallback lines | [~] 4 scripted scenes, tolerant matching, hints, resumable progress; speech answers/branching pending |
| P2-06 | Debrief → cards | 2 strengths, 1 fix, 3 cards; one retry | [~] debrief creates 3 FSRS cards and shows strengths/fix; retry flow pending |
| P2-07 | 30 validated scenes | Native-reviewed; < 1% error rate on gold set | [~] 4 scenes; native review and 26 more pending |
| P2-08 | Native eval harness | 500 items; 2–3 raters; release gate | [ ] |
| P2-09 | Pronunciation artifact | Before/after audio; band feedback; no fake score | [ ] |

**Exit criteria:** 3–5 minute mission works; p95 speech feedback < 3 s; < 1% native-rated content errors; < 2% ASR false negatives.

---

## 5. Phase 3 — Adaptive + beta (weeks 13–20)

- Elo item calibration; BKT mastery; Thompson-sampling selection.
- Placement test with uncertainty; recommended start.
- Leech intervention; scaffold automation; 85% success targeting.
- PWA install, offline review queue, media cache, push where supported.
- Can-do progress, weekly recap, before/after audio.
- Ethical streak: rest day, repair by practice, vacation, notification controls.
- Beta 100–500 users; retention/learning dashboards; pricing test.
- Privacy/DPA review; voice retention; age gate.

**Exit criteria:** D1 ≥ 45%, D7 ≥ 25%, D30 ≥ 15%; 30-day item retention ≥ 85%; variable cost < $4/MAU; NPS ≥ 40.

---

## 6. Phase 4 — Expansion (months 6–12)

- TOPIK track: diagnostic, timed sections, writing templates, mock exams.
- Workplace track: honorifics, email, meetings, phone, industry vocabulary.
- K-drama track: licensed clips, scene mining, shadowing, pragmatics.
- Heritage track: receptive→productive bridge, formal register, literacy.
- Writing feedback: rubric-based LLM + human escalation.
- Human review marketplace; B2B pilot.
- Native mobile app only if PWA data justifies it.

---

## 7. Dependency graph

```
P0-02/03/04 (AI) ─┐
P0-06/07/08 (data/media) ─┼─> P0-12 (tests/CI) ─> P1-03 (content) ─> P1-04 (FSRS) ─> P1-05 (planner) ─> P1-06 (UI)
P0-05 (XSS) ──────┘                                   │
P0-09/10/11 (platform) ───────────────────────────────┘
P1-02 (auth) ─> P1-07 (onboarding) ─> P1-10 (alpha)
P1-04/05/06 ─> P2-05 (scenes) ─> P2-06 (debrief) ─> P2-07 (content)
P1-09 ─> P3 (adaptive/beta)
```

**Critical path:** P0-02 → P0-04 → P0-07 → P0-08 → P1-03 → P1-04 → P1-05 → P1-06.

---

## 8. Current sprint board (started 19 Oct 2026)

| Task | Owner | State | Notes |
|---|---|---|---|
| P0-02 Lazy OpenAI client | AI stream | done | `app/services/ai.py`, no import-time client |
| P0-03 Timeouts/retries | AI stream | done | `app/utils/retries.py` |
| P0-04 Schemas | AI stream | done | `app/utils/schemas.py`, Pydantic v2 |
| P0-05 XSS/accessibility | Experience stream | done | DOM rendering, skip link, focus, contrast, reduced motion |
| P0-06 WAL/FK | Platform | done | Engine connect listener (`foreign_keys`, WAL, busy timeout) |
| P0-07 Media staging | Media/Platform | done | `AudioBatch`, rollback, `flask media-audit`, `media-gc` |
| P0-08 Migration baseline | Platform | done | `20261019_0001` idempotent phrase baseline + indexes |
| P0-09 Rate limiter | Platform | done | Thread-safe bounded limiter, per-endpoint, `Retry-After` |
| P0-10 Errors | Platform | done | 404/415/500, request IDs, no raw exception leakage |
| P0-11 Headers/auth | Platform | done | CSP, frame/referrer headers, optional basic auth |
| P0-12 Tests/CI | Quality | done | 169 tests, ruff, empty-DB migration gate |
| P1-02/04/05/06 vertical slice | Learning/Experience | done | Local user, 30 seed items, FSRS review, 10-new/day cap, Today/Review/Progress screens |
| P1-07 Onboarding + first word | Experience | done | Goal/time/experience/timezone, first spoken 안녕하세요, local recording |
| P1-08 Hangul days 1–7 | Learning/Experience | done | 7 lessons, 88 drills, mobile tables, Korean font fallback |
| Seed audio pipeline | AI/Media | done | `flask generate-item-audio` with dry-run, limit, force, rollback |
| Mission scenes v0 | Learning/Experience | done | 4 scenes, tolerant matcher, progress, debrief → 3 cards |

**Sprint exit demo:** ✅ boot with no key → ✅ `pytest` green → ✅ `flask db upgrade` from empty → ✅ failure path leaves zero rows/files → ✅ review a seeded card → ✅ grade it → ✅ see the due count drop and the next card.

**Remaining before Phase 0 can be called fully closed:**

- **P0-01 is a user action:** rotate the OpenAI key that has been in `.env`. The repo cannot do this for you.
- Optional: run `flask media-audit` and `flask media-gc --delete` to remove the 15 orphaned prototype MP3s. The command is dry-run by default.
- Optional: move from the in-process rate limiter to Redis before running multiple workers.

---

## 9. Metrics we will actually use

| Layer | Metric | Target |
|---|---|---|
| Activation | First spoken Korean sentence < 2 min | ≥ 80% |
| Activation | First session complete | ≥ 60% |
| Learning | 30-day item retention | ≥ 85% |
| Learning | 7-day can-do pass | ≥ 70% |
| Engagement | Sessions/week | ≥ 4 |
| Quality | Native-rated content errors | < 1% |
| Quality | ASR false negatives | < 2% |
| Retention | D1 / D7 / D30 | 45 / 25 / 15% |
| Cost | Variable cost / MAU | < $4 |
| Guardrail | Notification opt-out | < 10% |

---

## 10. Risk log

| Risk | Trigger | Response |
|---|---|---|
| Scope creep | More than one track in Phase 1 | Cut to Everyday A1; park everything else |
| Content errors | Native error rate > 2% | Pause generation; curated-only; add review capacity |
| ASR demoralization | False negatives > 2% | Show transcript; retry/type/skip; recalibrate |
| Cost blowout | > $4/MAU | Cache, pre-generate, cheaper models, cap free tier |
| Solo bandwidth | Missed sprint exit | Reduce scope; buy infra; no custom ML |
| Retention flat | D30 < 8% after 8 weeks | Stop content; re-interview; fix value proof |
| Privacy | Voice data retention unclear | Default 24–72 h; consent; age gate; legal review |

---

## 11. Changelog

| Date | Change |
|---|---|
| 2026-10-19 | Roadmap created; research/blueprint delivered |
| 2026-10-19 | Phase 0 implemented and verified: lazy AI client, schemas, timeouts/retries, XSS fix, WAL/FK, transactional media, migration baseline, rate limiter, error handling, security headers, tests/CI |
| 2026-10-19 | Phase 1 vertical slice shipped: local user, 30-item seed deck, FSRS-6 review engine, 10-new-cards/day cap, Today/Review/done screens, mobile layout |
| 2026-10-19 | Independent review fixes: submit-time due/new-card invariants, idempotency guard, item audio protected from media-gc, proxy-safe IPs, request-ID logging, config-driven models, commit boundaries, Hangul validation, CSRF on review form, local-day accounting |
| 2026-10-19 | Onboarding shipped: goal/time/experience/timezone, first spoken 안녕하세요 with local recording, profile persisted on the local user |
| 2026-10-19 | Hangul bootcamp days 1–3 shipped: letters, vowels/blocks, batchim and sound changes, 32 interactive reading drills, mobile tables, correct Korean font fallback |
| 2026-10-19 | Hangul days 4–7 shipped: double batchim, signs/menus/numbers, connected speech, final reading check; 88 drills total |
| 2026-10-19 | Seed-audio pipeline: `flask generate-item-audio` with dry-run, limit, force, per-item commit, rollback, and idempotent skip |
| 2026-10-19 | Phase 2 start: Sound Gym (11 minimal pairs, 8 production prompts), local recording, transcript-based speech checks, SpeechAttempt persistence, no audio retention |
| 2026-10-19 | Alpha instrumentation: append-only Event table recording onboarding, reviews, Sound Gym opens, and speech attempts; `flask metrics` activation/D1/D7 summary |
| 2026-10-19 | Mission scenes v0: café, directions, pharmacy, workplace intro; tolerant matching, hints, resumable sessions, debrief → 3 FSRS cards; scene events recorded |
