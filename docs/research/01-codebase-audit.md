# Codebase Audit — Korean Language Learner

**Audit date:** 2026-10-19  
**Revision:** `ea71df5` (`feat: generate conversations`) with a dirty working tree (modified `.cursor/rules/*.mdc`, untracked audio files, untracked `docs/`)  
**Scope:** every Python file, template, JS, CSS, migration, config, Makefile, README, requirements, env example, `.gitignore`, cursor rule, and the live SQLite schema/data.  
**Method:** static reading plus read-only inspection of the SQLite database, audio files, installed packages, and repository history. No application requests were made and no OpenAI API calls were issued.

---

## 0. Snapshot

| Item | Finding |
|---|---|
| Code size | 1,856 lines across Python/HTML/JS/CSS |
| App shape | Flask 2.0.1 monolith, one blueprint (`main`), SQLite, server-rendered Jinja + vanilla JS |
| Python | 3.12.4 in `venv`; Flask 2.0.1, Werkzeug 2.0.1, SQLAlchemy 1.4.23, Flask-SQLAlchemy 2.5.1, Flask-Migrate 3.1.0, openai 1.76.0, gunicorn 20.1.0 |
| DB | 13 phrases, 3 conversations, 7 conversation lines; 3 app tables + `alembic_version` |
| Audio | 31 static MP3s in `app/static/audio`; only 16 are referenced by the DB; 15 are orphans (624 KB, 54% of static audio); 23 MP3s are tracked in git (896 KB) |
| Tests | **Zero.** No test files, no pytest/coverage/ruff/mypy in the venv, no CI config |
| Runtime state | `journal_mode=delete`, `foreign_keys=0`, `busy_timeout=0`, `user_version=0` |
| Secrets | `.env` contains a real-looking `sk-...` key at `.env:1`. It is ignored by git (`.gitignore:96`) and was not tracked historically. Treat it as compromised and rotate it. |
| README accuracy | README:17-19 claims “interactive practice exercises” and “progress tracking”; neither exists. README:9 says `gpt-4o`; code uses `gpt-4.1-nano`. |

**Bottom line:** this is an early single-user prototype with two working verbs — translate a phrase with TTS, and generate a short conversation with per-line + merged audio. It is not yet a learning product, and it is not safe to expose publicly in its current form.

---

## 1. Feature inventory and actual learner journeys

### 1.1 What exists

| Capability | Entry point | What actually happens | Limits |
|---|---|---|---|
| Translate English phrase → Korean + audio | `GET /`, form `#phrase-form`, `POST /api/translate` | Validates empty/length, calls OpenAI `gpt-4.1-nano` for a single Korean string, calls `tts-1` voice `onyx`, saves MP3, inserts `Phrase`, returns JSON | English-only input; no alternatives/romanization/grammar; max 500 chars (`validators.py:10`); auto-saves with no confirmation |
| Browse saved phrases | `GET /library`, `GET /api/phrases` | 10/page (HTML), 20/page (API), newest first, inline audio + Repeat | No search, filter, edit, delete, favorite, tag, detail view, date, or export |
| Generate a conversation | `GET /conversations/new`, `POST /api/conversation` | LLM returns title/description/2–4 lines; per-line TTS alternates `onyx`/`nova`; pydub merges with 1.5 s pauses; inserts `Phrase` per line, `Conversation`, `ConversationLine` | 2–4 line count is prompt-only, not enforced; prompt max 200 only client-side; slow synchronous request |
| Browse/view conversations | `GET /conversations`, `/api/conversations`, `/conversations/<id>`, `/api/conversations/<id>` | List with merged audio, detail with merged audio + per-line audio | No edit/delete/regenerate/export; list API includes all lines/phrases and is N+1 |
| Playback | `<audio controls>` + `.repeat-btn` | Native audio, repeat resets `currentTime` and plays | No speed control, loop count, slow mode, shadowing, waveform, or per-syllable playback |
| CLI | `python hangul.py "phrase"` / `make run` | Translate + TTS into `audio_output/` | Duplicates web logic, no DB, no retries, no validation, no conversation support |
| Error pages | `app/errors.py` | HTML error template, JSON for `/api/` paths | Only 400/404/429/500; API 404 is converted to 500 by a broad `except` |
| Internal rate limit | `rate_limit()` decorator | In-memory per-IP counters for translate/conversation | Per-process, unbounded, shared bucket, proxy-blind, no auth |
| Internal translation cache | `@cache_result(86400)` | In-process dict keyed by text | Per-worker, no invalidation, thread races, unbounded |

### 1.2 End-to-end journeys

**J1 — First phrase (happy path).**
1. `GET /` renders `index.html` (`routes.py:50-52`).
2. User submits; JS prevents default, disables the button, shows spinner (`translate.js:7-22`).
3. `POST /api/translate` with `{text}` (`translate.js:25-31`).
4. Server parses JSON, validates length (`routes.py:69-78`, `validators.py:1-13`).
5. `translate_to_korean()` with 24 h in-process cache (`translation.py:13-45`).
6. Filename is sanitized English + 8-char UUID (`routes.py:84-90`).
7. `generate_audio()` streams MP3 to local disk (`audio.py:21-26`).
8. `Phrase` row committed (`routes.py:100-106`); response is `to_dict()`.
9. JS writes English/Korean with `textContent`, sets audio `src`, loads, and tries to autoplay (`translate.js:40-55`).

**J2 — Library.**
`GET /library?page=N` paginates 10 newest phrases (`routes.py:55-62`), renders cards with audio and Repeat (`library.html:8-17`). There is no search, sort, date, detail page, edit, delete, or “practice this” action.

**J3 — Conversation.**
1. `GET /conversations/new` renders the prompt form (`new_conversation.html`).
2. JS posts `{prompt}` (`new_conversation.js:22-26`).
3. Server requires a non-empty prompt but does **not** enforce its length or type (`routes.py:147-152`).
4. `generate_conversation_scenario()` asks for JSON with title/description/lines (`translation.py:64-101`).
5. For each line: TTS to `conv_<text>_<uuid>.mp3`, insert `Phrase`, `flush()` for id, build `ConversationLine` (`routes.py:167-206`).
6. Merge all line MP3s into `conversation_<uuid>.mp3` with 1.5 s gaps (`routes.py:208-212`, `audio_merge.py:6-50`).
7. Insert `Conversation`, link lines, commit (`routes.py:215-226`).
8. JS renders the result via `innerHTML` (`new_conversation.js:55-69`).
9. User can later view the conversation in the list/detail pages (`conversations.html`, `conversation_detail.html`).

**J4 — CLI.**
`hangul.py` loads `.env`, translates, and writes to `audio_output/` (`hangul.py:12-16`, `59-77`, `93-110`). It does not use the database, does not retry, and prints errors to stderr.

