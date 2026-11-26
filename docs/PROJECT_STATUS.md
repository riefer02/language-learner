# Project Status — 25 November 2026

**Verdict:** a working single-user alpha with a real-time Korean voice teacher,
a Korean + Amharic review core, a dictionary and personal term library, and a
fidel bootcamp. Not ready for public use: no accounts, no pronunciation scoring,
and Amharic speech is unsupported by the current provider.

Current architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md). Decisions:
[`architecture/00-decision-2026-11-23.md`](architecture/00-decision-2026-11-23.md).

---

## Historical detail — 20 October 2026

**Repository:** [language-learner](https://github.com/riefer02/language-learner) (product name: **Kiku**)
**Verdict at the time:** Phase 0 (stabilize) complete; the first FSRS review loop working.

## What works today

- English → Korean translation via `gpt-4.1-nano`, with validated structured output
- Korean TTS via OpenAI `tts-1` (single voice, or two voices in conversations)
- Saved phrase library with pagination and audio playback
- Short 2–4 line conversation generation with per-line and merged audio
- **Onboarding:** goal, daily time, experience, timezone, and a first spoken 안녕하세요 with local-only recording
- **Learn loop:** `/learn` today view, `/learn/review` retrieval card, 1–4 grading, FSRS-6 scheduling, review log, and time-boxed 3/10/25-minute sessions
- **Seed deck:** 30 hand-curated Korean items (survival phrases, core nouns, five grammar patterns), one review card per item
- **Daily new-card cap:** 10 new cards per day; review cards are always prioritized
- **Hangul bootcamp:** seven lessons (letters, vowels/blocks, batchim, double batchim, signs/menus/numbers, connected speech, final reading check) with 88 interactive drills
- **Mission scenes:** four scripted roleplays (café, directions, pharmacy, workplace intro) with tolerant answer matching, hints, resumable progress, voice answers, and a debrief that adds three chunks to the review deck
- **Can-do proof:** completing a scene creates a dated “I can…” artifact, shown on the progress page and as the next mission on Today
- **Sound Gym:** 11 minimal-pair perception drills, 8 production prompts, local-only recording, and transcript-based speech checks
- **Speech evidence:** `SpeechAttempt` records what the model heard and a transcript-match score — explicitly not a pronunciation grade; raw audio is never stored
- **Alpha instrumentation:** append-only `Event` table and `flask metrics` for activation, review users, speech attempts, D1/D7
- **Resources:** searchable Korean/English/romanization/notes lookup with type and level filters, plus quick links to Hangul, scenes, Sound Gym, library, conversations, translation, and settings
- **Installable PWA:** web manifest, icons, install metadata, an app-shell service worker, and a cached offline fallback
- **Gentle reminders:** `/settings` stores goal, daily time, timezone, reminder on/off, and reminder time; browser push subscriptions are stored server-side; `flask send-reminders` delivers at most one due-card reminder per learner per local day and skips days with nothing due
- **Progress view:** skill breakdown, last-7-days activity, 7+/30+ day delayed-retention signal, can-do proof, recent reviews, practiced-card count
- **Local single-user mode:** a local `User` row scopes profile, review cards, and logs; real accounts are next
- CLI translation/TTS tool (`hangul.py`)
- `flask seed-content`, `flask media-audit`, `flask media-gc`
- **195 automated tests**, ruff clean, CI with an empty-database migration gate and push-schema assertions

## What changed in Phase 0

- OpenAI clients are lazy; the app, migrations, and tests boot without a key.
- Explicit connect/read timeouts and `max_retries=0`; only transient errors are retried, with backoff.
- Pydantic schemas validate requests and model output (line count, speakers, lengths, Hangul).
- Conversation rendering uses `createElement`/`textContent`; no model-controlled `innerHTML`.
- SQLite uses WAL, `busy_timeout=5000`, `foreign_keys=ON`.
- Audio is generated in a private staging directory and moved only after success; failed jobs leave zero rows and zero files.
- Alembic builds a fresh database from empty; the missing `phrase` baseline is repaired.
- Rate limiting is thread-safe, bounded, per-endpoint, proxy-aware, and returns `Retry-After`.
- API 404/415/500 responses are correct, include request IDs, and do not leak internals.
- Security headers (CSP, frame/referrer policies), optional basic-auth gate, localhost warning.
- README, `.env.example`, Makefile, and CI reflect reality.

## Current screens

| Today | Review |
|---|---|
| ![Today screen](screenshots/learn-today.png) | ![Review screen](screenshots/learn-review.png) |

| Answer revealed | Mobile |
|---|---|
| ![Answer revealed](screenshots/learn-review-answer.png) | ![Mobile](screenshots/learn-mobile.png) |

| Onboarding | First spoken sentence |
|---|---|
| ![Onboarding](screenshots/onboarding-welcome.png) | ![First word](screenshots/onboarding-first-word.png) |

| Hangul lessons | Hangul drills |
|---|---|
| ![Hangul index](screenshots/hangul-index.png) | ![Hangul lesson](screenshots/hangul-lesson.png) |

| Sound Gym | Mission scenes |
|---|---|
| ![Sound Gym](screenshots/sound-gym.png) | ![Scenes](screenshots/scenes.png) |

| Scene play | Scene debrief |
|---|---|
| ![Scene play](screenshots/scene-play.png) | ![Scene complete](screenshots/scene-complete.png) |

| Voice answer panel | Weekly progress |
|---|---|
| ![Scene voice input](screenshots/scene-play-voice.png) | ![Weekly progress](screenshots/progress-weekly.png) |

| Resources | Resource search |
|---|---|
| ![Resources](screenshots/resources.png) | ![Resource search](screenshots/resources-search.png) |

| Settings & reminders |
|---|
| ![Settings](screenshots/settings.png) |

## What still does not exist

- Real user accounts, sessions, OAuth, and per-user data isolation (local single-user only)
- Postgres deployment; SQLite is still the default
- Placement test and an adaptive starting point (onboarding captures self-report only)
- Hangul typing drills and timed fluency coaching (the 7-lesson decoding curriculum is complete)
- Phoneme-level pronunciation scoring, prosody feedback, and calibrated L2 ASR (current checks are transcript-based)
- Native-reviewed audio for the seed deck, Sound Gym, and scene characters (browser TTS is a stopgap)
- Branching scene state and adaptive difficulty (scenes are scripted, 3 steps each)
- Native-reviewed character audio for scenes (browser TTS is a stopgap)
- Fuller grammar reference: parsed examples, register notes, and contrast pages beyond short item notes
- Streak repair, vacation mode, and a flexible habit system (a basic day streak exists)
- A full offline review queue (the PWA currently caches the shell and an offline fallback, not review data)
- Content pipeline: 30 items, 7 Hangul lessons, and 4 scenes only; no 20-scene library, no native review queue, no audio for seed items
- Speech/TTS cost controls beyond caching (no per-user budget)
- Postgres/Redis/multi-worker production setup

## Top risks

1. Content quality and breadth: 30 items is a demo, not a curriculum.
2. Single-user local mode; real accounts and per-user isolation are required before a public beta.
3. No native audio on seed items; browser speech synthesis is a temporary fallback.
4. Single-user local mode; auth and data isolation are required before any public deployment.
5. Transcript matching is useful evidence, not pronunciation scoring; phoneme/prosody feedback is still the hardest differentiator to build.
6. Reminder delivery needs a cron worker and HTTPS in production; the in-app loop works without it.

## Where to go next

- **Execution plan and status:** [`ROADMAP.md`](ROADMAP.md)
- **Product and learning design:** [`KIKU_BLUEPRINT.md`](KIKU_BLUEPRINT.md)
- **Full audit with file:line evidence:** [`research/01-codebase-audit.md`](research/01-codebase-audit.md)
- **Learning science:** [`research/02-learning-science.md`](research/02-learning-science.md)
- **Korean pedagogy:** [`research/03-korean-pedagogy.md`](research/03-korean-pedagogy.md)
- **Competitive teardown:** [`research/04-competitive-teardown.md`](research/04-competitive-teardown.md)
- **Architecture and AI:** [`research/05-tech-and-ai.md`](research/05-tech-and-ai.md)

**Immediate next sprint:** rotate the exposed key and run `flask generate-item-audio` → add phoneme evidence (Azure/SpeechSuper) behind the existing speech interface → real accounts + Postgres → 20 alpha users and a `flask metrics` review. Deploy `flask send-reminders` on a 5–15 minute cron once HTTPS is available.

---

## Update — 23 November 2026: multilingual foundation

Phase 1 of the language-neutral refactor is shipped. It is additive and has no
user-visible effect yet.

- **New tables:** `language`, `script`, `language_script`, `level_scale`,
  `course`, `deck`, `deck_item`, `item_form`, `item_gloss`,
  `dictionary_entry`, `dictionary_sense`, `translation`, `term_card`.
- **Language columns** added (nullable) to `item`, `phrase`, `conversation`,
  `user`, `speech_attempt`, `scene_session`, `can_do_artifact`, `event`.
- **Backfill:** all Korean items now have a Hangul citation form, an English
  gloss, `language_id=ko`, and `ko-core` deck membership; phrases carry
  `en→ko` source/target IDs and text.
- **Migrations:** `20261123_0011` (expand) and `20261123_0012` (backfill).
  Verified up from `20261019_0010` with live rows, down again with no data loss.
- **Ops:** `flask language-audit` reports coverage.
- **P0 fix:** `gpt-4.1-nano` was shut down on 23 Oct 2026; defaults moved to
  `gpt-5.6-luna`, with correct handling for reasoning-tier chat models.
- **Tests:** 202 pass; ruff clean; CI migration gate updated.

The plan, the Amharic recommendation, the teacher design, and the real-time
vendor decision are in
[`architecture/00-decision-2026-11-23.md`](architecture/00-decision-2026-11-23.md).

**Expiring models to migrate next:** `tts-1` shuts down 6 Jan 2027 and
`gpt-4o-transcribe` on 26 Feb 2027; both need the provider boundary before
then.

### Voice teacher (same day)

- `/learn/teacher` runs a real two-way voice lesson through OpenAI Realtime
  (`gpt-realtime-2.1-mini`) with Korean transcription, live transcript,
  on-demand drills, a personal term library, and an end-of-session debrief.
- Six allowlisted teacher tools write through the app: due items, dictionary
  lookup, create drill, save term, log attempt (creates a `produce` FSRS card),
  and end-summary.
- New tables `teacher_session`, `teacher_turn`, `drill`, `drill_attempt`
  (migration `20261123_0013`). No raw audio is stored.
- `gpt-transcribe` replaces the retiring `gpt-4o-transcribe` for speech checks.
- 211 tests pass; the teacher page renders on the migrated local database.
- Remaining deadline: pre-generated item audio still uses `tts-1` (shutdown
  6 Jan 2027). Live teacher voice does not depend on it.

### OpenAI-only cleanup and Amharic (same day)

- Pre-generated audio moved from `tts-1` to `gpt-audio-1.5` through Chat
  Completions. No Gemini key and no `/v1/audio/speech` dependency.
- `TEACHER_DAILY_MINUTES` and `TEACHER_MAX_SESSION_MINUTES` are enforced; new
  sessions return 429 when the daily budget is spent.
- Amharic (`am`) is active with a 64-item survival deck, Ge'ez forms and
  transliterations, review cards, and a six-lesson **Fidel** bootcamp at
  `/learn/fidel`.
- Settings → Learning switches between Korean and Amharic; review and progress
  are scoped per language.
- The voice teacher remains Korean-only because OpenAI Realtime does not
  support Amharic speech; the UI states this.
- Amharic content is starter material pending native review.

### Live verification and completion pass (same day)

- Verified with a valid key: all four models accessible; EN→KO and EN→AM
  translation; KO and AM TTS; KO ASR; realtime WebSocket audio, transcript,
  and a real tool call; exact teacher config accepted by the realtime API.
- TTS now rejects conversational drift instead of saving the wrong audio.
- Added a language-scoped dictionary with save-to-library, a “My terms”
  library section, and post-call drill grading that schedules FSRS cards.
- Translation is generic by target language with script validation.
- Generated audio for all 64 Amharic items; resources, progress, and review are
  scoped per language.
- Remaining: browser WebRTC SDP test, Amharic speech (unsupported by OpenAI),
  accounts, pronunciation scoring, and content depth.

### Documentation and agent guidance (same day)

- Added root `AGENTS.md`: commands, invariants, decision table, workflows, and
  definition of done for coding agents.
- Added `docs/ARCHITECTURE.md`: current module map, data model, request flows,
  legacy-column mapping, language support matrix, and structural debt.
- Rewrote `README.md` to match the product (teacher, Amharic, dictionary,
  current models).
- Marked `KIKU_BLUEPRINT.md` and `ROADMAP.md` as historical and pointed them at
  the current decision record.
- Consolidated text normalization into `app/utils/text.py`; added
  `Item.target_text` / `Item.gloss` accessors for the legacy columns.
- Korean-only scenes, Hangul, Sound Gym, and conversations now redirect or
  reject for Amharic instead of silently serving Korean content.

### Structural refactor (same day)

- **Column contract** migration `20261123_0014` renamed `item.korean` →
  `target_text`, `item.english` → `gloss`, `item.romanization` →
  `transliteration`; `phrase` now uses only `source_text`/`target_text`.
  Verified up and down on a copy with real rows, then applied to the live
  database; all 94 items and 13 phrases preserved.
- **Language-explicit URLs**: every learner page now lives under `/<lang_code>/`
  (`/ko/learn`, `/am/learn`, `/am/dictionary`, …). A URL preprocessor sets
  `g.language`; `url_for` fills `lang_code` automatically. Legacy paths such as
  `/learn` and `/settings` 301-redirect to the active language. Unprefixed APIs
  accept `?lang=` or a JSON `lang` field.
- **Route split**: `app/routes.py` is gone. The `main` blueprint now lives in
  `app/main/` (`home`, `content`, `settings`, `system`, `translate`,
  `conversations`, shared `helpers`). Endpoint names are unchanged.
- **Dead compatibility code removed**: the Korean-only `TranslationResponse`
  schema and `korean_translation` alias are gone.
- **Onboarding is language-aware** for Korean and Amharic (first word, script
  wording, goal filtering).
- Full suite and ruff pass; `/`, `/ko/*`, `/am/*`, translation, dictionary, and
  teacher pages all render against the migrated live database.

### Browser end-to-end pass (same day)

Tested in Chrome against `127.0.0.1:5000`:

- Home translation (EN→KO) with generated audio; Learn → review → grade; dictionary
  search → save term → library; resources search; settings language switch
  (KO→AM→KO) with correct URL redirect; Amharic review, dictionary, and fidel
  drill (typing, feedback, progress); scenes (café step 1→2); Hangul lesson;
  Sound Gym; progress; legacy path redirects; 404 page; mobile viewport.
- **Live teacher verified in the browser**: mic permission, WebRTC connected in
  under a second, real audio and two-way transcript, clean end, and debrief.
- Fixed during the pass: hidden loading spinner was visible; fidel JSON was
  double-escaped so the drill never started; Ethiopic text needed a bundled
  Noto font; fidel answers asked for a bare vowel instead of the full syllable;
  `/ko/library` leaked Amharic saved translations; settings still said
  “Everyday Korean” and showed TOPIK for Amharic; teacher end status raced to
  “disconnected” after a clean end.
- Browser console clean on all pages; no server 500/502s. Teacher tool calls
  were already verified over the realtime WebSocket; the browser call verifies
  the WebRTC transport, audio, transcripts, and lifecycle.


### UI, guidance, and accessibility pass (same day)

- Responsive navigation: brand link, disclosure menu under 900px with
  `aria-expanded`/`aria-controls`, Escape to close, Settings exposed in the
  nav, and `aria-current` on every item.
- Page framing: `page-hero`, language badge, consistent cards, footer with
  privacy note, and one `<h1>` per page.
- First-run guidance: dismissible three-step cards on Learn and Teacher,
  accessible `<details>` help for “due”, the four ratings, saving terms, fidel
  vowel orders, and what to ask the teacher. Dismissal is stored locally.
- Dictionary: no longer dumps the whole deck on load. It shows suggested
  searches, “Browse the whole deck”, a result count, and a clear empty state.
- Fidel: progress bar, live feedback, and a grid explanation.
- Accessibility audit in-browser: every page has one h1 and one main, no
  duplicate IDs, no unlabelled form controls, no unnamed buttons/links, no
  images without alt text, no horizontal overflow at 390px.
- Mobile and desktop screenshots verified in Chrome; console clean.


### Information architecture and design system (same day)

- **Home is Today.** `/` and `/<lang>/` land on `/<lang>/learn`; the phrase
  translator moved to `/<lang>/translate` under the **Words** group.
- **Navigation is grouped** into Learn / Practice / Words / Settings instead of
  eight flat links. The current language is a persistent header select that
  changes language and lands on Today.
- **My terms is discoverable** from the header, from a Today card with the saved
  count and preview, and from the dictionary. The page is now “Words you kept.”
- **Design tokens**: primitive palette → semantic colors → spacing, radius,
  elevation, type, and motion scales. New components use tokens; legacy CSS is
  migrated opportunistically. Tailwind was deliberately not added (see
  `docs/DESIGN.md`); the framework remains Flask + Jinja + vanilla JS + plain CSS.
- **Live style guide** at `/design` documents tokens and components.
- Browser-tested desktop and 390px mobile: grouped menus, language switch
  KO↔AM, My terms navigation, no overflow, no console errors.

### Adversarial review pass (same day)

Three parallel reviews (code, design/accessibility, security/deployment) ran
read-only. Fixes shipped:

- **Safety:** production config is now the default for WSGI entrypoints; strong
  secret validation; global CSRF protection; CSRF headers on the AI APIs;
  upload cap raised to match the speech budget; push endpoints must be public
  HTTPS; CI read-only permissions; `.env` mode 600 and `backups/` ignored.
- **Language correctness:** Korean seed items, scene debrief cards, scene
  sessions, and can-do artifacts are explicitly tagged `ko`; teacher tools
  (`get_due_items`, `lookup_dictionary`, drill fallback) are scoped to the
  session language; teacher terms link to their session (`0015`); debriefs no
  longer list terms from other lessons.
- **Data integrity:** turn indices retry on the unique constraint; ending a
  session twice preserves the model summary; review/new-card counts are
  language-scoped; the learner’s timezone is honored; concurrent term saves
  recover instead of returning 500; migration `0014` backfills before dropping.
- **Design/UX:** Amharic resources and onboarding no longer link to Hangul-only
  surfaces; conversations are language-scoped; My terms naming is consistent;
  review has a real heading and keyboard grading works after reveal; the
  dictionary no-match copy is correct; duplicate empty states removed; all page
  scripts are cache-busted.
- **Progressive enhancement:** the nav and language switch work without JS.

Documented debt: Flask 2.0 / Werkzeug 2.0 / SQLAlchemy 1.4 upgrades, single
process rate limiting, no license yet, and the remaining legacy CSS rules.

### Design audit and scene listening companion (25 November 2026)

- Added a collapsed **“Hear a natural reply”** companion to every mission scene
  step. It shows the canonical reply with transliteration, gloss, and notes, and
  plays it through the existing speech fallback. Opening it plays once; the
  button replays. Collapsed by default so production practice stays retrieval-
  first. Covered by a new scene test.
- Wrote [`design-audit-2026-11-25.md`](design-audit-2026-11-25.md): page framing
  and accessibility are sound; the debt is documentation drift (Settings and
  Browse in `DESIGN.md` no longer match the nav), 34 hex values still outside
  `:root`, manual asset versions, and two duplicate selector blocks.
- 257 tests pass; ruff clean.

### Content reports and native-check provenance (25 November 2026)

- Review answers, saved terms, and translated phrases now offer a
  **“Something’s off?”** disclosure: issue kind, the native speaker’s version,
  where/to whom it was said, and a note. It posts to `/api/content-reports`
  without leaving the page.
- New `content_report` table (migration `0016`) stores a snapshot of what was
  shown, so a report survives an item or phrase edit. Reports are scoped to the
  page language, not the learner’s stored preference.
- Triage is CLI-only: `flask content-reports`,
  `flask content-report-close <id> --status accepted|rejected`, and
  `flask content-check <item_id> [--uncheck]`. Nothing is rewritten
  automatically; the accept path warns when the target text and cached audio
  need separate regeneration.
- Accepting an item report marks `item.review_status = native_checked` only
  when the suggested text exactly matches the current target. A differing
  suggestion or a bare complaint leaves it `unchecked`; edit first, then run
  `flask content-check <item_id>`. A model never sets it.
- 268 tests pass; ruff clean. Verified live in Chrome: submit, row, CLI output,
  and cleanup.

### Streamlined review (25 November 2026)

- The whole prompt card is now a reveal target; the **Reveal answer** summary
  stays as the keyboard/screen-reader control and Space still works.
- Grading moved into a **sticky bottom bar** with four compact buttons and the
  keyboard hint, so it stays on screen after the answer expands.
- The ratings explainer and **Something’s off?** moved below the grade bar;
  the answer, notes, and provenance stay in the card.
- Verified at 390×667 and 320×568: the grade bar is fully visible without
  scrolling, and the answer/full card still scrolls behind it.
- 268 tests pass; ruff clean.

### Navigation and IA pass (25 November 2026)

- Added a global **English → target Look up** field to the header. It submits
  `/<lang>/translate?q=…`, which pre-fills and runs immediately, with audio.
- Navigation now has one job per group: **Learn** (Today, Review, Progress,
  Hangul/Fidel), **Practice** (Teacher, Scenes, Sound Gym; Korean only),
  **Words** (Look up, Dictionary, My terms). Resources is a deeper browse link
  from the dictionary, not a top-level item.
- Amharic hides Practice and Teacher; Fidel sits under Learn.
- Hangul and Fidel lesson pages carry a clickable course stepper; Hangul drills
  gained a live `0 / N read` progress bar.
- Removed Today’s duplicate footer link row; the tutorial step is now
  language-aware.
- Audit: [`navigation-audit-2026-11-25.md`](navigation-audit-2026-11-25.md).
- 272 tests pass; ruff clean. Chrome-checked at 390px and desktop.

### Dashboard Today (25 November 2026)

- Today is now a dashboard: the date, one **Due now** hero with the primary
  **Start review** action, compact stats (practiced, streak, reviews today,
  next batch), the next mission/course, My terms, and a weekly line.
- Removed the marketing headline, first-run tutorial, duplicate stat cards, the
  due explainer above the fold, and the footer’s duplicate nav links.
- Guidance moved below the dashboard as a single **How Kiku works** disclosure.
- The review CTA is above the fold at 390×844; the dashboard is capped at 800px
  on desktop.
- 272 tests pass; ruff clean.

### Page help and direct UI (25 November 2026)

- **Look up**, **Teacher**, and **Dictionary** now open on the interface: the
  title and the real control first, instructions behind a single `?`.
- The first visit opens the help panel once (`localStorage`); afterwards it
  stays closed. Escape or an outside click closes it.
- The old tutorial cards on Look up and Teacher are gone; the Dictionary help
  box moved into the same panel.
- 274 tests pass; ruff clean. Checked at 390px: the closed Look up page goes
  straight to the input, and the first-visit panel fits the viewport.

### Lookup romanization (25 November 2026)

- The Look up translation call now returns a **romanization** in the same model
  request: Revised Romanization for Korean, a simple Latin transliteration for
  Amharic.
- It is stored on `phrase.target_transliteration` and shown under the lookup
  result and in the library’s phrase cards.
- Migration `0017` adds the nullable column. Older saved phrases have no
  transliteration until they are looked up again.
- 277 tests pass; ruff clean. Verified live with `이거 얼마예요?` →
  `Igeo eolmayeyo?` and audio.

### Styling-system Phase 1 (25 November 2026)

- One **`ASSET_VERSION`** in `app/__init__.py`; every template uses
  `?v={{ asset_version }}`. The five hardcoded version values are gone.
- Page-header typography is unified across `page-head`, `page-hero`,
  `learn-header`, and `dash-head`: same h2 size, margins, eyebrow, and body
  color. Class-name migration is Phase 1b.
- Token sweep: unique hex outside `:root` **34 → 14**, hex declarations
  **126 → 19**; added semantic `--warning-*` / `--info-*` tokens.
- Merged the duplicate `.nav-container` and `.link-button` blocks.
- Added `tests/test_style_contract.py`: raw hex/px budgets, no duplicate
  top-level selectors, no hardcoded `?v=` values.
- Still open: 13 card families, 9 button families, 508 raw px, 7 breakpoints,
  and the four header class names. Tracked in
  [`styling-system-decision-2026-11-25.md`](styling-system-decision-2026-11-25.md).
- 281 tests pass; ruff clean. Header consistency checked at 390px across Today,
  My terms, Resources, Settings, and Progress.

### Adversarial review fixes (25 November 2026)

- Fixed a token-sweep bug that silently deleted five warm backgrounds; the style
  contract now catches truncated `var(--token)` values, raw `rgb()/white`
  declarations, and actually scans the whole stylesheet for duplicate selectors.
- First-visit help renders **inline** instead of covering the form; `?` opens the
  panel on later visits. The panel fits 390/1000px.
- Header lookup runs once (`run=1`), strips the one-shot flag, and blocked
  autoplay no longer shows a false error alert.
- `box-sizing` fixes the 22px input overflow; the last nav submenu is
  right-aligned; review keyboard ignores audio/video/sliders, Space is native,
  and 1–4 has a persisted off switch; grade digit contrast and unnamed
  landmark/label issues are fixed.
- New-card caps and weekly/retention stats are language-scoped. Settings
  URL/form language sync is fixed; unknown `/en`-style prefixes 404; unprefixed
  pages use the preference; Amharic dead ends, manifest, teacher route,
  `/conversations/new`, review-session reset, and TOPIK goal are fixed; CSP
  allows blob media.
- Content-report acceptance semantics, relative SQLite paths, non-string `lang`
  validation, gloss-bearing snapshots, scaled translation output budgets, and
  CSRF request ids are fixed.
- **299 tests pass**; ruff clean.

### Amharic addressee (25 November 2026)

- Look up now asks **“Who are you speaking to?”** for Amharic: a man, a woman, a
  group, or **Not sure — show both**. The choice is passed into the translation
  prompt, which uses the matching second-person forms.
- “Not sure” asks the model for both forms when the phrase has a gender
  contrast; the result and library show which addressee a saved phrase used.
- Migration `0018` stores `phrase.addressee`; older phrases have no addressee.
- Review cards for a gendered item now show an **Other ways to say it** panel
  with every curated form (male, female, group), so the deck teaches the
  contrast instead of hiding the other versions. The seed gained the missing
  female/group "What is your name?" forms and group forms for how-are-you,
  please, goodbye, and welcome.
- **305 tests pass**; ruff clean.

### Formality for every language (25 November 2026)

- Look up now asks **“How formal?”** for both languages: Korean everyday polite
  (해요, default), formal (합니다), and casual (반말); Amharic everyday (default)
  and formal (እርስዎ).
- The choice changes the translation prompt and cache key, is stored as
  `phrase.register` (migration `0019`), and is shown in results and My terms.
- Review cards now also surface curated register alternates from
  `app/languages/variants.py` (for example 감사합니다 → 고마워요 / 고마워 and
  እንደምን ነህ? → እንደምን ነዎት?), so Korean and Amharic teach the contrast.
- **313 tests pass**; ruff clean.

### Saved-result URLs (25 November 2026)

- A successful Look up now pushes `?phrase=<uuid>` into browser history.
  Back and Forward walk through the phrases you just looked at, and reload
  works because the server renders the saved phrase from SQLite.
- This path performs no model call and generates no audio, so history
  navigation cannot re-bill or create duplicate phrases. A missing or
  wrong-language phrase falls back to the form with a short notice.
- The header’s `?q=…&run=1` shortcut remains one-shot and is replaced by the
  saved phrase URL on success.
- 316 tests pass; ruff clean.

### Stored audio for every alternate form (26 November 2026)

- Every **Other ways to say it** form now plays stored audio instead of browser
  speech synthesis. The Amharic gendered forms use their item audio; curated
  register forms use a content-hashed `variant_<lang>_<hash>.mp3`.
- `flask generate-variant-audio --language am` (and `ko`) pre-generates the
  forms; `POST /api/variants/audio` generates one missing form on demand after
  allowlisting it against the card. Generated forms are available on reload.
- The saved-result page no longer re-bills if you press Enter without changing
  the phrase or options; it points at the visible result instead. The library
  now links each saved phrase to its canonical `?phrase=<uuid>` URL.
- The service worker excludes `/static/audio/` (Range/206 responses) and awaits
  cache writes, so generated audio is not cached as a partial response.
- 323 tests pass; ruff clean.

### Settings nav alignment and cache truth (25 November 2026)

- The plain **Settings** link now uses the same inline-flex box, padding,
  font weight, and 12px gap as the Learn/Practice/Words summaries. Measured
  identical on desktop (top 11, height 38) and mobile (16px, height 50).
- Root cause of “the fix keeps not showing”: the service worker cached the
  unversioned CSS/JS and matched with `ignoreSearch`, so it served the previous
  release’s stylesheet for every new `?v=`. It now caches only same-origin
  `/static/` files by **exact URL**; `ASSET_VERSION` works again.
- 303 tests pass; ruff clean. Verified live with `How are you?`:
  - A woman → `እንዴት ነሽ?` / `Endet nesh?`
  - Not sure → `እንዴት ነህ? (እንዴት ነሽ?)`
