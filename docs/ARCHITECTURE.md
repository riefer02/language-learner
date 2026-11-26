# Architecture

Current as of 23 November 2026. This is the map; `AGENTS.md` is the working
contract, `docs/PROJECT_STATUS.md` is the honest state, and
`docs/architecture/00-decision-2026-11-23.md` is the decision record.

## Shape

```
Browser (Jinja + vanilla JS)
   │  forms / fetch + CSRF
   ▼
Flask blueprints
   ├─ main        /<lang>/, dictionary, library, settings, translate, PWA, /design
   ├─ learn       /learn, /learn/review, /learn/fidel, /learn/hangul, scenes
   ├─ onboarding  /welcome
   └─ teacher     /<lang>/learn/teacher, /api/teacher/*
   │
   ├─ app/learning   review queue, FSRS, stats, scenes, dictionary
   ├─ app/languages  content packs + seeders
   ├─ app/services   AI clients, translation, audio, speech, teacher engine
   └─ app/utils      text, media, retries, rate limits, schemas
   ▼
SQLAlchemy / SQLite (Postgres-ready)
```

One process, one database, one local user. No worker queue, no websocket server
of our own. The browser talks to OpenAI directly for the voice teacher; Flask
only mints the session and serves tools.

## Data model

### Language-neutral core

```
language ──< language_script >── script
   │
   ├──< level_scale
   ├──< course ──< deck ──< deck_item >── item
   │                                          │
   │                                          ├──< item_form   (script, text, translit, audio)
   │                                          ├──< item_gloss  (lang, translation)
   │                                          └──0..1 dictionary_entry ──< dictionary_sense
   │
   └──< term_card >── user
```

- `item` is one learnable unit for any language. `item_type` is
  `lexeme | chunk | grammar | sentence`.
- `item_form` is where written forms live: citation, inflected, variant. A form
  carries a script, normalized text, transliteration scheme, and audio.
- `item_gloss` is a meaning in a UI language. `english` is not a column.
- `dictionary_entry`/`dictionary_sense` are the browseable lexicon;
  `term_card` is the learner's saved copy with context.

### Learner state

- `review_card` is FSRS state for `(user, item, skill)`. Shape is unchanged
  from the Korean-only app; language is implied by the item.
- `review_log` is append-only history.
- `term_card` is the personal library. Saving a term also ensures a review card.
- `content_report` is a learner-flagged correction with a snapshot of what was
  shown. Triage is manual and never rewrites content automatically.
- `item.review_status` records provenance: `unchecked` or `native_checked`.
- `can_do_artifact`, `scene_session`, `speech_attempt` are learner evidence.

### Teacher

```
teacher_session ──< teacher_turn
       │
       └──< drill ──< drill_attempt ──0..1 review_card
```

`teacher_session.provider` names the adapter; `provider_session_id` is opaque.
Raw audio is never persisted.

## Column names

`item.target_text`, `item.gloss`, and `item.transliteration` are the canonical
names for target text, English gloss, and romanization. `phrase.source_text`
and `phrase.target_text` are canonical. The old `korean`/`english`/`korean_text`
columns were renamed in migration `20261123_0014`; do not reintroduce them.

## Request flows

All learner pages live under `/<lang_code>/` (`ko` or `am`). A URL value
preprocessor resolves the language into `g.language`; `url_for` automatically
fills `lang_code` from `g`. Unprefixed legacy paths (`/learn`, `/settings`, …)
301-redirect to the active language. API routes stay unprefixed and resolve the
language from the learner.

### Review

`GET /<lang>/learn` → `current_language(user)` → `ensure_review_cards(user, language)`
→ `stats(user, language)` → `learn_today.html`.
`GET /learn/review` → `next_due_card(user, language)` → reveal → POST rating →
`apply_rating` → `ReviewLog`.

New cards are capped by `NEW_CARDS_PER_DAY`; due reviews always come first.
Gendered Amharic items (`… (to a man/woman/group)`) and register alternates from
`app/languages/variants.py` also render an **Other ways to say it** block from
`review_variants(item, language_code)`, so every review shows the curated forms,
not just the one the card happened to pick.

Alternate forms use stored audio, never browser speech synthesis: gendered forms
are real items and use `item.audio_path`; curated register forms use a stable
`variant_<lang>_<hash>.mp3`. `flask generate-variant-audio` pre-generates them;
`POST /api/variants/audio` generates one missing form on demand after checking it
belongs to the card. `media-audit`/`media-gc` count existing variant files as
referenced.

### Teacher (voice)