**J5 — Failure/retry.**
A TTS or merge failure returns 500. Partial MP3s are left on disk; DB rows are normally rolled back by Flask-SQLAlchemy teardown, but there is no explicit rollback or file cleanup. The user retries; new UUID filenames and new rows are created, so duplicates and orphans accumulate. The live DB already shows six variants of the same “Hi, I’d like two beers” line and 15 unreferenced static MP3s.

**J6 — What a learner cannot do.**
No account, no saved progress, no review queue, no quiz, no SRS, no Hangul lesson, no pronunciation recording/feedback, no grammar explanation, no level/placement, no goal/streak, no Korean→English mode, no Korean text input/IME practice, no edit/delete/export, no PWA/offline, no search. This is the gap between the README’s claims and the code.

---

## 2. Architecture assessment

### 2.1 App factory and blueprints

`create_app()` exists (`app/__init__.py:14-44`) and does four things: load config, ensure the audio directory, init SQLAlchemy, register one blueprint and error handlers. It is directionally correct but incomplete:

- **Config is selected by string** from `config[config_name]` (`app/__init__.py:16`); an unknown `FLASK_ENV` raises `KeyError` with no validation.
- **`load_dotenv()` runs at import** (`app/__init__.py:8`), making environment loading a side effect of importing the package.
- **The audio directory write probe runs on every app creation** (`app/__init__.py:20-29`) using a fixed `test_write.txt`. Two gunicorn workers can race (one removes the file while the other writes/removes it), and a read-only filesystem crashes startup.
- **Flask-Migrate is initialized in `run.py:11`, not in the factory.** Any other WSGI entrypoint or test app lacks `flask db` and migration wiring.
- **Only one blueprint** (`main`) mixes HTML pages and JSON APIs (`routes.py:14`). There is no API versioning, no auth blueprint, no service boundary.
- **No `TestingConfig`**, no config validation, no secret loading abstraction.
- **`run.py` builds a module-level app** (`run.py:8`), so `gunicorn run:app` inherits `debug=True` unless `FLASK_ENV` is explicitly production. The README never documents a production entrypoint.

### 2.2 Models and data layer

Three models, all global and anonymous:

- `Phrase` (`models.py:6-25`): `english_text` indexed but **not unique** (`models.py:9`), `korean_text`, `audio_path` as a URL string, naive `created_at`, unused `uuid`.
- `Conversation` (`models.py:28-53`): title/description/merged `audio_path`, ORM cascade delete-orphan (`models.py:34-40`), but no DB-level FK cascade.
- `ConversationLine` (`models.py:56-75`): `conversation_id`, `phrase_id`, `speaker` string, `order`; no unique `(conversation_id, order)`, no indexes on FKs, no DB `ON DELETE`.

There is **no `User`, `Deck`, `Card`, `Review`, `Attempt`, `Tag`, `Lesson`, `Course`, `Goal`, `Job`, `UsageEvent`, or `AudioAsset` model**. There is no ownership column anywhere. The schema cannot express “whose phrase is this?” or “when was it last reviewed?”. `Conversation.to_dict()` and `ConversationLine.to_dict()` lazy-load relationships (`models.py:52`, `74`), which is the source of the N+1 behavior.

Timestamps use `datetime.utcnow` (`models.py:12`, `33`), which is deprecated in Python 3.12 and stores naive UTC with no timezone. Serialization assumes non-null (`models.py:24`, `51`).

### 2.3 Services and orchestration

`translation.py` and `audio.py` are thin OpenAI wrappers. `audio_merge.py` wraps pydub/ffmpeg. `caching.py` is a home-made dict cache. `validators.py` only checks empty/length.

Problems:

- **OpenAI clients are module-level globals** (`translation.py:7`, `audio.py:7`, `hangul.py:16`), created at import time, with no app lifecycle, no key injection, no timeout, and no `max_retries=0`. Importing the app, running migrations, or collecting tests requires a valid key.
- **Services depend on Flask `current_app`** (`translation.py:4`, `audio.py:4`, `audio_merge.py:3`, `caching.py:4`), so they cannot be unit-tested without an app context.
- **Routes do orchestration, persistence, file naming, TTS, merging, and serialization** (`routes.py:65-117`, `143-235`). There is no service layer for the actual use cases, no repository/unit-of-work, and no transaction boundary abstraction.
- **CLI duplicates the translation prompt** (`hangul.py:19-56`) rather than importing the service, so prompts and models will drift.
- **No provider abstraction.** OpenAI model names, voice names, and response formats are hard-coded (`translation.py:22`, `84`; `audio.py:24`; `hangul.py:23`, `70`).

### 2.4 Background work, caching, rate limiting

- **Background work: none.** LLM, TTS, and ffmpeg all run inside the request (`routes.py:155-226`). A 4-line conversation is 1 LLM call + 4 TTS calls + 1 ffmpeg merge, all synchronous. There is no job table, queue, progress endpoint, SSE, retry policy, or dead-letter handling. Gunicorn’s default sync worker and 30 s timeout will kill long requests.
- **Caching: in-process dict** (`caching.py:8`). It is per-worker, lost on restart, not shared, not thread-safe (check-then-act at `caching.py:28-36`), unbounded, and only cleans expired entries on a miss (`caching.py:38-41`). The key does not include model/prompt version, so changing the translation prompt serves stale results for 24 h. It caches translation only, not TTS, conversations, or HTTP responses.
- **Rate limiting: home-made decorator** (`routes.py:16-47`). One global `request_history` dict, keyed by `request.remote_addr`, with a 60 s sliding list. It is per-process, unbounded (keys are never deleted), not lock-protected, shared across both decorated endpoints, and blind to proxies. `abort(429)` is handled (`errors.py:17-23`), but no `Retry-After`/rate headers are returned.

### 2.5 Error handling

`app/errors.py` registers 400/404/429/500 only. There are no handlers for 401/403/405/413/415, no JSON content negotiation, and no error codes. Broad `except Exception` blocks catch everything (`routes.py:113-117`, `229-235`, `254-256`, `264-266`), including `HTTPException`. The conversation 500 returns `str(e)` to the client (`routes.py:234`), leaking internals. The API detail route converts a legitimate 404 into a 500 (`routes.py:262-266`). There is no request ID, no correlation ID, and no structured error envelope.

### 2.6 Database migrations

There is exactly one migration: `migrations/versions/afc06f678e70_add_conversation_and_conversationline_.py`. It has `down_revision = None` (`:14`) and creates only `conversation` and `conversation_line` (`:21-39`). It **does not create `phrase`**, does not create the `phrase` indexes, and does not baseline the existing database.

The actual schema is produced by `db.create_all()` in `run.py:23` (CLI) and `run.py:30` (startup). Consequences:

