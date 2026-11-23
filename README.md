# Kiku

A local-first language-learning app for **Korean** and **Amharic**, built around
retrieval, spaced repetition, and a real-time speaking teacher.

Kiku is not a translation demo. The loop is: review what is due → speak or
write a real answer → get one correction → save the term → see it again later.

## What works today

| Area | Korean | Amharic |
|---|---|---|
| Daily FSRS review | 30-item starter deck | 64-item survival deck |
| Script course | Hangul bootcamp (7 lessons) | Fidel bootcamp (6 lessons) |
| Dictionary + saved terms | yes | yes |
| Pre-generated audio | partial | all 64 items |
| Live voice teacher | yes (OpenAI Realtime) | no — OpenAI has no Amharic speech |
| Scenes / roleplay | 4 scripted scenes | no |
| Speech checks | transcript-based | disabled |

The teacher runs a 7-minute spoken lesson with a plan, recasts mistakes, and can
call app tools: look up a word, create drills, save a term, grade an attempt,
and end with a debrief. Drill answers become FSRS review cards. The API key
never reaches the browser, raw audio is never stored, and daily/session minute
limits are enforced server-side.

## Stack and models

- Python 3.12, Flask 2.0, SQLAlchemy 1.4, Alembic, SQLite (Postgres-ready)
- Server-rendered Jinja + dependency-free vanilla JS
- Chat/translation: `gpt-5.6-luna`
- Speech-to-text: `gpt-transcribe`
- Audio generation: `gpt-audio-1.5` through Chat Completions
- Real-time voice: `gpt-realtime-2.1-mini` over WebRTC

OpenAI is the only AI provider. No Gemini or other vendor is wired in.

## Setup

Requires Python 3.11+ (3.12 recommended), an OpenAI API key, and `ffmpeg` for
conversation audio merging.

```bash
make install-dev                      # venv + runtime + test dependencies
cp env.example .env                   # then set OPENAI_API_KEY
FLASK_APP=run.py venv/bin/python -m flask db upgrade
FLASK_APP=run.py venv/bin/python -m flask seed-content
FLASK_APP=run.py venv/bin/python -m flask seed-amharic
venv/bin/python run.py                # http://127.0.0.1:5000
```

The `.env` file is read when the process starts; restart after changing it.
Microphone access requires `localhost` or HTTPS.

## Routes

| Route | Purpose |
|---|---|
| `/<lang>/` | Redirects to Today |
| `/<lang>/learn` | Today: what is due, my terms, next action (`ko`, `am`) |
| `/<lang>/translate` | Translate a phrase and generate audio |
| `/<lang>/learn/review` | FSRS retrieval card and grading |
| `/<lang>/learn/teacher` | Live voice lesson, transcript, debrief (Korean) |
| `/am/learn/fidel` | Amharic fidel bootcamp |
| `/ko/learn/hangul` | Korean Hangul bootcamp |
| `/<lang>/dictionary` | Search the active deck, save a term |
| `/<lang>/library` | My terms: saved terms and translations |
| `/<lang>/resources` | Browse/filter the active deck |
| `/<lang>/settings` | Language, goal, timezone, reminders |

Unprefixed paths such as `/learn` and `/settings` redirect to the active
language. `/` redirects to the learner's language.

## Commands

```bash
make test                              # full test suite
venv/bin/ruff check app config.py run.py tests
FLASK_APP=run.py venv/bin/python -m flask db upgrade
FLASK_APP=run.py venv/bin/python -m flask seed-content
FLASK_APP=run.py venv/bin/python -m flask seed-amharic
FLASK_APP=run.py venv/bin/python -m flask generate-item-audio --language am
FLASK_APP=run.py venv/bin/python -m flask metrics
```

`flask metrics`, `flask language-audit`, `flask media-audit`, and
`flask send-reminders` are also available.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module map, data model, flows, invariants
- [`docs/DESIGN.md`](docs/DESIGN.md) — framework decision, tokens, components, IA and accessibility
- [`AGENTS.md`](AGENTS.md) — how coding agents should work in this repo
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — honest current state
- [`docs/architecture/00-decision-2026-11-23.md`](docs/architecture/00-decision-2026-11-23.md) — product and architecture decisions
- [`docs/architecture/06-multilingual-refactor.md`](docs/architecture/06-multilingual-refactor.md) — coupling audit and 8-phase refactor plan
- [`docs/research/`](docs/research/) — learning science, Korean pedagogy, competitors, real-time vendors, Ethiopian languages

`docs/KIKU_BLUEPRINT.md` and `docs/ROADMAP.md` are historical design documents
from October 2026. Use the decision record and project status for current truth.

## Known limitations

- Single local user; no accounts or per-user isolation.
- Pronunciation checks compare transcripts, not phonemes or prosody.
- Amharic speech (ASR/TTS/tutor) is not usable with OpenAI today.
- Amharic content is starter-depth and not native-reviewed; scenes are Korean-only.
- No full offline review queue; the PWA caches the shell and an offline fallback.
- Pre-generated Korean audio is partial; browser speech synthesis is a fallback.

## Tests

The suite uses a throwaway SQLite database and a fake OpenAI client: no network
and no key are required. Migrations are tested against an old database with real
referencing rows, then downgraded. CI lints, migrates an empty database, checks
the expected table set, and runs the suite.