```
Start → getUserMedia → RTCPeerConnection + oai-events channel → SDP offer
Flask POST /api/teacher/sessions
  → create TeacherSession (pending)
  → POST /v1/realtime/calls (multipart sdp + session config)
  → answer SDP, provider call id, status=active
Browser audio + transcript events
  → function_call_arguments.done
  → POST /api/teacher/tools/<name>  (allowlisted, language-scoped)
  → conversation.item.create(function_call_output) + response.create
End → POST /api/teacher/sessions/<id>/end → debrief
  → POST /api/teacher/drills/<id>/attempt → DrillAttempt + ReviewCard
```

Tools: `get_due_items`, `lookup_dictionary`, `create_drill`,
`add_term_to_library`, `log_attempt`, `end_session_summary`.

### Dictionary

`/dictionary?q=` → `search_items(language_id, q)` → save POST →
`save_term` → `TermCard` + `ReviewCard` for the item's default skill.
The teacher's `add_term_to_library` calls the same function.

### Translation

`POST /api/translate` → `translate_text_with_romanization(text, target_code,
addressee, register)` → script validation (Hangul for `ko`, Ethiopic for `am`) →
`generate_audio` → `Phrase` with source/target ids, `target_text`,
`target_transliteration`, `addressee`, and `register` → JSON with `target_text`,
`romanization`, `addressee`, `register`, and `target_lang`.

The romanization is generated in the same model call as the translation (Revised
Romanization for Korean, a simple Latin transliteration for Amharic). It is a
reading guide, not a pronunciation grade, and the field is optional: a response
without it still saves the translation.

For Amharic, `addressee` is `male`, `female`, `group`, or `any`. The prompt uses
the matching second-person forms; `any` asks for both when the phrase has a
gender contrast. The value is stored on the phrase and shown in the library.

Every language can also set `register`: `casual`, `polite`, or `formal`.
Korean defaults to `polite` (해요) and offers formal (합니다) and casual (반말);
Amharic defaults to `formal` (እርስዎ) and offers everyday (አንተ/አንቺ). The chosen
speech level changes the prompt, the cache key, and the saved phrase. The API
accepts `register` (the internal field is `formality`; both names validate),
and values the target language does not offer are clamped to its default. A
language with no register choices stores no register label. Migration `0020`
labels pre-formality Amharic phrases as `casual`; Korean legacy rows stay
unrecorded and are shown without a register line.

`GET /<lang>/translate?phrase=<uuid>` is the canonical, replay-free URL for a
saved result: it renders the phrase (text, romanization, addressee, register,
audio) from SQLite and never calls the model or generates audio. Look up pushes
this URL into history after a successful request, so Back and Forward move
between results at no cost. The old `?q=…&run=1` header shortcut stays a
one-shot and is replaced by the phrase URL when it succeeds.

`generate_audio` uses `gpt-audio-1.5` with a `<read>` contract and rejects
conversational output whose transcript does not match the input.

## Language support

| Capability | Korean (`ko`) | Amharic (`am`) |
|---|---|---|
| Review deck | 30 items | 64 items |
| Script course | Hangul `/learn/hangul` | Fidel `/learn/fidel` |
| Dictionary / terms | yes | yes |
| Pre-generated audio | partial | 64 items |
| Scenes | 4 | no |
| Voice teacher | yes | no (OpenAI has no `am` speech) |
| Speech checks | transcript-based | disabled |
| Translation | yes | yes |

Language resolution lives in `app/learning/service.current_language()`: user
preference → `ko` fallback. Content packs should not edit core routes.

## Frontend

- Jinja templates extend `base.html`; one JS file per page under
  `app/static/js/`, included via `{% block scripts %}`.
- CSRF: meta tag `csrf-token`; JSON POSTs send `X-CSRFToken`. Pages with forms
  use `csrf_token()`.
- `mic` requires localhost or HTTPS.
- `active_language` is injected by a context processor; use it for language
  labels and `lang`/TTS attributes (`app/utils/text.py` has the maps).
- No build step. Keep JS dependency-free.

## Testing

- `tests/conftest.py` creates a throwaway SQLite file per test and a fake
  OpenAI client; no network, no key.
- Provider behavior is tested with fakes. The live path is manual and budgeted.
- Migration tests build an old DB with real referencing rows, upgrade, assert
  the backfill, then downgrade.
- CI lints, migrates an empty DB, asserts the table set, and runs pytest.

## Known structural debt

1. **Content is starter-depth.** Amharic needs native review and audio review;
   fidel needs native audio; scenes are Korean-only.
2. **No accounts.** Every feature assumes the single local user.
3. **Amharic ASR/TTS quality is not usable**; do not enable speech features.
4. **Korean-only surfaces remain** (scenes, Hangul, Sound Gym, conversations).
   They redirect for Amharic, but are not yet generalized.
5. **Onboarding is generic**, but the goals/experience wording and first-word
   choice still need language-specific packs beyond Korean and Amharic.