- A fresh `flask db upgrade` creates conversation tables referencing a nonexistent `phrase` table; the app then fails when it queries phrases.
- Running `db.create_all()` on a fresh DB creates `phrase` but does not stamp Alembic, so a later `db upgrade` tries to create `conversation` again and fails.
- Future schema changes have no reliable baseline; autogenerate will be noisy or wrong.
- `make db-init` runs `flask db init` (`Makefile:77-78`) even though `migrations/` already exists, so it fails.
- There is no migration test, no downgrade test, and no deploy-time migration step.

### 2.7 Config, secrets, logging, deployment

`config.py` is a simple class hierarchy:

- `SECRET_KEY` defaults to `"dev-key-change-in-production"` (`config.py:8`); `.env` sets a placeholder (`your_secret_key_here`).
- DB URI defaults to a repo-local SQLite file (`config.py:9-11`).
- Audio dir is `app/static/audio` (`config.py:13`), coupling media storage to the web root.
- `MAX_CONTENT_LENGTH` is 10 MB (`config.py:14`), irrelevant today but very large for a text prompt.
- Production logging writes to `app.log` with `maxBytes=10240` and 10 backups (`config.py:35-44`) — 100 KB total, and `RotatingFileHandler` is not multiprocess-safe. All workers write the same file.
- No `ProxyFix`, HTTPS enforcement, secure cookie flags, HSTS, CSP, or security headers.
- No Dockerfile, Procfile, gunicorn config, CI, staging, health check, or migration gate.
- `ffmpeg` is required by pydub but only documented in README/cursor rules, not checked at startup or declared in requirements.

### 2.8 Positive architectural notes

- The app factory and blueprint split are a reasonable starting point.
- SQLAlchemy ORM is used consistently; no raw SQL or string interpolation.
- Filenames are sanitized and UUID-suffixed (`routes.py:84-90`, `174-181`), so path traversal is not evident.
- Jinja autoescaping protects the server-rendered conversation detail/list pages.
- `Conversation.lines` has a cascade and deterministic `order_by`.
- API error handlers exist for the main status codes.
- `.env` and the DB are gitignored; the OpenAI key is not in git history.
- There is a migration scaffold and a Makefile, even if the migration baseline is wrong.

---

## 3. Correctness bugs and failure modes

### B1. OpenAI client initialization at import time — **P0**

`translation.py:7`, `audio.py:7`, and `hangul.py:16` call `OpenAI()` at module import. If `OPENAI_API_KEY` is missing, importing the app raises before Flask can render a helpful error. This also means `flask db upgrade`, `flask init-db`, pytest collection, and any WSGI worker require an API key. The client is not tied to app config, cannot be rotated without a restart, and is not closed. In a preload/fork gunicorn setup, the shared httpx pool is also a concern.

**Fix:** initialize the client in the app factory or a lazy provider; inject it into services; allow a fake client in tests; fail only on the first API call with a clear configuration error.

### B2. No timeouts; retry multiplication — **P0**

The OpenAI SDK defaults are `timeout=600s` and `max_retries=2` (confirmed in `venv/.../openai/_constants.py:9-10`). The app adds its own 3-attempt loop with `time.sleep(2)` (`translation.py:19-59`, `81-114`; `audio.py:21-54`). Worst case is 3 manual attempts × 3 SDK attempts = 9 calls, each potentially waiting 600 seconds. A single stuck request can occupy a worker for a very long time and run up cost. Retries also apply to non-retryable 400/401 errors.

**Fix:** set explicit connect/read timeouts (e.g., 5 s/20 s), `max_retries=0` or 1 at the SDK layer, retry only 429/5xx/timeouts with exponential backoff + jitter, and cap total elapsed time. Move generation to a worker.

### B3. Audio files are outside the DB transaction — **P0**

In `/api/translate`, the MP3 is written at `routes.py:94` and the row is committed at `106`. In `/api/conversation`, each line file is written at `183-185`, the phrase is flushed at `197-198`, and the conversation is committed at `226`. The merge output is written at `211` before the commit at `226`.

If TTS fails on line 3, lines 1–2 MP3s remain; if merge fails, all line MP3s remain; if the commit fails (e.g., SQLite lock), the merged file remains. Flask-SQLAlchemy teardown usually rolls back uncommitted rows, but there is **no explicit `rollback()` and no file cleanup** in any `except` block. Partial files from a failed streaming response are also left behind (`audio.py:23-26`). Retrying creates new UUIDs, so failed work is never reused.

**Fix:** write to a temp/staging directory, commit metadata first or use a job/outbox, and unlink all staged files on failure in a `finally`; add a periodic orphan sweeper. Better: content-addressed object storage with idempotency keys.

### B4. SQLite write lock held across network calls — **P0**

In the conversation loop, `db.session.flush()` (`routes.py:198`) starts a write transaction. The next iteration then performs a network TTS call (`183-185`) while the write lock is still held; the merge and commit happen much later (`211-226`). SQLite is configured with `journal_mode=delete`, `busy_timeout=0`, and `foreign_keys=0` (verified in the live DB). Any concurrent writer gets an immediate `database is locked` error. The app also never enables foreign keys, so DB-level referential integrity is off.

**Fix:** switch to WAL, set `busy_timeout` (e.g., 5000 ms), enable `PRAGMA foreign_keys=ON`, and keep write transactions short: gather all external results first, then insert/commit in one short transaction. For multi-user production, move to PostgreSQL.

### B5. Rate limiter leaks memory, races, and shares buckets — **P1**

`request_history` is a module global (`routes.py:17`). Each new IP adds a key that is never deleted (`29-33`); only that IP’s list is trimmed when it returns. The `len(...) >= limit` check and `append` (`36-41`) are a non-atomic check-then-act, so concurrent threads can exceed the limit. Each gunicorn worker has its own dict, so the effective limit is `workers × limit`. `request.remote_addr` is the proxy address behind nginx unless `ProxyFix` is configured, so all users can share one bucket. Both decorators (translate at `66`, conversation at `144`) use the **same** history dict, so 10 translate calls can block a conversation call even though its limit is 5. Restart resets everything. There is no `Retry-After`.

**Fix:** Flask-Limiter with Redis, per-user + per-IP keys, separate endpoint buckets, atomic increments, proxy-aware client IP, and standard rate-limit headers.

### B6. DOM XSS via `innerHTML` — **P1/P0 for multi-user**

`new_conversation.js:56-69` interpolates `conv.title`, `conv.description`, `line.speaker`, `line.phrase.english_text`, `line.phrase.korean_text`, and `line.phrase.audio_path` into an HTML string and assigns it to `resultDiv.innerHTML` at line 69. These values are LLM-controlled. A prompt-injected response such as `<img src=x onerror=...>` executes in the creator’s session. Today this is mostly self-XSS because the Jinja detail/list pages autoescape and the prompt is user-entered; it becomes stored XSS as soon as any client renders API data this way or conversations are shared. There is no CSP to blunt it.

**Fix:** build nodes with `createElement`/`textContent`; if rich text is ever required, sanitize with DOMPurify on the client and server. Add a strict CSP. Treat all model output as untrusted.

