# AGENTS.md

Kiku is a **local-first language-learning app**: Flask 2.0, SQLAlchemy 1.4,
SQLite by default, server-rendered Jinja, vanilla JS. Python 3.12 in `./venv`.
The product currently teaches **Korean** (voice teacher, scenes, Hangul) and
**Amharic** (review deck, fidel bootcamp, dictionary). One local user, no accounts.

## Read first

- `docs/ARCHITECTURE.md` — module map, data model, request flows, invariants.
- `docs/PROJECT_STATUS.md` — what is actually working and what is not.
- `docs/architecture/00-decision-2026-11-23.md` — why the teacher, languages,
  and model choices are what they are.
- Open `docs/research/*` only when the task is about vendor/model choice.

## Commands (always from the repo root)

```bash
make test                                  # full pytest suite
venv/bin/python -m pytest tests/test_teacher.py -q
venv/bin/ruff check app config.py run.py tests
venv/bin/python run.py                     # dev server on :5000

FLASK_APP=run.py venv/bin/python -m flask db upgrade
FLASK_APP=run.py venv/bin/python -m flask seed-content
FLASK_APP=run.py venv/bin/python -m flask seed-amharic
FLASK_APP=run.py venv/bin/python -m flask generate-item-audio --language am
```

`.env` is read at process start. **Restart the server after changing it.**
Never commit `.env`, `*.db`, `backups/`, `audio_output/`, or generated media.

## Layout that carries meaning

| Path | Responsibility |
|---|---|
| `app/models.py` | Core tables (`Item`, `ReviewCard`, `ReviewLog`, learner state); imports the two model modules below for metadata |
| `app/models_language.py` | Language, Script, LevelScale, Course/Deck, ItemForm/ItemGloss, Dictionary, TermCard |
| `app/models_teacher.py` | TeacherSession, TeacherTurn, Drill, DrillAttempt |
| `app/main/` | `main` blueprint split by surface: home, content, settings, system, translate, conversations |
| `app/learning/service.py` | Review queue, stats, streak, language resolution — every query is language-scoped |
| `app/learning/dictionary.py` | Dictionary search, save-term, review-card handoff |
| `app/services/teacher.py` | Teacher engine, provider adapter, tool router, drill grading |
| `app/teacher/routes.py` | Teacher HTTP/API surface and page |
| `app/languages/` | Content packs and seeders (`ko` legacy, `am`) |
| `app/utils/text.py` | The one normalization/similarity/script helper |
| `app/templates/`, `app/static/js/` | Server-rendered UI; one JS file per page |

Do not create per-language tables. One `item` table with `language_id` is a
load-bearing decision because FSRS is keyed by `(user, item, skill)`.

## Invariants

- **Language scoping:** any new content query filters `Item.language_id` (or
  joins through it). Use `available_cards(..., language_id=...)`; never
  `Item.query` without a scope in learner-facing code.
- **Column names:** `item.target_text`, `item.gloss`, `item.transliteration`,
  and `phrase.source_text` / `phrase.target_text` are canonical. Never
  reintroduce `korean` / `english` / `korean_text` columns.
- **Language URLs:** every learner page is `/<lang_code>/...`; `g.language` is
  set by the URL preprocessor and `url_for` fills `lang_code` automatically.
  API routes stay unprefixed and resolve language from the learner.
- **Review scheduling:** teacher/drill paths may create a `ReviewCard`, but
  never call `apply_rating` to fabricate a review. Only the review page grades.
- **Teacher:** the OpenAI key stays server-side; tools are allowlisted; drill
  item IDs are intersected with the session's language; raw audio is never stored.
- **TTS:** `gpt-audio-1.5` must *read* the text. Keep the literal-read guard in
  `generate_audio`; a conversational reply is a bug, not audio.
- **Migrations:** never edit an applied migration. SQLite cannot batch-rebuild
  `phrase`/`item` while rows reference them with FKs on — use plain nullable
  `ADD COLUMN`, and add an old→new test that seeds referencing rows.
- **OpenAI-only.** Do not add a Gemini/other provider without an explicit ask.

## Where does this change go?

| Change | Do |
|---|---|
| New learner page | `app/main/` (or the owning blueprint) route under `/<lang_code>/` + template + JS + nav link + test |
| Review/queue logic | `app/learning/service.py`, then tests in `tests/test_learning_loop.py` |
| Dictionary/library | `app/learning/dictionary.py`, `app/main/content.py`, `templates/dictionary.html` |
| Teacher behavior/tool | `app/services/teacher.py` (`TOOL_SCHEMAS` + handler + `TOOL_HANDLERS`), route if new HTTP surface |
| New language | `app/languages/<code>_content.py` + `seed.py` + CLI; no core edits |
| New table | matching `models_*.py`, import in `app/models.py`, migration, CI table list |
| New prompt/model | `app/services/translation.py` or `teacher.py`; keep provider/model in config |

## UI conventions

- `base.html` owns the single `<h1>` (brand) and the `<main>` landmark. Page
  titles are `<h2>`; sections are `<h3>`.
- Reuse the existing classes: `page-hero`, `language-badge`, `tutorial-card`
  (with `data-dismissible` + `[data-dismiss]`), `help-tip` (native
  `<details>`), `empty-state`, `chip-row`, `learn-meta`.
- Every control needs a visible `<label>` or `aria-label`; every icon button
  needs a name. Keep the skip link and the global focus-visible ring.
- The primary nav collapses at 900px via `#nav-toggle`; test a new nav item at
  390px before shipping.
- Bump the `?v=` query on changed CSS/JS includes so Chrome does not test a
  stale asset.

## Workflows

**Add a language**
1. Add items/script data under `app/languages/`.
2. Seed `Language`, `LanguageScript`, `Course`, `Deck`, `Item`, `ItemForm`,
   `ItemGloss`, `DeckItem`, then `ensure_review_cards(user, language_id)`.
3. Add it to the settings language list; scope every new query; run tests.
4. Do not claim speech support unless the provider actually supports the language.

**Change the teacher**
1. Prefer adding a tool to the existing allowlist over widening the prompt.
2. Validate args with Pydantic, scope item IDs to the session, persist the turn.
3. Add a fake-provider test in `tests/test_teacher.py`; never call the live API
   in tests.

**Change the schema**
1. Expand with nullable columns → backfill → dual-write → contract, in separate
   releases.
2. Add an old→new migration test with real referencing rows.
3. Update `.github/workflows/ci.yml` expected tables if you add one.

## Done means

- `venv/bin/ruff check app config.py run.py tests` passes.
- `venv/bin/python -m pytest -q` passes.
- A migration change upgrades a **fresh** DB and a **seeded legacy** DB.
- A new page has a smoke test; a new tool has a fake-provider test.
- `docs/PROJECT_STATUS.md` reflects any user-visible change.
- Live API checks are manual and budgeted; ask before spending beyond cents.