### B7. API 404 becomes 500 — **P1**

`Conversation.query.get_or_404(conversation_id)` raises `NotFound` at `routes.py:262`, immediately caught by `except Exception` at `264`, which returns a 500 at `265-266`. Clients cannot distinguish “missing” from “server broken,” and monitoring gets false 500s.

**Fix:** query with `db.session.get()` and return 404 explicitly, or re-raise `HTTPException` before the broad handler. Add a test for `/api/conversations/999999`.

### B8. N+1 queries and oversized list payloads — **P1**

`Conversation.to_dict()` accesses `self.lines` (`models.py:52`) and each `line.phrase` (`models.py:74`). Both relationships are lazy (`models.py:34-40`, `64`). `/api/conversations` calls `to_dict()` for every item (`routes.py:248`), producing 1 count query + 1 list query + 1 query per conversation for lines + 1 query per line for its phrase. A page of 10 conversations with 3 lines each is roughly 42 queries. `/api/conversations/<id>` has the same issue (`routes.py:263`), and the HTML detail template lazy-loads lines/phrases too (`conversation_detail.html:11-18`). The list API also returns full line/phrase objects when a summary would do.

**Fix:** `selectinload(Conversation.lines).selectinload(ConversationLine.phrase)`; add a `ConversationSummary` serializer; make `lines` opt-in via `?include=lines`.

### B9. Duplicate phrase and TTS generation — **P1**

There is no unique constraint or normalization on `Phrase.english_text` (`models.py:9`). `/api/translate` always inserts a new row and always regenerates TTS (`routes.py:94-106`). The conversation loop always inserts a new `Phrase` and TTS per line (`routes.py:183-198`), even if the exact line already exists. The translation cache is only in-process and only for the LLM call. The live DB/audio already demonstrates the result: six `conv_hi_id_like_two_beers_*` variants for one line, plus 15 unreferenced MP3s.

**Fix:** normalize text (trim, case-fold, collapse whitespace), add a unique key including voice/model, reuse existing phrase/audio, content-hash audio, and add a dedupe/backfill migration.

### B10. Input and model-output validation is far too weak — **P1**

`validate_phrase()` only checks empty and >500 chars (`validators.py:1-13`). The conversation route does not validate prompt length, type, or language (`routes.py:147-152`). The LLM response is only checked for a non-empty `lines` list (`translation.py:95-101`). There is no schema check for:

- title/description type or length (`Conversation.title` is `String(200)`, but SQLite does not enforce it),
- line count (2–4 is prompt-only at `translation.py:75`),
- `speaker` being int 1/2,
- `english_text`/`korean_text` being strings, non-empty, bounded,
- Hangul presence or translation plausibility,
- alternating speakers.

`line.get("speaker", 1)` can be the string `"2"`; `speaker_voices.get(speaker, "onyx")` (`routes.py:161`, `184`) then misses and uses `onyx` for both speakers. Non-string text causes `.strip()` to raise. A response with 50 lines is accepted and billed for 50 TTS calls.

**Fix:** Pydantic/Marshmallow request and response schemas; server-side max prompt (200 chars), max 4 lines, max chars/line, speaker enum, Hangul check; normalize and reject or regenerate invalid output.

### B11. Malformed JSON and wrong content types become 500 — **P1**

`request.get_json()` at `routes.py:69` raises `BadRequest` (400) for malformed JSON and `UnsupportedMediaType` (415) for a non-JSON body. Both are caught by `except Exception` at `113` and returned as a generic 500. The same pattern exists in the conversation route (`147`).

**Fix:** `get_json(silent=True)`, explicit 415/400 responses, and dedicated handlers. Do not use a blanket `except` around parsing.

### B12. Raw exception and user-content leakage — **P1**

The conversation 500 returns `str(e)` to the client (`routes.py:234`). That can include file paths, SDK error details, and model/provider messages. The app logs full user text (`routes.py:81`), raw model output (`translation.py:94`), and full tracebacks (`routes.py:230-232`). Production rotation is only 100 KB (`config.py:35-44`), so useful history is lost quickly.

**Fix:** generic client errors with a request ID; structured logs with redaction; log prompt/response only behind a debug flag with a retention policy.

### B13. Pagination edge cases and incorrect `current_page` — **P2**

`page` is read with `type=int`, defaults to 1, and `paginate(error_out=False)` coerces `<1` to 1. But the API returns the **input** `page`, not the normalized pagination page (`routes.py:135`, `251`). `?page=0` returns items from page 1 with `"current_page": 0`; `?page=999` returns an empty list with `"current_page": 999` and `"pages": 2`. Ordering uses only `created_at.desc()` (`routes.py:59`, `126`, `243`, `273`), so ties can cause row drift across pages. `per_page` is fixed and unvalidated.

**Fix:** order by `(created_at.desc(), id.desc())`, return `pagination.page`, clamp or 404 out-of-range pages, and cap/validate `per_page`.

### B14. Speaker type and voice mapping — **P1**

Covered in B10, but worth isolating: `speaker_voices = {1: "onyx", 2: "nova"}` (`routes.py:161`) assumes integer keys. JSON `"speaker": "2"` yields `onyx`, so two-speaker conversations can sound like one speaker. `f"Speaker {speaker}"` (`routes.py:203`) can also produce `"Speaker {'id': 2}"` or similar if the model deviates.

**Fix:** cast and validate `speaker` to `int` in `{1, 2}` before use.

### B15. Null timestamps and `None` descriptions — **P2**

`Phrase.to_dict()` calls `self.created_at.isoformat()` (`models.py:24`); `Conversation.to_dict()` does the same (`models.py:51`). A legacy row with `created_at NULL` (the column is nullable) raises and becomes a 500. Templates render `{{ conversation.description }}` (`conversation_detail.html:5`, `conversations.html:16`); if it is `None`, Jinja renders the literal string “None”. Timestamps are naive UTC (`models.py:12`, `33`) with no timezone conversion.

**Fix:** non-null server defaults, timezone-aware UTC, defensive serializers, and `{{ x or '' }}` in templates.

### B16. Autoplay listener race — **P2**

`translate.js` sets `audio.src`, calls `audio.load()` (`44-46`), then attaches a `canplaythrough` listener (`52-55`). The event can fire before the listener is attached, especially with a cached file, so autoplay may never run. The `play()` promise rejection is caught, but the listener may be lost.

**Fix:** attach the listener before setting `src`, or call `play()` from a `loadeddata`/`canplay` handler with a single-shot guard.

### B17. Library lazy-loading is dead code — **P2**

`library.js:4-11` looks for `audio[data-src]`, but `library.html:13` and the other templates render `<audio src="...">` directly. The scroll/resize listeners run on every event for no benefit. This is misleading “optimization” code.

**Fix:** either add `data-src` and use `IntersectionObserver`, or remove the file and listeners.

### B18. Null dereference in conversation repeat handler — **P2**

`new_conversation.js:75-77` sets `audio.currentTime = 0` before checking `if (audio)`. If the closest `.audio-player` has no audio, this throws. The global handler in `app.js:41-47` has the same assumption.

**Fix:** null-check before mutating.

### B19. App factory writes a test file with a fixed name — **P2/P1 ops**

`app/__init__.py:23-26` creates `test_write.txt` in the live audio directory on every app creation. Concurrent workers can race; read-only deployments fail; tests touch real media. This is an import-time side effect disguised as a health check.

**Fix:** remove the probe; use a storage adapter that checks/creates the directory idempotently, and test it explicitly.

### B20. Broken migration baseline — **P1**

Detailed in §2.6. The live DB has `alembic_version=afc06f678e70` but `phrase` was created by `create_all()`. A new environment cannot be built reliably from migrations, and future migrations have no trustworthy baseline. `make db-init` is also wrong.

**Fix:** create a baseline migration for `phrase` and its indexes, stamp existing DBs, remove `create_all()` from production startup, run `flask db upgrade` in deploy, and add an empty-DB migration test.

### B21. Cache invalidation and concurrency — **P2**

`caching.py` keys only on function name + positional args (`18-24`). It does not include the model, prompt version, or provider. Two concurrent misses both call OpenAI and overwrite each other (`28-36`). Entries are only removed when a miss triggers cleanup (`38-41`), so a hot cache can grow without bound. There is no max size or metrics.

**Fix:** Redis with versioned keys, TTL, max memory policy, and single-flight/locking. Include model/prompt version in the key.

### B22. Duplicate `Migrate` ownership — **P2**

`Migrate(app, db)` lives in `run.py:11`, not in `create_app()`. Any test app or alternate entrypoint does not get migration commands. This is a structural cause of B20.

### B23. Static audio orphaning — **P1 evidence**

The live tree has 31 static MP3s, 16 DB references, and 15 orphans totaling 624 KB (54% of static audio). The six `conv_hi_id_like_two_beers_*` files are repeated generations of one line. This is direct evidence for B3 and B9. There is no cleanup command, no reference check, and no lifecycle policy.

### B24. CLI drift — **P2**

`hangul.py` reimplements translation and TTS (`19-77`) with a separate model/prompt and no retry/validation. README says `gpt-4o`; code says `gpt-4.1-nano`. The CLI is not a thin client over the same services, so fixes will diverge.

---

## 4. Learner-experience gaps

### 4.1 No learning loop

There is no review queue, no SRS scheduler (SM-2/FSRS), no flashcard state, no attempt history, no correctness signal, no mastery estimate, and no daily plan. A user can generate content but cannot **study** it. The only interaction is “play audio again.”

### 4.2 No Hangul/alphabet onboarding

There is no alphabet lesson, syllable block trainer, stroke order, reading drill, or romanization. A beginner is dropped into English→Korean translation with no path to literacy. Korean text is displayed, but not taught.

### 4.3 No pronunciation feedback

Output is TTS only (`audio.py:23-26`). There is no microphone capture, ASR, forced alignment, scoring, waveform comparison, or feedback on the learner’s speech. “Repeat” only replays the model voice.

### 4.4 No grammar or vocabulary explanation

The translation prompt asks for one string (`translation.py:27`). There is no lemma, part of speech, particle breakdown, honorific/register note, literal gloss, example sentence, or grammar note. The user cannot learn **why** the Korean is what it is.

### 4.5 No leveling or placement

No CEFR/TOPIK/ILR level, no difficulty metadata on phrases or conversations, no placement test, no progression. Every generated sentence is equally “level-less.” Conversation length is prompt-only 2–4 lines.

### 4.6 No goals, streaks, or motivation

No daily target, streak, XP, achievement, reminder, or progress chart. No sense of return reason.

### 4.7 No personalization or adaptivity

There is no user model at all, so no interests, history, error patterns, preferred topics, voice, speed, or difficulty adaptation. The only “personalization” is the free-text prompt.

### 4.8 English-first, one-direction workflow

The entire UI is English (`base.html:2`), forms ask for English (`index.html:7-18`, `new_conversation.html:7-20`), and the only translation direction is EN→KO. There is no KO→EN, no bilingual mode, no Korean-first prompt, no source-language detection, and no way to practice producing Korean from a meaning. For a learner, this is a lookup tool, not a practice tool.

### 4.9 Audio-only output, limited playback

The learner gets text + a single MP3. There is no romanization, slow/normal speed toggle, repeat count, loop, shadowing mode, pause-after-line, waveform, or per-word highlighting. `preload="none"` is good for bandwidth but there is no prefetch strategy. Merged conversations have a fixed 1.5 s pause (`routes.py:211`) with no user control.

### 4.10 Conversation limitations

Generated conversations cannot be edited, deleted, regenerated, lengthened, shortened, re-voiced, exported, or role-played. There is no “hide Korean,” “hide English,” “play only my line,” or “respond as speaker 2” mode. Line count, speakers, voices, and pause are hard-coded or prompt-only (`routes.py:161`, `211`; `translation.py:64`). There is no grammar or vocabulary extraction from the conversation.

### 4.11 Organization and content management

No search, filter, tags, decks, favorites, notes, edit, delete, duplicate detection, export, or date display. The library is an append-only feed. There is no content pipeline, curation, or quality review; every phrase is machine-generated and immediately public.

### 4.12 Mobile, PWA, keyboard, IME

Responsive CSS exists (`style.css:25-40`) and a viewport tag (`base.html:5`), but there is no manifest, service worker, offline mode, install prompt, push notification, or app shell. The nav has no hamburger and can overflow at 320 px. There is no Korean keyboard/IME practice, no input method support, and no keyboard shortcuts beyond Space/Enter on Repeat (`app.js:49-59`). Forms have no `action`/`method`, so they do nothing without JavaScript.

### 4.13 Accessibility

- `html lang="en"` (`base.html:2`) while Korean text is unmarked; screen readers will use an English voice for Korean. Add `lang="ko"` spans.
- Loading containers are `aria-hidden="true"` (`index.html:24`, `new_conversation.html:25`) while containing the only “Translating…” status text; that text is hidden from assistive tech. `aria-live` is on the form, not the status. Use `role="status"`/`aria-live` and do not hide it.
- Errors auto-hide after 5 s (`app.js:33-37`, `new_conversation.js:50-52`) and focus is moved but not restored; screen-reader users can miss them.
- `outline: none` on focus for nav/buttons/inputs (`style.css:84`, `140`, `164`); only a background change remains. WCAG 2.4.7 risk.
- White text on `--accent: #ff8c42` (`.repeat-btn`, `style.css:172-180`) is roughly 2.9:1, below WCAG AA 4.5:1 for normal text.
- No skip link despite `main id="main-content"` (`base.html:43`).
- No `prefers-reduced-motion` handling for the spinner/card hover (`style.css:99`, `207-223`).
- Audio elements have no accessible names describing the phrase; every Repeat button has the same label.
- No dark mode, text-size control, or high-contrast mode.

### 4.14 Trust and learning quality

There is no confidence score, alternative translation, human review, correction path, or explanation of likely errors. Machine translation errors are presented as authoritative. The app does not distinguish “translation” from “verified learning content.”

---

## 5. Security, privacy, and operations

| Risk | Evidence | Impact |
|---|---|---|
| **No authentication/authorization** | No `User` model, no `user_id`, no login/session, all routes public (`routes.py:50-287`) | Anyone can read all phrases/conversations, generate content, and burn the owner’s OpenAI credits. All data is global. |
| **CSRF** | Flask-WTF is installed (`requirements.txt:5`) but `CSRFProtect` is never initialized; no tokens/origin checks | JSON-only parsing incidentally blocks classic cross-site form posts, but there is no defense-in-depth. Any future form/session auth would be vulnerable. |
| **XSS** | `new_conversation.js:56-69`; no CSP | LLM-controlled HTML executes in the DOM. Self-XSS today, stored/client-side XSS as soon as API data is rendered elsewhere. |
| **Secret handling** | `.env:1` contains a real-looking `sk-...`; `SECRET_KEY` fallback at `config.py:8`; `.env` placeholder at `.env:7` | Key is in the working tree and may be in backups/shell history. Rotate it. Default secret undermines future sessions. |
| **Debug exposure** | `run.py:7-8` defaults to development; `run.py:34` enables debug/reloader | If bound to `0.0.0.0`, the Werkzeug debugger is an RCE risk. Production config is not the default. |
| **Rate-limit bypass** | Per-process dict (`routes.py:17`), `remote_addr` (`25`), shared bucket, restart reset, no auth | Effective limits scale with worker count; proxies collapse all users into one IP; attackers can rotate IPv6 or restart. |
| **Input validation** | `validators.py:1-13`; conversation route `147-152`; LLM output `95-101` | Oversized prompts/lines, wrong types, prompt injection, and unbounded TTS cost. |
| **SQLite concurrency/DoS** | `journal_mode=delete`, `busy_timeout=0`, `foreign_keys=0`; long write transaction `routes.py:198-226` | Concurrent requests can cause immediate lock errors; a slow TTS call holds the write lock. |
| **Static audio exposure** | `app/static/audio`; 23 files committed; no auth/signed URLs | Audio content is public and permanent; repo bloat; no access control or deletion. |
| **Error/log leakage** | `routes.py:234`, `translation.py:94`, `routes.py:81` | Internal paths/provider errors returned to clients; user text and raw model output stored in logs. |
| **Cost controls** | No quota/budget/user cap; no TTS cache; duplicates; 9-attempt retries; no line/char cap | A public instance is an open OpenAI proxy. Spend can grow without bound. |
| **Dependency risk** | Flask 2.0.1/Werkzeug 2.0.1/SQLAlchemy 1.4.23/gunicorn 20.1.0/openai 1.76.0 (`requirements.txt:1-10`) | All are old/EOL; gunicorn 20.1.0 predates the 22.0.0 request-smuggling fix (CVE-2024-1135). No pip-audit/CI. |
| **Privacy/data lifecycle** | Text sent to OpenAI; audio stored indefinitely; no delete/export; no consent/notice | Learner content and voice data are retained with no user control. |
| **Ops** | No health/metrics/alerts/backups/CI/container; ffmpeg undeclared; `make clean` deletes DB/audio (`Makefile:64-72`) | No safe deploy or recovery path. |

**Not found:** SQL injection (ORM throughout), path traversal (filename sanitization at `routes.py:84-90`/`174-181`), unsafe deserialization, or open redirects. These are genuine positives.

---

## 6. Test coverage and recommended strategy

### 6.1 Current state

- **Zero tests.** No `tests/`, no `pytest`, no `coverage`, no CI, no fixtures.
- No test configuration (`TestingConfig`), no in-memory DB, no temp audio dir.
- Import-time OpenAI clients make tests fail without a key.
- The audio write probe (`app/__init__.py:20-29`) touches the real static directory.
- The most failure-prone code — rate limiter, cache, partial generation, merge, 404 behavior, pagination, XSS — is entirely untested.

### 6.2 Test strategy

**Prerequisites (refactor for testability):**

1. Add `TestingConfig` with `TESTING=True`, in-memory/temp SQLite (or Postgres testcontainer), temp audio dir, dummy `OPENAI_API_KEY`, and `WTF_CSRF_ENABLED=False` for API tests plus dedicated CSRF tests.
2. Move OpenAI client creation into the factory/lazy provider; inject `translation_client`, `tts_client`, `clock`, `storage`, and `queue`.
3. Inject a fake clock into the rate limiter and cache, and a fake storage abstraction into audio/merge.
4. Add `pytest`, `pytest-cov`, `pytest-flask`, `responses`/`respx`, `freezegun`, `Playwright`, `axe-core`, `ruff`, `mypy`, `pip-audit`.

**Test layers:**

| Layer | Tools | Cases |
|---|---|---|
| Unit | pytest | validators; filename sanitizer; cache key/expiry; rate limiter with fake clock + concurrent threads; schema parsing; merge failure; cost calculation |
| API/route | pytest + Flask test client | 200/400/404/415/429/500; JSON shape; pagination (0, negative, huge, ties); API 404 not 500; oversized/non-string inputs; malformed JSON |
| Integration | pytest + fake OpenAI/HTTP server | translation success/invalid JSON/missing key/truncation; TTS failure on line N; retry counts; timeout; merge failure; assert **zero DB rows and zero orphan files** after failure |
| DB/migration | pytest + Alembic | empty DB → upgrade → expected schema; downgrade; FK/unique constraints; duplicate prevention; SQLite lock/WAL behavior; Postgres parity |
| Frontend | Vitest + jsdom | `renderConversation` with `<img onerror>` payload; assert no HTML injection; audio/repeat handlers; null audio |
| E2E | Playwright | first phrase, library pagination, conversation create/view, error/retry, mobile viewport |
| Accessibility | axe + manual | live-region announcements, Korean `lang`, focus order, contrast, keyboard-only |
| Security | pytest/ZAP | XSS payloads, CSRF content types, rate-limit bypass, authz (once added), secret/config checks |
| Load | k6/Locust | concurrent conversation creation; p95 latency; lock errors; worker saturation |
| Quality eval | golden set | 50–100 curated EN→KO phrases with human reference; schema validity; Hangul presence; conversation line count/speaker alternation; TTS intelligibility spot checks |

**Coverage targets:** 80% of service/util code, 70% overall; 100% of failure paths that create files or DB rows. Add a CI gate that fails on orphan files after the failure-injection suite.

---

## 7. Technical debt ranking and target architecture

### 7.1 Prioritized debt table

| Priority | Lens | Finding | Evidence | Impact | Effort |
|---|---|---|---|---|---|
| **P0** | Security/Product | No auth, no user model, all data global | `models.py`, `routes.py:50-287` | Critical if public; blocks any real product | L (2–4 wk) |
| **P0** | Reliability | OpenAI clients at import; no key → app/tests/migrations fail | `translation.py:7`, `audio.py:7`, `hangul.py:16` | App cannot boot in clean env; blocks CI | S (1–2 d) |
| **P0** | Reliability/Cost | 600 s default timeout + 3× manual × 2 SDK retries | `translation.py:19-59`, `audio.py:21-54`; SDK constants | Worker hangs, duplicate spend | S (1–2 d) |
| **P0** | Data integrity | Files written outside DB transaction; no cleanup | `routes.py:94-106`, `183-226`; `audio_merge.py:47` | Orphan audio, partial conversations | M (3–5 d) |
| **P0** | Data integrity | SQLite write lock across TTS; no WAL/busy_timeout/FK | `routes.py:198-226`; live pragmas | `database is locked`; corruption risk | M (2–4 d) |
| **P0** | Security | DOM XSS via `innerHTML` | `new_conversation.js:56-69` | Script execution; future stored XSS | S (1 d) |
| **P0** | Security/Ops | Live-format API key in `.env`; weak/default secret; debug default | `.env:1`, `.env:7`, `config.py:8`, `run.py:7-34` | Credential/cost compromise; debugger RCE risk | S (hours) |
| **P0** | Engineering | Zero tests/CI | repo-wide | No regression safety; every change is risky | M (1–2 wk) |
| **P0** | Product | No learning loop/SRS/onboarding | no models/routes | Not a learning product | XL (months) |
| **P1** | Reliability | Rate limiter leak/race/per-worker/shared bucket/proxy-blind | `routes.py:17-47`, `66`, `144` | Trivial bypass; shared limits | S/M (2–4 d) |
| **P1** | Data | Migration baseline missing `phrase`; `create_all` masks it | migration file, `run.py:23,30` | Fresh deploy/migrations broken | M (3–5 d) |
| **P1** | Performance | N+1 + heavy conversation list payload | `models.py:52,74`; `routes.py:248,263` | Query blowup as data grows | S (1–2 d) |
| **P1** | Correctness | No server/LLM schema validation | `validators.py:1-13`; `routes.py:147-171`; `translation.py:95-101` | 500s, wrong voices, runaway cost | S (2–3 d) |
| **P1** | Cost/Data | Duplicate phrases/TTS | `routes.py:100-106`, `192-198`; `models.py:9` | 54% orphan audio already; wasted spend | M (3–5 d) |
| **P1** | Correctness | API 404 → 500; raw error leakage | `routes.py:262-266`, `229-235` | Broken clients; info leak | S (hours) |
| **P1** | UX/Scale | No background jobs/progress; sync TTS/merge | `routes.py:155-226` | Timeouts, poor UX, worker exhaustion | L (1–2 wk) |
| **P1** | Security | No CSRF/security headers/CSP | no `CSRFProtect`; no `after_request` | Defense-in-depth gap | S (1–2 d) |
| **P1** | Privacy/Ops | Raw prompt/user text in logs; tiny rotation; multiprocess unsafe | `routes.py:81`, `translation.py:94`, `config.py:35-44` | PII leakage; lost logs | S (1–2 d) |
| **P1** | Ops | Public/committed static audio; no lifecycle | `app/static/audio`; 23 tracked files | Content leak, repo bloat | M (3–5 d) |
| **P1** | Accessibility | Korean `lang` missing, hidden loading, focus/contrast issues | `base.html:2`; `index.html:24`; `style.css:84,140,164,172-180` | Unusable for screen-reader/low-vision learners | M (3–5 d) |
| **P1** | Dependencies | EOL Flask/Werkzeug/SQLAlchemy/gunicorn; no audit | `requirements.txt:1-10` | Known CVEs; no patches | M (3–5 d) |
| **P2** | Correctness | Pagination `current_page`/tie ordering | `routes.py:57-61,123-135,241-251` | Confusing/duplicated rows | S (hours) |
| **P2** | UX | Dead lazy-load; autoplay race; null deref | `library.js:4-11`; `translate.js:44-55`; `new_conversation.js:75-77` | Broken optimizations | S (hours) |
| **P2** | Data | Null timestamps/descriptions; naive UTC | `models.py:12,24,33,51` | 500s / “None” UI | S (hours) |
| **P2** | Docs/Ops | README false claims; `make db-init` wrong; destructive `clean` | `README.md:17-19`; `Makefile:64-72,77-78` | Trust and operator errors | S (hours) |
| **P2** | Product | No search/edit/delete/export/tags | routes/templates | Limited utility | L (2–3 wk) |
| **P2** | Product | No PWA/offline/mobile app shell | no manifest/SW | Poor mobile retention | L (3–4 wk) |
| **P2** | UX | No dark mode/reduced motion/font controls | `style.css` | Polish/accessibility | S (1–2 d) |

### 7.2 Target architecture

Keep a **modular monolith** and add a worker. Do not split into microservices yet.

```
Browser / PWA
   │  Jinja + HTMX (or Next.js PWA)
   ▼
Flask app factory ── /web  /api/v1  /auth
   │  authn/authz, CSRF, rate limit, request validation, idempotency
   ▼
Domain services
   TranslationService · SpeechService · ConversationService
   ReviewService (FSRS) · CurriculumService · ProgressService · MediaService
   ▼
PostgreSQL  +  Redis  +  S3/R2
   │            │          │
   │            │          └─ audio objects, signed URLs, content hashes
   │            └─ cache, rate limiter, queue, locks
   └─ users, content, cards, reviews, jobs, usage events
   ▼
Worker (RQ/Celery/Arq)
   LLM → TTS → merge → upload → mark job done
   retries/backoff/idempotency/dead-letter/cost metering
   ▼
Observability: structured logs + request IDs, Sentry, OpenTelemetry/Prometheus, cost dashboards
```

**Data model to add:**

`User`, `Profile`, `Course`, `Lesson`, `Lexeme/Phrase`, `Translation`, `AudioAsset`, `Deck`, `Card`, `ReviewState`, `ReviewLog`, `Conversation`, `ConversationLine`, `Attempt`, `Goal`, `Streak`, `Tag`, `Job`, `UsageEvent`.

Key fields: `user_id` on all learner data; normalized text; `romanization`; `part_of_speech`; `grammar_notes`; `difficulty`/`level`; `audio_hash`; `voice`/`model`/`speed`; `due_at`; `stability`/`difficulty`/`retrievability` (FSRS); `created_at`/`updated_at` in UTC; soft delete; unique constraints on `(user_id, normalized_text)` and `(conversation_id, order)`.

**Key architectural rules:**

- All LLM/TTS/merge work is async and idempotent; API returns `202 + job_id`; client polls or subscribes via SSE.
- All media lives in object storage, content-addressed; DB stores keys, not public URLs; signed/authenticated playback.
- All inputs/outputs are schema-validated; all model output is untrusted.
- All writes are short transactions; external calls happen outside them.
- All caches/rate limits are Redis-backed and versioned.
- All learner data is user-scoped; every query includes `user_id`.
- Every expensive call records provider, model, tokens/characters, cost, latency, and user/job.

### 7.3 Realistic roadmap

**Phase 0 — Safety (1–2 weeks).** Rotate the key; remove import-time clients; add timeouts/retry policy; fix XSS; add auth gate (even a single-user password) or bind to localhost only; fix 404/validation; add temp-file cleanup; enable WAL/busy_timeout/FK; add pytest + CI; fix migration baseline.

**Phase 1 — Platform (4–6 weeks).** Postgres + Redis + worker; user accounts; job table/progress; object storage; API v1; Flask-Limiter; CSRF/CSP/security headers; structured logs/metrics; migration/deploy pipeline.

**Phase 2 — Learning loop (8–12 weeks).** Hangul onboarding; placement; FSRS review queue; phrase/card model; review UI; goals/streaks; progress dashboard; conversation role-play; edit/delete/export; content curation.

**Phase 3 — Adaptive product (quarter 2+).** Pronunciation capture/scoring; adaptive difficulty; personalized topics; PWA/offline; analytics; cost optimization; quality evals; possibly mobile app.

**Success metrics:** time-to-first-phrase < 2 min; D1/D7 retention; reviews/day; phrase retention at 30 days; cost per active learner; p95 cached translation < 2 s; p95 conversation job < 20 s; error rate < 1%; orphan audio count = 0; accessibility audit pass.

---

## Appendix A — Endpoint inventory

| Method | Path | Auth | Purpose | Notes |
|---|---|---|---|---|
| GET | `/` | none | New phrase page | `routes.py:50` |
| GET | `/library` | none | Phrase list, 10/page | `routes.py:55` |
| POST | `/api/translate` | none | Translate + TTS + save | rate limit 10/min; `routes.py:65` |
| GET | `/api/phrases` | none | Phrase list JSON, 20/page | `routes.py:120` |
| POST | `/api/conversation` | none | Generate conversation + audio | rate limit 5/min; `routes.py:143` |
| GET | `/api/conversations` | none | Conversation list JSON | N+1; `routes.py:238` |
| GET | `/api/conversations/<id>` | none | Conversation detail JSON | 404→500; `routes.py:259` |
| GET | `/conversations` | none | Conversation list HTML | `routes.py:269` |
| GET | `/conversations/<id>` | none | Conversation detail HTML | `routes.py:279` |
| GET | `/conversations/new` | none | New conversation form | `routes.py:285` |
| GET | `/static/audio/*.mp3` | none | Audio files | public; 31 files |

## Appendix B — Live schema and evidence

```sql
CREATE TABLE phrase (
  id INTEGER PRIMARY KEY,
  uuid VARCHAR(36) UNIQUE,
  english_text VARCHAR(500) NOT NULL,
  korean_text VARCHAR(500) NOT NULL,
  audio_path VARCHAR(200) NOT NULL,
  created_at DATETIME
);
CREATE INDEX ix_phrase_created_at ON phrase (created_at);
CREATE INDEX ix_phrase_english_text ON phrase (english_text);

CREATE TABLE conversation (
  id INTEGER PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  audio_path VARCHAR(200) NOT NULL,
  created_at DATETIME
);
CREATE INDEX ix_conversation_created_at ON conversation (created_at);

CREATE TABLE conversation_line (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES conversation(id),
  phrase_id INTEGER NOT NULL REFERENCES phrase(id),
  speaker VARCHAR(20) NOT NULL,
  "order" INTEGER NOT NULL
);
CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY);
```

Evidence queries used:

- `sqlite3 korean_learner.db '.schema'`
- `pragma journal_mode; pragma foreign_keys; pragma busy_timeout;`
- Counts: 13 phrases, 3 conversations, 7 lines.
- Audio reference audit: 31 static MP3s, 16 referenced, 15 orphans (624,000 bytes / 1,154,340 total).
- Duplicate filename audit: six `conv_hi_id_like_two_beers_*` variants.
- `git ls-files 'app/static/audio/*' | wc -l` → 23; `du -ch` → 896 KB.
- `find . -iname '*test*'` → none.
- `venv/bin/pip list` → no pytest/coverage/ruff/mypy.
- Python syntax parse of every project `.py` file → all OK.

## Appendix C — What is done well

- Clear separation of `app/services`, `app/utils`, templates, and static assets.
- App factory and blueprint scaffold are present.
- ORM everywhere; no raw SQL injection surface.
- Filename sanitization + UUID suffix; no path traversal observed.
- Jinja autoescaping on server-rendered pages.
- Cascade/order on conversation lines.
- Error handlers for the main status codes.
- `.env` and DB are ignored by git; key was not committed.
- Basic responsive CSS, labels, `aria-live` regions, and keyboard Repeat support show good intent.
- A migration scaffold and Makefile exist, even though the baseline needs correction.

---

## Executive summary

Korean Language Learner is a 1,856-line Flask prototype, not yet a learning product. It has two working verbs: translate an English phrase to Korean with TTS, and generate a short conversation with per-line and merged audio. A learner can create phrases, browse a library, generate conversations, and replay audio. That is the entire loop. There is no account, no review queue, no SRS, no Hangul onboarding, no pronunciation feedback, no grammar explanation, no leveling, no goals or streaks, and no personalization. The README’s claims of practice exercises and progress tracking are unimplemented.

The happy path works for one local user with a valid OpenAI key, but the engineering is fragile. OpenAI clients are created at import, so the app, migrations, and tests fail without a key. The SDK’s 600-second timeout and retries are multiplied by manual retries. TTS and ffmpeg run synchronously inside requests, while SQLite holds a write lock across network calls with `busy_timeout=0`. Audio files are written outside the database transaction, leaving 15 of 31 static MP3s orphaned (624 KB, 54%) and six duplicate variants of one line. Conversation rendering uses `innerHTML` on LLM output, creating a DOM XSS sink. The rate limiter is an unbounded, thread-unsafe, per-process dict shared across endpoints and blind to proxies. API 404s become 500s, conversation lists trigger N+1 queries, and the migration baseline omits the `phrase` table. There are zero tests and no CI.

The highest-leverage next steps are unglamorous: rotate the exposed key, remove import-time clients, add timeouts and async jobs, make media writes transactional and cleanable, fix XSS, add auth/data isolation, repair the migration baseline, and build a test/CI safety net. Only then should the product invest in the actual learning loop: Hangul onboarding → placement → FSRS review → conversation practice → progress and adaptive difficulty.
</subagent>