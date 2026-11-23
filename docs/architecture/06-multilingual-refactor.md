# 06 — Multilingual Refactor + Real-Time AI Teacher

**Status:** Architecture audit and target design. No application code changed.
**Scope:** Flask 2.0.1 / Flask-SQLAlchemy 2.5.1 / SQLAlchemy 1.4.23 / Alembic (Flask-Migrate 3.1) app “Kiku”, currently Korean-only, ~11.8k LOC Python, 195 tests.
**Method:** Read the actual code. Every structural claim below has a `file:line` reference. I did not infer behavior from filenames or docs.

---

## 0. Verdict in one page

Kiku is not “Korean with a few strings.” Korean is a load-bearing assumption in five independent layers:

1. **The schema names the language.** `item.korean`, `item.english`, `phrase.korean_text`, `speech_attempt.target_text`, `scene_session.scene_slug`, and `uq_item_content` have no language dimension (`app/models.py:15-16, 96-104, 218, 254, 282`).
2. **Curriculum is Python modules imported directly by routes.** `hangul_data.py` is 1,485 lines and `scene_data.py` 467 lines; both are imported at module import time (`app/learning/routes.py:26, 54`; `app/learning/scenes.py:11`), so a second language means editing core route imports.
3. **AI providers are singletons with Korean baked into prompts and schemas.** The translation prompt returns `korean_translation` (`app/services/translation.py:73-77, 49`); the speech provider sends `language="ko"` and normalizes only `[0-9A-Za-z가-힣]` (`app/services/speech.py:26-28, 84`); Pydantic validators require Hangul (`app/utils/schemas.py:25-27, 62-69, 100-105`).
4. **The UI and URLs are Korean feature pages.** `/learn/hangul`, `/learn/sound-gym`, `lang="ko"`, `ko-KR` in five JS files, Korean copy in 20+ templates, and a PWA named “Kiku — Korean.”
5. **Tests and migrations encode Korean as truth.** 195 tests assert `/learn/hangul`, `안녕하세요`, `커피`, `korean_text`, and Hangul-only rejection; the migration chain builds `item(korean, english)` and the CI gate asserts that exact schema.

**The good news:** the FSRS scheduler (`app/learning/scheduler.py:42-97`), review-card uniqueness (`app/models.py:135-141`), media staging (`app/utils/media.py:25-74`), lazy OpenAI client (`app/services/ai.py:57-95`), and service-extension pattern (`app/__init__.py:300-304`) are language-neutral and reusable. The refactor is a **schema + content + service-boundary refactor**, not a rewrite.

**Design position:**

- One `item` table with `language_id` + child `item_form` / `item_gloss` / `dictionary_entry` rows. **Do not** create per-language tables. FSRS is per `(user, item, skill)` and must stay that way.
- A `LanguagePack` protocol is the single source of linguistic behavior. DB stores language metadata and content; code owns normalization, tokenization, romanization, validation, ASR/TTS profiles, level scale, and curriculum source.
- AI services become provider protocols with a per-app service registry, preserving the existing `current_app.extensions[...]` and lazy-client patterns. Generated content is always constrained to DB item IDs and validated per pack before persistence.
- Real-time teacher is a server-owned session with server-minted ephemeral tokens, persisted turns, and an allowlisted tool router. Drills return to FSRS through existing `ReviewCard` rows, not a parallel scheduler.
- Ship in 8 phases. **Phase 1 is additive-only and zero-user-visible-risk**: new tables, nullable columns, backfill `language='ko'`, no route/template/read changes. Contract the old columns only after one release of dual-write.

---

## 1. Coupling inventory

### 1.1 Severity key

| Severity | Meaning |
|---|---|
| **BLOCKER** | Prevents a second language from being stored/served correctly, causes cross-language collisions, or makes core routes import Korean-only data. |
| **NEEDS-PARAMETERIZATION** | Works for one language but must be pack/config/DB-driven before a second language ships. |
| **COSMETIC** | Naming, copy, CSS class, DB filename; fix opportunistically. |

### 1.2 Persistence layer (`app/models.py`, migrations)

| # | Location | Korean assumption | Severity | Target |
|---|---|---|---|---|
| 1 | `app/models.py:104` `Item.korean` | The target-language text is a column named “korean.” Amharic/Spanish cannot use it honestly. | **BLOCKER** | `language_id` on `item`; text moves to `item_form.text` with `script_id`; keep `korean` only during expand. |
| 2 | `app/models.py:105` `Item.english` | Gloss/translation is a column named “english.” UI language is not the same as source language. | **BLOCKER** | `item_gloss` (`lang`, `text`, `gloss_type`) or `dictionary_sense`; no “english” column. |
| 3 | `app/models.py:95-98` `uq_item_content` on `(korean, english, item_type)` | Uniqueness has no language; “no” in Spanish and “no” in English can collide when the legacy column holds any target language. | **BLOCKER** | Partial unique `(language_id, item_type, key_normalized, sense_key)` where `deleted_at IS NULL`; drop this constraint in contract. |
| 4 | `app/models.py:106` `Item.romanization` | A single romanization column assumes Hangul → RR. Ge’ez, Japanese, Spanish need different schemes and the scheme is not recorded. | **NEEDS-PARAMETERIZATION** | `item_form.transliteration` + `transliteration_scheme`; pack `romanize()`. |
| 5 | `app/models.py:107` `Item.level` | Integer level has implicit TOPIK 1–6 meaning; Spanish CEFR and Japanese JLPT do not share those bands. | **NEEDS-PARAMETERIZATION** | `level_scale_id` + pack level scale; resource filters read pack bands. |
| 6 | `app/models.py:103` `Item.item_type` | Set is small (`lexeme/chunk/grammar/sentence`) and UI labels are English. Amharic root/pattern items need `root`, `fidel`, `minimal_pair` types. | **NEEDS-PARAMETERIZATION** | Keep `item_type` as an open string validated by pack; add types without migration. |
| 7 | `app/models.py:15-16` `Phrase.english_text/korean_text` | Saved translation library is hard-coded English→Korean; no source/target language IDs. | **BLOCKER** for the translation feature; **not** for the core learn loop | Add `source_language_id`, `target_language_id`, `source_text`, `target_text`; rename in contract. Consider migrating `phrase` → `item` later. |
| 8 | `app/models.py:21, 26-28` `Phrase.__repr__` / `to_dict` keys | API and JS consume `english_text`/`korean_text` (`app/static/js/translate.js:53-59`). | **BLOCKER** for API compatibility | Keep response keys as aliases for one release; add `source_text`/`target_text`; version API later. |
| 9 | `app/models.py:282` `SpeechAttempt.target_text` | No language, no target item/form link, no phoneme scores. | **BLOCKER** | `language_id`, `item_id`, `item_form_id`, `phoneme_scores` JSON, `scoring_version`; rename to `PronunciationAttempt` in contract. |
| 10 | `app/models.py:254` `SceneSession.scene_slug` + `243-245` unique `(user_id, scene_slug)` | Scene slugs are global; two languages cannot both have `cafe-order`. | **BLOCKER** before second language | Add `language_id`; replace unique with `(user_id, language_id, scene_slug)`; later `scene_id` FK. |
| 11 | `app/models.py:218` `CanDoArtifact.scene_slug` + `207-211` unique | Same global slug problem; can-do labels are English/Korean strings. | **BLOCKER** before second language | Add `language_id`; unique `(user_id, language_id, scene_slug)`; store `label` in UI language. |
| 12 | `app/models.py:152` `ReviewCard.skill` | Values are generic strings, but UI labels and prompt sides are Korean-specific (`app/learning/routes.py:559-572`). | **NEEDS-PARAMETERIZATION** | Keep skill strings; move labels/prompt-side rules to pack. |
| 13 | `app/models.py:62-90` `User` | No target language, no UI locale; `goal` includes `topik`, `culture` and `experience` includes `hangul` (`app/models.py:77-79`). | **BLOCKER** for account-level language selection | Add `target_language_id`, `ui_locale`; goal/experience values become pack data with validation. |
| 14 | `app/models.py:387` `ConversationLine.speaker` `"Speaker 1"` | Stored display string, not a role enum; conversation language not recorded. | **NEEDS-PARAMETERIZATION** | Add `language_id` to `Conversation`; store `speaker_role` enum (`tutor/learner/character`). |
| 15 | `app/models.py:348` `Event.props` | Free-text JSON; no language column, so analytics cannot segment by language. | **NEEDS-PARAMETERIZATION** | Add nullable `language_id`; derive from user/item when absent. |
| 16 | `app/models.py:36-38` `Conversation.title/description` | Generated in English, no language metadata. | **COSMETIC / needs-parameterization** | Store `language_id`; pack supplies prompt and output language. |
| 17 | `migrations/versions/20261019_0002_learning_core.py:31-53` | Creates `item(korean, english, ...)` and `uq_item_content`. | **BLOCKER** | New expand migrations, never edit applied migrations. |
| 18 | `migrations/versions/20261019_0001_baseline_phrase.py:34-45` | Creates `phrase(english_text, korean_text)`. | **BLOCKER** | Same expand/backfill/contract path. |
| 19 | `migrations/versions/20261019_0007_speech_and_events.py:23` | `speech_attempt.target_text` no language. | **BLOCKER** | Add columns; backfill ko. |
| 20 | `migrations/versions/20261019_0008_scene_sessions.py:22, 30-32` and `migrations/versions/20261019_0009_can_do_artifacts.py:22, 27-29` | Global `scene_slug` uniqueness. | **BLOCKER** before second language | Add language, replace unique in expand/contract. |

### 1.3 Curriculum and learning modules

| # | Location | Korean assumption | Severity | Target |
|---|---|---|---|---|
| 21 | `app/learning/hangul_data.py:14-1485` | 1,485 lines: seven Hangul lessons, 88 drills, Hangul-specific tables and notes. Imported directly by `app/learning/routes.py:26`. | **BLOCKER** | Move to `app/languages/ko/script/*.json` + generic loader; shim for one release. |
| 22 | `app/learning/scene_data.py:20-466` | Four Korean scenes; step keys `character_korean`, `character_english`, `target_item.korean/english`; embedded Korean “알렉스.” | **BLOCKER** | `app/languages/ko/curriculum/scenes/*.json`; schema uses `text`, `gloss`, `translation`, `speaker_role`. |
| 23 | `app/learning/sound_gym_data.py:12-213` | Korean minimal pairs defined by Hangul jamo contrasts (`ㅂ/ㅃ/ㅍ`), RR romanization, Korean production prompts. | **BLOCKER** for sound gym in another language | `app/languages/<code>/sound_gym/*.json`; generic `contrast`, `units`, `target` fields. |
| 24 | `app/learning/seed_data.py:12-46` | 30 hand-curated Korean items; keys `korean`, `english`; `seed_content()` inserts globally when `Item.query.count() == 0` (`app/learning/routes.py:72-75`). | **BLOCKER** | `curriculum/seed_items.json` per pack; `seed_content(language_id, deck_slug)`, never global emptiness. |
| 25 | `app/learning/scenes.py:16-17` `_normalize` | Strips everything except `0-9A-Za-z가-힣`; rejects Ge’ez, kana, accented Latin, and Hangul jamo. | **BLOCKER** | `pack.normalize()`; per-language equivalence class. |
| 26 | `app/learning/scenes.py:121-145` `_create_debrief_cards` | Reads `card["korean"]`, `card["english"]`, hard-codes `item_type="chunk"`. | **BLOCKER** | Read pack scene schema; use `target_form`/`gloss`; `item_type` from data. |
| 27 | `app/learning/scenes.py:171-179` transcript | Writes `character_korean` into transcript JSON. | **NEEDS-PARAMETERIZATION** | `character_text`, `character_form_id`; language-scoped. |
| 28 | `app/learning/service.py:117-160, 215-238` | `stats()` counts all `Item` rows; `ensure_review_cards()` creates cards for every item regardless of language. | **BLOCKER** for multi-language decks | Every query takes `language_id`/`deck_id` filter; “all items” is a bug once two languages exist. |
| 29 | `app/learning/service.py:63-102` | `available_cards()` is user-scoped but not language-scoped; a Spanish learner sees Korean cards. | **BLOCKER** | Filter via `Item.language_id` join or denormalized `ReviewCard.language_id`. |
| 30 | `app/learning/analytics.py:143-195` | `metrics_summary()` counts all users/items/events globally. | **NEEDS-PARAMETERIZATION** | Add optional `language_id`; default aggregate for admin. |
| 31 | `app/learning/analytics.py:72-140` | Weekly recap is user-scoped but can-dos and cards are not language-scoped. | **NEEDS-PARAMETERIZATION** | Join item language or store `language_id` on cards/logs. |
| 32 | `app/learning/scheduler.py:42-112` | Language-neutral. Reuse unchanged. | — | Keep as-is; add `language_id` only if denormalizing cards. |
| 33 | `app/learning/cli.py:18-25, 63-100` | Seeds “starter Korean content,” prints `item.korean`, generates audio from `item.korean` with one voice. | **NEEDS-PARAMETERIZATION** | `--language`, `--deck`, `--voice` resolved from pack. |
| 34 | `hangul.py:25-125` (repo root CLI) | Separate Korean-only EN→KO + TTS script; `korean_translation` key, `voice="onyx"`. | **COSMETIC / defer** | Replace with `tools/translate_cli.py --lang`; not on web path. |

### 1.4 AI, speech, validation, config

| # | Location | Korean assumption | Severity | Target |
|---|---|---|---|---|
| 35 | `app/services/translation.py:18-20, 64-86` | Prompt says “Translate … to Korean,” requires JSON key `korean_translation`; no source/target language parameters. | **BLOCKER** | `TranslationProvider.translate(TranslationRequest(source_lang, target_lang, text, context_item_ids))`; pack-supplied prompt fragments. |
| 36 | `app/services/translation.py:49` | Parses `TranslationResponse.korean_translation`. | **BLOCKER** | Generic `TranslationResponse.translation` with target language validation; keep alias for ko. |
| 37 | `app/services/translation.py:110-127` | Translation cache key is `TRANSLATION_CACHE_VERSION:model:text`, no language/pack version. | **BLOCKER** for correctness | Key includes `source_lang`, `target_lang`, `pack_version`, provider/model. |
| 38 | `app/services/translation.py:130-146` | Conversation prompt hard-codes “Korean language learners,” `english_text`/`korean_text`, “natural Korean written in Hangul.” | **BLOCKER** | Generic conversation scenario schema; pack supplies output language and script rule. |
| 39 | `app/utils/schemas.py:25-27` `contains_hangul` | Only precomposed Hangul syllables; not jamo, Ge’ez, kana, accented Latin. | **BLOCKER** | `pack.validate_text()`; generic `target_text` field; script ranges from pack. |
| 40 | `app/utils/schemas.py:52-69` | `TranslationResponse.korean_translation` + Hangul validator. | **BLOCKER** | `TranslationResponse.translation` + `target_lang`; validator is pack callback. |
| 41 | `app/utils/schemas.py:83-105` | `ConversationLine.english_text/korean_text` + Hangul validator. | **BLOCKER** | `source_text`/`target_text`/`target_lang`; pack validator. |
| 42 | `app/services/speech.py:26-28` `_normalize` | Hangul-only regex; strips jamo and all non-Latin scripts. | **BLOCKER** | `pack.normalize()` per language. |
| 43 | `app/services/speech.py:39` | Error says “Target text must contain Korean characters.” | **NEEDS-PARAMETERIZATION** | Pack-specific message. |
| 44 | `app/services/speech.py:80-86` | `language="ko"` hard-coded to OpenAI transcription. | **BLOCKER** | `ASRRequest.language_code` from pack. |
| 45 | `app/services/speech.py:100-108` | Provider/model recorded, but no language or phoneme scores; result schema is transcript-match only. | **NEEDS-PARAMETERIZATION** | `PronunciationScorer` interface; `PronunciationAttempt` fields. |
| 46 | `app/services/audio.py:21-26, 31` | Default `voice="onyx"`, one TTS model; no language/voice map. | **NEEDS-PARAMETERIZATION** | `TTSRequest(profile, voice_role)`; pack `tts.voices`. |
| 47 | `app/services/ai.py:37-95` | Global singleton keyed only by API key; injection via `extensions["openai_client"]`. | **Reusable** | Keep lazy pattern; move behind provider adapters; do not globally key only by API key once multiple providers exist. |
| 48 | `config.py:30-32` | Default DB filename `korean_learner.db`. | **COSMETIC** | `kiku.db`, with env override and compatibility. |
| 49 | `config.py:43-47` | `TRANSLATION_MODEL`, `CONVERSATION_MODEL`, `TTS_MODEL`, `TTS_VOICE_1/2` are global. | **NEEDS-PARAMETERIZATION** | Provider defaults global; voice/model overrides per language pack. |
| 50 | `config.py:66-73` | `SPEECH_PROVIDER`, `SPEECH_TRANSCRIBE_MODEL`, `SPEECH_ACCEPT_THRESHOLD` global; threshold may need per language. | **NEEDS-PARAMETERIZATION** | Pack `asr`/`scoring` profile; config only deployment overrides. |
| 51 | `config.py:96` `LEARNER_TIMEZONE` | Single local user assumption; not language-specific, but per-user language profiles need `User.timezone` (already exists). | **Reusable / account work** | Per-user timezone remains. |
| 52 | `env.example:12-16, 32-40` | Documents Korean-only TTS/STT model and voices. | **COSMETIC** | Add provider + per-language override examples. |
| 53 | `app/__init__.py:342-349` | Jinja filter `has_hangul` decides `lang="ko"` automatically. | **BLOCKER** for template genericity | Replace with `script_of(text)`/pack-aware filter; templates use explicit `lang` from form. |
| 54 | `app/__init__.py:311-319` | Registers `main`, `learn`, `onboarding`; no language selection/registry extension. | **NEEDS-PARAMETERIZATION** | Register language registry and language-aware URL handling. |

### 1.5 Routes, templates, JS, PWA, static audio

| # | Location | Korean assumption | Severity | Target |
|---|---|---|---|---|
| 55 | `app/learning/routes.py:69` blueprint `url_prefix="/learn"` | No language segment; all learners share the same routes. | **NEEDS-PARAMETERIZATION** | `/<lang_code>/learn` (with legacy `/learn` redirect for ko). |
| 56 | `app/learning/routes.py:483-505` `/hangul`, `/hangul/<slug>` | Hangul is a hard-coded feature, not one script course. | **BLOCKER** for script courses | `/<lang>/script`, `/<lang>/script/<lesson>`; Hangul becomes ko pack data. |
| 57 | `app/learning/routes.py:559-560` | `prompt_side = "korean"` / `"english"`; template branches on those literals. | **BLOCKER** for UI | Pack defines prompt/answer sides; template uses `item.primary_form`, `item.primary_gloss`. |
| 58 | `app/learning/routes.py:567-572` | Skill/type labels hard-coded English. | **NEEDS-PARAMETERIZATION** | Pack/UI locale labels. |
| 59 | `app/learning/routes.py:404-410` | Speech target validation requires `contains_hangul`; error says “short Korean target text.” | **BLOCKER** | `pack.validate_text(target_text)`, language from request. |
| 60 | `app/routes.py:99-136` `/resources` | Search filters `Item.korean`, `Item.english`, `Item.romanization`; level filter 1–6. | **BLOCKER** for non-Korean search | Search `item_form`/`item_gloss` scoped to current language; level bands from pack. |
| 61 | `app/routes.py:263-319` `/api/translate` | Calls `translate_to_korean`, writes `Phrase(english_text, korean_text)`, filename from English text. | **BLOCKER** for multi-language translation | Generic request with source/target language; `Phrase` source/target columns. |
| 62 | `app/routes.py:341-345, 383-420` conversation | Two Korean TTS voices; filenames from `line.english_text`; fields `korean_text`. | **NEEDS-PARAMETERIZATION** | Pack voice roles; generic line fields; language ID. |
| 63 | `app/routes.py:89-96` `/library`; `app/templates/library.html:11-12` | Lists `Phrase` English/Korean columns. | **NEEDS-PARAMETERIZATION** | List `TermCard`/saved translations with source/target. |
| 64 | `app/onboarding/routes.py:24-55` | Goals are Korean-specific: “Everyday Korean,” “K-drama & music,” “TOPIK.” | **BLOCKER** for onboarding a Spanish learner | Goal list from pack; generic + language-specific goals. |
| 65 | `app/onboarding/routes.py:63-84` | Experience values include `hangul`; Spanish/Amharic need `script_literate`. | **NEEDS-PARAMETERIZATION** | Generic `new/script_literate/conversational/intermediate`; pack maps wording. |
| 66 | `app/onboarding/routes.py:156-171` | `/welcome/first-word` hard-codes 안녕하세요 in template. | **NEEDS-PARAMETERIZATION** | Pack `first_utterance` (item/form/audio). |
| 67 | `app/templates/base.html:2, 6, 36` | `<html lang="en">`, title “Korean Language Learner,” aria label “Korean language learner.” | **COSMETIC / needs-parameterization** | UI locale + product name; language name from pack. |
| 68 | `app/templates/base.html:52-58` | Nav item “Hangul” with `/learn/hangul`. | **BLOCKER** for generic nav | Nav label from pack’s script course (“Hangul,” “Fidel,” “Alphabet”). |
| 69 | `app/templates/learn_today.html:6` | “Today’s Korean.” | **COSMETIC / needs-parameterization** | “Today’s Spanish,” etc. |
| 70 | `app/templates/learn_review.html:19, 23, 37, 44, 51, 65` | Literal “Korean → English,” `lang="ko"`, “Say it in Korean,” “Hear … in Korean.” | **BLOCKER** for correct labels and accessibility | Generic `source/target` labels; `lang` from form script; pack display name. |
| 71 | `app/templates/resources.html:8, 13, 19, 48` | “Search your Korean deck,” `lang="ko"`, “Search Korean, English…” | **NEEDS-PARAMETERIZATION** | Pack language name; generic search placeholder. |
| 72 | `app/templates/index.html:18-19, 38-39` | “translate to Korean,” `.phrase-korean` `lang="ko"`. | **NEEDS-PARAMETERIZATION** | Generic translation UI with language picker. |
| 73 | `app/templates/scene_play.html:23-66` | Korean transcript labels, `lang="ko"`, “Your line in Korean,” “Type your Korean line.” | **BLOCKER** for scene UI in another language | `lang` from scene pack; labels from UI locale; input `dir`. |
| 74 | `app/templates/scene_list.html:6` | “Use Korean before you feel ready.” | **COSMETIC / needs-parameterization** | Pack name. |
| 75 | `app/templates/scene_complete.html:26-27` | `lang="ko"` + `card.korean` / `card.english`. | **NEEDS-PARAMETERIZATION** | Generic form/gloss fields. |
| 76 | `app/templates/hangul_index.html`, `hangul_lesson.html` | Whole templates are Hangul-specific (`:2, :5-6, :28-38, :104`). | **BLOCKER** for non-Hangul scripts | Rename to `script_index.html`, `script_lesson.html`; data-driven. |
| 77 | `app/templates/welcome.html:6-8`, `welcome_first_word.html:2, 13, 20, 50` | Korean onboarding copy and 안녕하세요. | **BLOCKER** for non-ko onboarding | Pack onboarding strings/first item. |
| 78 | `app/templates/settings.html:22-29, 43-49` | Hard-coded Korean goals and `hangul` experience. | **NEEDS-PARAMETERIZATION** | Pack goals/experience; settings reads current user language. |
| 79 | `app/templates/sound_gym.html:35, 58, 66` | `lang="ko"`, `word.korean`, “in Korean.” | **NEEDS-PARAMETERIZATION** | Generic `word.text`, pack language name. |
| 80 | `app/templates/learn_progress.html:6, 134-135` | “Your Korean,” `item.korean`, `item.english`. | **COSMETIC / needs-parameterization** | Pack name + form/gloss. |
| 81 | `app/static/js/onboarding.js:23`, `review.js:78`, `scene.js:13`, `hangul.js:39`, `sound_gym.js:19` | `utterance.lang = "ko-KR"` repeated five times. | **BLOCKER** for correct TTS pronunciation | `data-tts-lang` from pack; one shared `speak()` helper. |
| 82 | `app/static/js/translate.js:53-59` | Reads `data.korean_text`; `.phrase-korean`. | **BLOCKER** for API/JS contract | `data.target_text`, `data.source_text`; compatibility alias one release. |
| 83 | `app/static/js/new_conversation.js:121-145` | Reads `phrase.korean_text`; sets `lang="ko"` and class `phrase-korean`. | **NEEDS-PARAMETERIZATION** | Generic `target_text`, `lang` from payload. |
| 84 | `app/static/js/sound_gym.js:39, 55, 62` | `data-korean` attributes drive the drill. | **NEEDS-PARAMETERIZATION** | `data-target`, `data-script`; pack-independent. |
| 85 | `app/static/manifest.webmanifest:2-4` | Name “Kiku — Korean,” description “Voice-first Korean…” | **NEEDS-PARAMETERIZATION** | Dynamic manifest per language, or generic “Kiku — Languages.” |
| 86 | `app/static/sw.js:55` | Push body “A short Korean session is ready.” | **NEEDS-PARAMETERIZATION** | Generic body or per-language payload; push server already has `url: /learn/` (`app/services/push.py:191-196`). |
| 87 | `app/static/css/style.css:13, 182, 741, 1085, 1142-1329, 1515, 1753, 1987` | `.hangul`, `.phrase-korean`, `.resource-korean`, `.bubble-korean`, font comment. | **COSMETIC** | Add `.script-*`/`.target-*`; keep aliases. |
| 88 | `app/static/audio/*` (16 files) and `config.py:36` | Flat directory; filenames from English text (`app/utils/media.py:96-104`); no language/voice partition. | **NEEDS-PARAMETERIZATION** | `AUDIO_DIR/<lang>/<voice>/<stem>.mp3`; keep media audit recursive. |

### 1.6 Tests, CI, migrations

| # | Location | Korean assumption | Severity | Target |
|---|---|---|---|---|
| 89 | `tests/conftest.py:56-64` | Fake OpenAI payload returns `korean_translation` and `korean_text`. | **BLOCKER** for tests | Generic payload + per-language fake responses. |
| 90 | `tests/conftest.py:111-113` | Fake transcription always returns `안녕하세요`. | **NEEDS-PARAMETERIZATION** | Fake returns pack-specific transcript. |
| 91 | `tests/test_onboarding.py:25-26, 85, 113-128` | Asserts Korean copy and `/learn/hangul`. | **BLOCKER** for test parameterization | Pack-driven assertions/URL helper. |
| 92 | `tests/test_resources.py:10, 14-21` | Asserts “Hangul bootcamp” and `q=커피`. | **NEEDS-PARAMETERIZATION** | Use pack sample word and current language route. |
| 93 | `tests/test_speech.py:10-20, 57-67` | Korean exact/partial/wrong; non-Korean target rejection. | **BLOCKER** for generic speech | Parametrize per pack; “wrong script” test per language. |
| 94 | `tests/test_ai_services.py:175-233, 267-285` | `korean_translation`, Hangul validator. | **BLOCKER** for provider contracts | Generic `translation` + `target_lang`; pack validator injection. |
| 95 | `tests/test_phase0_platform.py:341-351` | `test_translation_rejects_non_hangul_output`. | **BLOCKER** for generic validation | `test_translation_rejects_wrong_script_for_target_language`. |
| 96 | `tests/test_scene_data.py:33-42, 84, 124-131` | Keys `character_korean`, `korean`, `english`. | **NEEDS-PARAMETERIZATION** | Schema v2 keys; golden per pack. |
| 97 | `tests/test_sound_gym_data.py:10-13, 59-67` | Keys `korean`, `romanization`, `english`; duplicate Korean check. | **NEEDS-PARAMETERIZATION** | Generic `text`, `transliteration`, `gloss`; per-pack uniqueness. |
| 98 | `tests/test_hangul_data.py:7-24, 112-129` | Asserts seven Hangul lessons, exact drill counts. | **BLOCKER** for pack extraction | Generic `test_script_pack` golden by pack. |
| 99 | `tests/test_learning_loop.py:12-20` | Assumes auto-seed gives ≥25 items and one card per item across all languages. | **BLOCKER** once two languages exist | Seed only current deck/language; assert deck counts. |
| 100 | `tests/test_scene_speech.py:40-73` | Uses `SCENES[0]` and Korean expected lines. | **NEEDS-PARAMETERIZATION** | `pack.scenes[0]`; per-language fake transcript. |
| 101 | `tests/test_audio_cli.py:9-12` | `_make_item(korean="안녕하세요")`. | **COSMETIC / needs-parameterization** | Generic `text`/`language`. |
| 102 | `.github/workflows/ci.yml:30-74` | CI migration gate expects the exact Korean-era table set and `review_log.was_new`; no multilingual tables. | **BLOCKER** for shipping migrations | Update expected tables/columns; add old→new data migration test. |
| 103 | `tests/conftest.py:173-174` | Uses `db.create_all()`, not migrations; can mask migration drift (as happened with the `phrase` baseline, `0001:1-7`). | **RISK** | Keep `create_all` for speed but add metadata-vs-migrations parity test. |

### 1.7 What actually blocks language #2 (ordered, not exhaustive)

1. **No `language` row / `language_id` anywhere.** Nothing can be scoped.
2. **`Item.korean`/`Item.english` + `uq_item_content`.** Target text and uniqueness are language-hostile.
3. **Content modules imported directly by routes** (`hangul_data`, `scene_data`, `seed_data`, `sound_gym_data`). A second language requires editing core routes unless extracted.
4. **Translation/schema validators hard-coded to Hangul** (`translation.py`, `schemas.py`). AI cannot produce Amharic or Spanish.
5. **ASR `language="ko"` and Hangul-only normalization** (`speech.py`). Speech checks silently fail for every other script.
6. **TTS voice/locale hard-coded** (`audio.py`, five JS `ko-KR`, config). Wrong pronunciation is a quality bug.
7. **Scene/can-do global slugs.** Same scene slug in two languages violates a unique constraint.
8. **Stats/cards/seed are global.** A second deck changes every learner’s counts and review queue.
9. **URL/UI has no language selector.** Even if data existed, users cannot reach it.
10. **Tests/CI encode Korean** and would block the migration PR.

### 1.8 What does **not** block a second language (defer)

- CSS class names, product name, DB filename, README.
- The root `hangul.py` CLI (dead web path; replace later).
- Existing `Conversation`/`Phrase` library UX can remain English→target for one release; it is not on the FSRS critical path.
- Phoneme-level pronunciation scoring: transcript gate is language-agnostic once normalization/ASR language are pack-driven.
- Full UI localization (translating every button into Amharic/Spanish) — not needed to teach a language; English UI is acceptable at launch.

---

## 2. Target domain model

### 2.1 Key decisions (opinionated)

| Decision | Choice | Why |
|---|---|---|
| Item storage | **Single polymorphic `item` table + `language_id`**, with `item_form`, `item_gloss`, optional `dictionary_entry_id` | FSRS is `(user, item, skill)` (`app/models.py:132-172`). Table-per-language multiplies scheduler, review UI, analytics, migrations. Item identity stays stable across languages. |
| Text storage | **`item_form` child rows**, not text columns on `item` | Korean has jamo/precomposed/Hangul+Hanja; Amharic has fidel and root-pattern forms; Japanese has mixed scripts. A form row carries `script_id`, `text`, `normalized_text`, `transliteration`, `audio_path`, `form_kind`. |
| Gloss storage | **`item_gloss`** (`lang`, `text`, `gloss_type`) and `dictionary_sense` for lexical entries | UI language ≠ source language. Avoid `english` columns. |
| Script representation | **`script` + `script_unit` catalog, but behavior lives in `LanguagePack`** | Hangul block composition, Ge’ez abugida order, Latin alphabet, and Japanese mixed script are not one data shape. DB stores metadata/units for UI and golden files; code does normalization/segmentation. |
| Transliteration | **Per-form `transliteration` + `transliteration_scheme`; pack `romanize()`** | No “romanization column” semantics. Korean RR/Yale, Amharic BGN/PCGN or ALA-LC, Japanese Hepburn are schemes, not languages. |
| Morphology | **`item_form.morphology` JSON + `morphology_family` / `form_group` / `form_condition`**, validated by pack JSON Schema | Korean particle allomorphs and Amharic root-pattern are representable without a universal feature geometry. No premature linguistics database. |
| Multi-sense | **`dictionary_entry` (lemma+POS) → `dictionary_sense` (ordered meanings)** | Homographs are real (Korean 개 “dog” vs counter; Amharic homonyms). |
| User library | **`term_card` references an `item` and/or `dictionary_entry`** | Personal library does not duplicate content. Promote to a personal deck/item only when the learner wants to practice. |
| Soft delete/versioning | `deleted_at`, `version`, `content_hash`, `status` on content tables; partial unique indexes | Preserve review history; allow deprecation and re-import. Existing partial-index precedent: `app/models.py:63-71`. |
| Scene content | **Pack JSON as source of truth; DB `scene` optional later** | Scenes are authored content, not user data. Start by adding `language_id` to sessions and scoping slugs; add `scene` table when teacher-generated scenes exist. |
| Phrase library | Keep table; add source/target IDs, rename columns in contract; later migrate to `item`/`snippet` | Avoid a big-bang rewrite; library is not the learning core. |
| ReviewCard | **Unchanged shape** `(user_id, item_id, skill)` | Existing scheduler and UI are reusable; language is implied by item. Optionally denormalize `language_id` later for analytics. |

### 2.2 Current → target schema (text diagram)

**Current**

```
phrase(id, uuid, english_text, korean_text, audio_path)
conversation(id, title, description, audio_path)
  └─ conversation_line(conversation_id, phrase_id, speaker, order)

user(id, email, goal, daily_minutes, experience, timezone, ...)
item(id, item_type, korean, english, romanization, level, freq_rank,
     audio_path, notes, default_skill)
  UNIQUE(korean, english, item_type)
review_card(user_id, item_id, skill, FSRS...)  UNIQUE(user,item,skill)
  └─ review_log(card_id, user_id, rating, ...)

speech_attempt(user_id, item_id?, target_text, transcript, match_score, ...)
scene_session(user_id, scene_slug, step_index, ...)  UNIQUE(user, scene_slug)
can_do_artifact(user_id, scene_slug, label)          UNIQUE(user, scene_slug)
event(user_id, name, props JSON)
```

**Target**

```
language(id, code, name, native_name, direction, default_level_scale_id)
  ├─n language_script(n) ─n script(id, code, script_type, direction, unicode_ranges, composition)
  ├─n level_scale(id, code, min, max, labels JSON)
  ├─n course(id, slug, title, ...)
  │     └─n deck(id, course_id?, owner_id?, slug, kind, version, deleted_at)
  │           └─n deck_item(n) ─n item
  └─n dictionary_entry(id, language_id, lemma_item_id?, normalized_headword, pos, gender_class,
                        register, frequency_rank, version, deleted_at)
        └─n dictionary_sense(id, entry_id, sense_order, gloss_lang, gloss, definition,
                             example_item_id?, register, domain)

item(id, language_id, primary_deck_id?, item_type, level, level_scale_id?,
     freq_rank, default_skill, status, version, content_hash, key_normalized, sense_key,
     deleted_at, superseded_by_id)
  ├─n item_form(id, item_id, script_id, form_kind, text, normalized_text,
  │              transliteration, transliteration_scheme, ipa, audio_path,
  │              is_primary, morphology JSON, form_group, form_condition,
  │              version, deleted_at)
  ├─n item_gloss(id, item_id, lang, text, gloss_type, is_primary, version)
  └─0..1 dictionary_entry

translation(id, source_language_id, target_language_id, sense_id?, source_item_id?,
            target_item_id?, source_text_hash, source_text, target_text,
            provider, model, quality, is_human_reviewed, version)

term_card(id, user_id, language_id, item_id?, dictionary_entry_id?, source,
          note, tags JSON, created_at, archived_at)
  UNIQUE partial (user_id, item_id) / (user_id, dictionary_entry_id)

review_card(user_id, item_id, skill, FSRS...)     -- unchanged
review_log(card_id, user_id, rating, ...)         -- unchanged

pronunciation_attempt(id, user_id, language_id, item_id?, item_form_id?,
                      target_text, transcript, overall_score, match_score, acceptable,
                      provider, model, phoneme_scores JSON, prosody_scores JSON,
                      duration_ms, scoring_version, created_at)

teacher_session(id, uuid, user_id, language_id, course_id?, deck_id?, mode,
                provider, provider_session_id, status, started_at, ended_at,
                token_expires_at, turn_count, cost_micros, summary_text, metadata JSON)
  └─n teacher_turn(id, session_id, turn_index, role, text, lang, tool_name,
                   tool_args JSON, tool_result JSON, latency_ms, created_at)
        UNIQUE(session_id, turn_index)

drill(id, uuid, language_id, user_id?, session_id?, source, drill_type,
      prompt_item_id, expected JSON, payload JSON, validated, validator_version,
      pack_version, created_at, deleted_at)
  └─n drill_attempt(id, drill_id, user_id, response, score, acceptable,
                    feedback, duration_ms, created_item_id?, review_card_id?,
                    client_attempt_id, created_at)

scene_session(user_id, language_id, scene_slug, ...)  UNIQUE(user, language, scene_slug)
can_do_artifact(user_id, language_id, scene_slug, label) UNIQUE(user, language, scene_slug)
event(user_id, language_id?, name, props JSON)
user(..., target_language_id, ui_locale)
```

**Mapping from today’s columns**

| Today | Target |
|---|---|
| `item.korean` | `item_form.text` (`script=hangul`, `form_kind=citation`, `is_primary=1`) |
| `item.english` | `item_gloss.text` (`lang=en`, `gloss_type=translation`, `is_primary=1`) |
| `item.romanization` | `item_form.transliteration` (`scheme=rr`) |
| `item.audio_path` | `item_form.audio_path` (per form/voice) |
| `item.notes` | `item_gloss` (`gloss_type=note`) or `item.note` JSON by UI lang |
| `item.level` | `item.level` + `language.default_level_scale` |
| `phrase.english_text/korean_text` | `phrase.source_text/target_text` + `source_language_id/target_language_id` |
| `speech_attempt.target_text` | `pronunciation_attempt.target_text` + `item_form_id` + `language_id` |
| `scene_session.scene_slug` | `scene_session.scene_slug` + `language_id` (then optional `scene_id`) |
| `uq_item_content` | partial unique `(language_id, item_type, key_normalized, sense_key)` |

### 2.3 Table sketches (SQLAlchemy-flavored, not final migrations)

Only the columns that matter for the design are shown. Every content table gets `created_at`, `updated_at`, `version`, `deleted_at` unless noted.

```python
class Language(db.Model):
    __tablename__ = "language"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), nullable=False, unique=True)   # "ko", "am", "es", "ja"
    name = db.Column(db.String(64), nullable=False)                # English name
    native_name = db.Column(db.String(64), nullable=False)         # 한국어, አማርኛ, Español, 日本語
    direction = db.Column(db.String(3), nullable=False, default="ltr")
    default_level_scale_id = db.Column(db.Integer, db.ForeignKey("level_scale.id"))
    ui_locale = db.Column(db.String(16), nullable=True)            # default UI locale
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Script(db.Model):
    __tablename__ = "script"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, unique=True)  # hangul, geez, latin, kana, han
    name = db.Column(db.String(64), nullable=False)
    script_type = db.Column(db.String(20), nullable=False)         # alphabet|abjad|abugida|syllabary|logosyllabic|mixed
    direction = db.Column(db.String(3), nullable=False, default="ltr")
    unicode_ranges = db.Column(db.Text, nullable=True)             # JSON [[0xAC00,0xD7A3],...]
    composition = db.Column(db.String(20), nullable=False)         # linear|block|abugida|mixed


class LanguageScript(db.Model):
    __tablename__ = "language_script"
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey("script.id"), primary_key=True)
    role = db.Column(db.String(16), nullable=False, default="primary")  # primary|auxiliary|romanization
    is_default = db.Column(db.Boolean, nullable=False, default=False)


class LevelScale(db.Model):
    __tablename__ = "level_scale"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=True)  # None = global CEFR
    code = db.Column(db.String(24), nullable=False)                # topik, cefr, jlpt, custom_am
    min_level = db.Column(db.Integer, nullable=False, default=1)
    max_level = db.Column(db.Integer, nullable=False, default=6)
    labels = db.Column(db.Text, nullable=False)                    # JSON {"1":"TOPIK 1",...}
    descriptors = db.Column(db.Text, nullable=True)                # JSON
    __table_args__ = (db.UniqueConstraint("language_id", "code", name="uq_level_scale_language_code"),)


class Item(db.Model):
    __tablename__ = "item"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False, index=True)
    primary_deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=True)
    dictionary_entry_id = db.Column(db.Integer, db.ForeignKey("dictionary_entry.id"), nullable=True)
    item_type = db.Column(db.String(24), nullable=False, default="lexeme")
    level = db.Column(db.Integer, nullable=False, default=1)
    level_scale_id = db.Column(db.Integer, db.ForeignKey("level_scale.id"), nullable=True)
    freq_rank = db.Column(db.Integer, nullable=True)
    default_skill = db.Column(db.String(20), nullable=False, default="recognize")
    status = db.Column(db.String(16), nullable=False, default="published")  # draft|published|deprecated
    key_normalized = db.Column(db.String(300), nullable=False)
    sense_key = db.Column(db.String(300), nullable=False, default="")
    content_hash = db.Column(db.String(64), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    superseded_by_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    # __table_args__: Index("ix_item_language_level_type", "language_id", "level", "item_type")
    # partial unique Index("uq_item_language_type_key", "language_id", "item_type",
    #                      "key_normalized", "sense_key", unique=True,
    #                      sqlite_where=db.text("deleted_at IS NULL"),
    #                      postgresql_where=db.text("deleted_at IS NULL"))


class ItemForm(db.Model):
    __tablename__ = "item_form"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False)
    script_id = db.Column(db.Integer, db.ForeignKey("script.id"), nullable=False)
    form_kind = db.Column(db.String(20), nullable=False, default="citation")  # citation|surface|inflected|variant|phonetic
    text = db.Column(db.String(500), nullable=False)
    normalized_text = db.Column(db.String(500), nullable=False)
    transliteration = db.Column(db.String(500), nullable=True)
    transliteration_scheme = db.Column(db.String(24), nullable=True)          # rr|yale|bgn_pcgn|hepburn|...
    ipa = db.Column(db.String(500), nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    morphology = db.Column(db.Text, nullable=True)                 # JSON, pack-validated
    morphology_family = db.Column(db.String(24), nullable=True)    # particle|ending|root_pattern|infix
    form_group = db.Column(db.String(60), nullable=True)           # e.g. eun-neun
    form_condition = db.Column(db.String(60), nullable=True)       # after_consonant|after_vowel
    version = db.Column(db.Integer, nullable=False, default=1)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # unique(item_id, form_kind, normalized_text) partial deleted_at IS NULL
```

`DictionaryEntry` / `DictionarySense`:

```python
class DictionaryEntry(db.Model):
    __tablename__ = "dictionary_entry"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    lemma_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    headword = db.Column(db.String(300), nullable=False)
    normalized_headword = db.Column(db.String(300), nullable=False)
    pos = db.Column(db.String(24), nullable=False)                 # noun|verb|particle|...
    gender_class = db.Column(db.String(24), nullable=True)         # Spanish gender, noun class, etc.
    register = db.Column(db.String(24), nullable=True)             # polite|formal|informal|neutral
    frequency_rank = db.Column(db.Integer, nullable=True)
    etymology = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(16), nullable=False, default="published")
    version = db.Column(db.Integer, nullable=False, default=1)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # partial unique (language_id, normalized_headword, pos)


class DictionarySense(db.Model):
    __tablename__ = "dictionary_sense"
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("dictionary_entry.id", ondelete="CASCADE"), nullable=False)
    sense_order = db.Column(db.Integer, nullable=False, default=1)
    gloss_lang = db.Column(db.String(12), nullable=False, default="en")
    gloss = db.Column(db.String(300), nullable=False)
    definition = db.Column(db.Text, nullable=True)
    domain = db.Column(db.String(60), nullable=True)
    register = db.Column(db.String(24), nullable=True)
    example_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    # unique(entry_id, sense_order)
```

`Course` / `Deck` / `DeckItem` / `ItemGloss` / `Translation`:

```python
class Course(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    slug = db.Column(db.String(60), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    goal = db.Column(db.String(40), nullable=True)
    level_scale_id = db.Column(db.Integer, db.ForeignKey("level_scale.id"), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    # unique(language_id, slug)


class Deck(db.Model):
    __tablename__ = "deck"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # NULL = public
    slug = db.Column(db.String(60), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.String(24), nullable=False, default="core")  # core|script|scene|personal|teacher|dictionary
    source = db.Column(db.String(24), nullable=False, default="seed")  # seed|import|teacher|user
    version = db.Column(db.Integer, nullable=False, default=1)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # partial unique (language_id, owner_id, slug) where deleted_at IS NULL


class DeckItem(db.Model):
    __tablename__ = "deck_item"
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id", ondelete="CASCADE"), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    added_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class ItemGloss(db.Model):
    __tablename__ = "item_gloss"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="CASCADE"), nullable=False)
    lang = db.Column(db.String(12), nullable=False, default="en")     # UI/source language
    text = db.Column(db.String(500), nullable=False)
    gloss_type = db.Column(db.String(20), nullable=False, default="translation")  # translation|definition|note|hint
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    # unique(item_id, lang, gloss_type) partial version/deleted rules if needed


class Translation(db.Model):
    __tablename__ = "translation"
    id = db.Column(db.Integer, primary_key=True)
    source_language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    target_language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    sense_id = db.Column(db.Integer, db.ForeignKey("dictionary_sense.id"), nullable=True)
    source_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    target_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    source_text_hash = db.Column(db.String(64), nullable=False)
    source_text = db.Column(db.Text, nullable=False)
    target_text = db.Column(db.Text, nullable=False)
    provider = db.Column(db.String(30), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    quality = db.Column(db.String(16), nullable=False, default="machine")  # machine|reviewed|native
    is_human_reviewed = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    # unique(source_language_id, target_language_id, sense_id, source_text_hash, quality)
```

`Drill` / `DrillAttempt` (drills are generated, so they get their own version/validation fields):

```python
class Drill(db.Model):
    __tablename__ = "drill"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey("teacher_session.id", ondelete="SET NULL"), nullable=True)
    source = db.Column(db.String(16), nullable=False, default="teacher")  # teacher|curriculum
    drill_type = db.Column(db.String(24), nullable=False)                # cloze|translate|produce|minimal_pair|scene
    prompt_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    expected = db.Column(db.Text, nullable=False)                        # JSON
    payload = db.Column(db.Text, nullable=True)                          # JSON options/hints
    validated = db.Column(db.Boolean, nullable=False, default=False)
    validator_version = db.Column(db.String(24), nullable=True)
    pack_version = db.Column(db.String(24), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)


class DrillAttempt(db.Model):
    __tablename__ = "drill_attempt"
    id = db.Column(db.Integer, primary_key=True)
    drill_id = db.Column(db.Integer, db.ForeignKey("drill.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    response = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=True)
    acceptable = db.Column(db.Boolean, nullable=False, default=False)
    feedback = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    created_item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    review_card_id = db.Column(db.Integer, db.ForeignKey("review_card.id"), nullable=True)
    client_attempt_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    # unique(drill_id, user_id, client_attempt_id)
```

`TermCard`:

```python
class TermCard(db.Model):
    __tablename__ = "term_card"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True)
    dictionary_entry_id = db.Column(db.Integer, db.ForeignKey("dictionary_entry.id", ondelete="SET NULL"), nullable=True)
    source = db.Column(db.String(24), nullable=False, default="manual")  # manual|teacher|dictionary|scene
    note = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)                       # JSON array
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # partial unique (user_id, item_id) and (user_id, dictionary_entry_id) where archived_at IS NULL
    # CHECK (item_id IS NOT NULL OR dictionary_entry_id IS NOT NULL)
```

`PronunciationAttempt` (today’s `speech_attempt`):

```python
class PronunciationAttempt(db.Model):
    __tablename__ = "speech_attempt"          # rename table in contract if desired
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id", ondelete="SET NULL"), nullable=True)
    item_form_id = db.Column(db.Integer, db.ForeignKey("item_form.id", ondelete="SET NULL"), nullable=True)
    target_text = db.Column(db.String(300), nullable=False)        # legacy/denormalized
    transcript = db.Column(db.String(500), nullable=False)
    overall_score = db.Column(db.Float, nullable=True)
    match_score = db.Column(db.Float, nullable=False)              # transcript match
    acceptable = db.Column(db.Boolean, nullable=False, default=False)
    provider = db.Column(db.String(30), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    phoneme_scores = db.Column(db.Text, nullable=True)             # JSON list
    prosody_scores = db.Column(db.Text, nullable=True)             # JSON
    duration_ms = db.Column(db.Integer, nullable=True)
    scoring_version = db.Column(db.String(24), nullable=False, default="transcript-v1")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
```

`TeacherSession` / `TeacherTurn` / `Drill` / `DrillAttempt`:

```python
class TeacherSession(db.Model):
    __tablename__ = "teacher_session"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("language.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=True)
    mode = db.Column(db.String(24), nullable=False, default="free")   # free|scene|drill|exam
    provider = db.Column(db.String(30), nullable=False)
    provider_session_id = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="pending")  # pending|active|ended|failed
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    turn_count = db.Column(db.Integer, nullable=False, default=0)
    cost_micros = db.Column(db.Integer, nullable=True)
    summary_text = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)


class TeacherTurn(db.Model):
    __tablename__ = "teacher_turn"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("teacher_session.id", ondelete="CASCADE"), nullable=False)
    turn_index = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(16), nullable=False)               # teacher|learner|system|tool
    text = db.Column(db.Text, nullable=True)
    lang = db.Column(db.String(12), nullable=True)
    tool_name = db.Column(db.String(40), nullable=True)
    tool_args = db.Column(db.Text, nullable=True)                 # JSON
    tool_result = db.Column(db.Text, nullable=True)               # JSON
    latency_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    # unique(session_id, turn_index)
```

### 2.4 Uniqueness, soft delete, and content versioning

**Uniqueness per language**

- `item`: partial unique `(language_id, item_type, key_normalized, sense_key)` where `deleted_at IS NULL`.
  - `key_normalized = pack.lemma_key(primary form text)`.
  - `sense_key` defaults to `pack.lemma_key(primary gloss)`, so Korean 개 “dog” and 개 “counter” can coexist without a separate migration.
  - This replaces `uq_item_content` (`app/models.py:95-98`), which wrongly includes English text and omits language.
- `item_form`: partial unique `(item_id, form_kind, normalized_text)` where `deleted_at IS NULL`. Allows citation form + particle variants + inflected forms.
- `dictionary_entry`: partial unique `(language_id, normalized_headword, pos)`.
- `dictionary_sense`: unique `(entry_id, sense_order)`.
- `translation`: unique `(source_language_id, target_language_id, sense_id, source_text_hash, quality)`; prevents duplicate machine translations and allows human-reviewed variants.
- `term_card`: partial unique `(user_id, item_id)` and `(user_id, dictionary_entry_id)` where `archived_at IS NULL`.
- `scene_session` / `can_do_artifact`: unique `(user_id, language_id, scene_slug)` (expand phase), later `scene_id`.
- `review_card`: keep `(user_id, item_id, skill)` exactly (`app/models.py:135-141`). Language is implicit via item.
- `teacher_turn`: unique `(session_id, turn_index)`.
- `drill_attempt`: unique `(drill_id, user_id, client_attempt_id)` for idempotent tool retries.

**Soft delete**

- `deleted_at` on item, item_form, item_gloss, dictionary_entry, dictionary_sense, drill.
- Queries in `learning/service.py` must filter `deleted_at IS NULL`. Do not delete rows referenced by `ReviewLog`/`ReviewCard`; deprecate by `status`/`deleted_at` and keep scheduling behavior or add `ReviewCard.suspended` later.
- Partial indexes work on SQLite 3.8+ and Postgres; the repo already uses a partial unique index for local users (`app/models.py:63-71`).

**Content versioning**

- `version` increments on material edits; `content_hash` stores a deterministic hash of form/gloss/morphology.
- `pack_version` is stored on generated content, translations, drills, and pronunciation attempts, so a pack change invalidates caches and flags stale content.
- Optional `content_revision` audit table:
  ```text
  content_revision(id, entity_type, entity_id, version, diff JSON, actor, created_at)
  ```
  Add only if native review requires an audit trail; do not build a CMS.

### 2.5 Script model: Hangul vs Ge’ez vs Latin vs Japanese

| Script | `script_type` | `composition` | Pack responsibilities |
|---|---|---|---|
| Hangul (`ko`) | `alphabet` (featural, block-written) | `block` | NFC normalize; optionally decompose jamo for drills; segment L/V/T; romanize RR/Yale; validate precomposed syllables and jamo. Current code only accepts `가-힣` (`app/utils/schemas.py:27`), so jamo input fails today. |
| Ge’ez / Fidel (`am`, Tigrinya) | `abugida` | `abugida` | Each fidel is a codepoint in the Ethiopic block with consonant + vowel-order metadata; no dynamic block composition. Normalize NFC; segment fidel; romanize BGN/PCGN or ALA-LC; validate Ethiopic ranges. |
| Latin (`es`) | `alphabet` | `linear` | NFC/NFD handling for accents; case fold; word tokenizer; inverted punctuation `¿¡`; gender/number morphology; romanization is identity (scheme `none`). |
| Japanese (`ja`) | `mixed` (hiragana/katakana/kanji) | `mixed` | Script-run segmentation, kana normalization, kanji reading via dictionary, Hepburn romanization; no simple unit catalog. |

Important: **do not try to force all scripts into one `script_unit` table for behavior.** Use `script`/`script_unit` for metadata, UI letters, and golden tests; use the pack for normalization/tokenization/romanization. This avoids modeling Hangul block composition and Ge’ez abugida order as the same thing.

### 2.6 Morphology and transliteration details

**Korean particle variants**

Store each surface variant as an `item_form` row in the same `form_group`:

```text
item "은/는" (grammar)
  form_group="eun-neun", form_kind="variant", text="은", form_condition="after_consonant"
  form_group="eun-neun", form_kind="variant", text="는", form_condition="after_vowel"
  morphology={"type":"particle","allomorphs":["은","는"],"feature":"topic"}
```

This makes variants reviewable and renderable (`item_form`), without needing a morphological analyzer at request time. The pack's validator checks that every variant is in the expected allomorph set.

**Amharic root-pattern**

```json
{
  "type": "root_pattern",
  "root": "s-b-r",
  "pattern": "CəCC",
  "template": "ሰብር",
  "features": {"aspect": "perfective", "person": "3sg", "gender": "m"}
}
```

Store on `item_form.morphology` with `morphology_family="root_pattern"`. The pack validates root consonants and allowed patterns; it does **not** auto-generate every paradigm cell. Generated forms are draft content until reviewed.

**Transliteration**

- `item_form.transliteration` is cached/derived, not authoritative.
- `transliteration_scheme` is a pack-defined string (`rr`, `yale`, `bgn_pcgn`, `ala_lc`, `hepburn`, `none`).
- Regenerate when `pack_version` changes; never mix schemes in one display path.
- UI shows target text first; transliteration is optional and labeled with the scheme when it is not the default.

### 2.7 Alembic migration path: expand → backfill → contract

**Release R1 — Expand (v0.5.0), zero user-visible risk**

New revision: `20261123_0011_language_core.py` (down_revision `20261019_0010`).

- Create: `language`, `script`, `language_script`, `level_scale`, `course`, `deck`, `deck_item`, `item_form`, `item_gloss`, `dictionary_entry`, `dictionary_sense`, `translation`, `term_card`, `teacher_session`, `teacher_turn`, `drill`, `drill_attempt`. Teacher tables can be created here even if unused; they are additive.
- Add nullable columns:
  - `item.language_id`, `item.primary_deck_id`, `item.dictionary_entry_id`, `item.key_normalized`, `item.sense_key`, `item.status`, `item.version`, `item.content_hash`, `item.deleted_at`, `item.superseded_by_id`.
  - `phrase.source_language_id`, `phrase.target_language_id` (leave `english_text`/`korean_text` until contract).
  - `speech_attempt.language_id`, `item_form_id`, `overall_score`, `phoneme_scores`, `prosody_scores`, `scoring_version`.
  - `scene_session.language_id`, `can_do_artifact.language_id`, `event.language_id`, `user.target_language_id`, `user.ui_locale`, `conversation.language_id`.
- Create non-unique indexes only in R1. Do **not** add `NOT NULL` yet; do **not** change app reads.

New revision: `20261123_0012_backfill_korean.py`.

- Insert:
  ```sql
  INSERT INTO language (code, name, native_name, direction, is_active)
  VALUES ('ko', 'Korean', '한국어', 'ltr', 1);
  INSERT INTO script (code, name, script_type, direction, composition)
  VALUES ('hangul', 'Hangul', 'alphabet', 'ltr', 'block');
  INSERT INTO language_script (language_id, script_id, role, is_default) ...
  INSERT INTO level_scale (language_id, code, min_level, max_level, labels)
  VALUES ((SELECT id FROM language WHERE code='ko'), 'topik', 1, 6, '{...}');
  ```
- Backfill:
  ```sql
  UPDATE item SET language_id = (SELECT id FROM language WHERE code='ko') WHERE language_id IS NULL;
  UPDATE phrase SET source_language_id = (SELECT id FROM language WHERE code='en') ...;
  UPDATE phrase SET target_language_id = (SELECT id FROM language WHERE code='ko') ...;
  UPDATE speech_attempt SET language_id = (SELECT id FROM language WHERE code='ko') ...;
  UPDATE scene_session SET language_id = (SELECT id FROM language WHERE code='ko') ...;
  UPDATE can_do_artifact SET language_id = (SELECT id FROM language WHERE code='ko') ...;
  ```
  Seed an `en` language row too (Kiku currently uses English as the source/gloss language). This is a language, even if the UI is English.
- Copy item content:
  ```sql
  INSERT INTO item_form (item_id, script_id, form_kind, text, normalized_text,
                         transliteration, transliteration_scheme, audio_path,
                         is_primary, version)
  SELECT i.id, s.id, 'citation', i.korean, i.korean, i.romanization, 'rr',
         i.audio_path, 1, 1
  FROM item i, script s
  WHERE s.code = 'hangul' AND NOT EXISTS (SELECT 1 FROM item_form f WHERE f.item_id = i.id);
  ```
- Copy glosses:
  ```sql
  INSERT INTO item_gloss (item_id, lang, text, gloss_type, is_primary, version)
  SELECT id, 'en', english, 'translation', 1, 1 FROM item
  WHERE NOT EXISTS (SELECT 1 FROM item_gloss g WHERE g.item_id = item.id AND g.lang='en');
  ```
- Backfill `key_normalized` and `sense_key` in a separate CLI/job (`flask backfill-content --language ko`) because normalization is pack logic, not SQL. For Korean, `key_normalized = text` is safe for NFC precomposed data; the CLI verifies with the pack.
- After backfill, create partial unique indexes (Postgres and SQLite support them):
  - `uq_item_language_type_key` on `(language_id, item_type, key_normalized, sense_key)` where `deleted_at IS NULL`.
  - `uq_item_form_item_kind_text` on `(item_id, form_kind, normalized_text)` where `deleted_at IS NULL`.
  - `uq_dictionary_entry_language_headword_pos` on `(language_id, normalized_headword, pos)` where `deleted_at IS NULL`.
- Replace scene/can-do uniqueness only after the old constraint can be dropped. In R1, keep old unique constraints; add new indexes non-unique or unique where data permits. The old `(user_id, scene_slug)` unique still blocks same slug across languages; drop it in R3 before the second language ships.

**Release R2 — Dual-write (v0.6.0)**

- Application writes both legacy columns and new tables. Introduce repository methods (`ItemRepository.create`, `ItemRepository.update`) and SQLAlchemy `before_flush`/service hooks rather than editing every route.
- Reads still default to legacy columns for ko; new language paths read `item_form`/`item_gloss`.
- Add `NOT NULL` to new columns only after a verified backfill:
  ```python
  with op.batch_alter_table("item") as batch:
      batch.alter_column("language_id", existing_type=sa.Integer(), nullable=False)
  ```
  SQLite requires batch mode; Alembic handles table rebuild. Do this in a separate revision (`0013_language_not_null.py`) after a data audit.
- Add `scene_session.language_id` / `can_do_artifact.language_id` NOT NULL and new unique indexes.
- No user-visible change; run both write paths in CI.

**Release R3 — Contract (v0.7.0)**

New revision: `20261123_0014_contract_remove_korean_columns.py`.

- `batch_alter_table("item")`:
  - drop `korean`, `english`, `romanization`;
  - drop `uq_item_content` (SQLite rebuild);
  - keep `level`, `freq_rank`, `notes` (or move notes to `item_gloss`).
- `batch_alter_table("phrase")`:
  - rename `english_text` → `source_text`, `korean_text` → `target_text`;
  - add `source_language_id`/`target_language_id` NOT NULL.
- `batch_alter_table("speech_attempt")`:
  - make `language_id` NOT NULL; keep `target_text` for compatibility/denormalized display; add `item_form_id` FK; rename model class/table to `pronunciation_attempt` only if API compatibility is not required (otherwise keep table name).
- `scene_session` / `can_do_artifact`: drop old unique constraints, enforce `(user_id, language_id, scene_slug)`.
- Drop legacy columns only after one production release of dual-write and a verified row-count/content-hash report.
- Downgrade restores schema but cannot restore dropped text; document “schema-reversible, data-lossy.” CI migration tests should run downgrade only on the expand/backfill revisions, and empty-DB downgrade for the contract revision.

**What if we must avoid dropping columns?**
Keep them as generated/denormalized columns indefinitely. But that leaves `korean`/`english` names in the schema and invites accidental use. For a real multi-language product, contract is worth it. If the product owner wants zero risk, use a “compatibility view” or model synonyms and defer the contract beyond R3.

### 2.8 SQLite/Alembic specifics

- SQLite cannot drop/alter columns/constraints in place; use `op.batch_alter_table` for any rename/drop/NOT NULL change. Flask-Migrate 3.1/Alembic supports this.
- Do not use `Base.metadata.create_all()` in migrations; migrations must be standalone SQLAlchemy operations.
- New tables are created with `op.create_table`, which works on empty and existing DBs.
- Partial index syntax differs slightly:
  ```python
  op.create_index(
      "uq_item_language_type_key", "item",
      ["language_id", "item_type", "key_normalized", "sense_key"],
      unique=True,
      sqlite_where=sa.text("deleted_at IS NULL"),
      postgresql_where=sa.text("deleted_at IS NULL"),
  )
  ```
- **Circular FKs need deliberate ordering.** `language.default_level_scale_id → level_scale.id` while `level_scale.language_id → language.id`, and `item.dictionary_entry_id → dictionary_entry.id` while `dictionary_entry.lemma_item_id → item.id`. Create the tables without one side of each FK, then add the constraint with `op.create_foreign_key(..., use_alter=True)` (or in a second `batch_alter_table` for SQLite). Do not let SQLAlchemy sort create order alphabetically.
- This repo’s CI migrates an empty SQLite DB and then asserts tables (`.github/workflows/ci.yml:30-74`). Add the new table names to that gate and add a second test path: build the old schema at `20261019_0010`, insert representative rows, then upgrade to head and assert backfill.

### 2.9 Preserving data and test DB bootstrap

- **Data:** all R1/R2 migrations are additive and idempotent (`WHERE ... IS NULL`, `NOT EXISTS`). Backfill maps 30 seed items, existing phrases, speech attempts, scenes, and can-dos to `ko`. No rows are deleted.
- **Test bootstrap:** `tests/conftest.py:173-174` calls `db.create_all()`, not migrations. Every new model must be imported from `app/models.py` (directly or via `app/models_language.py` imported at the bottom) so `db.metadata` includes it. Keep `create_all` fast; add a parity test comparing `db.metadata.tables` to the migrated schema so the CI gate and test bootstrap cannot drift.
- **Feature flag:** `MULTILINGUAL_READS=False` in R1/R2; pages behave exactly as today. `DEFAULT_LANGUAGE="ko"`; `LANGUAGES_ENABLED="ko"`.

---

## 3. Service abstraction

### 3.1 `LanguagePack` protocol

Location: `app/languages/base.py`. It is a `typing.Protocol`, not an abstract base class, so packs can be simple objects/modules and tests can fake them.

```python
from dataclasses import dataclass
from typing import Literal, Mapping, Protocol, Sequence

LanguageCode = str          # "ko", "am", "es", "ja"
ScriptCode = str
TextKind = Literal["word", "phrase", "sentence", "lesson", "transcript"]

@dataclass(frozen=True)
class ScriptSpec:
    code: ScriptCode
    name: str
    script_type: Literal["alphabet", "abjad", "abugida", "syllabary", "logosyllabic", "mixed"]
    direction: Literal["ltr", "rtl"]
    unicode_ranges: tuple[tuple[int, int], ...]
    composition: Literal["linear", "block", "abugida", "mixed"]
    normalization: Literal["NFC", "NFD", "NFKC"] = "NFC"

@dataclass(frozen=True)
class LevelBand:
    value: int
    label: str
    descriptor: str = ""

@dataclass(frozen=True)
class LevelScale:
    code: str                      # "topik", "cefr", "jlpt", "custom_am"
    bands: tuple[LevelBand, ...]
    def label(self, value: int) -> str: ...
    def band(self, value: int) -> LevelBand | None: ...

@dataclass(frozen=True)
class ASRProfile:
    provider: str                  # "openai", "azure", "local"
    language_code: str             # "ko", "am", "es", "ja"
    model: str
    supports_word_timestamps: bool = False
    supports_phoneme_timestamps: bool = False
    hints: tuple[str, ...] = ()    # expected vocabulary / decoding hints

@dataclass(frozen=True)
class TTSProfile:
    provider: str
    language_code: str             # "ko-KR", "am-ET", "es-ES", "ja-JP"
    model: str
    voices: Mapping[str, str]      # role -> provider voice id: {"default": "onyx", "teacher": "nova"}
    speed: float = 1.0

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    normalized: str
    issues: tuple[ValidationIssue, ...] = ()

@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    kind: Literal["word", "particle", "grapheme", "punctuation"]

@dataclass(frozen=True)
class ItemCandidate:
    language: LanguageCode
    item_type: str
    text: str
    gloss: str
    transliteration: str | None
    script: ScriptCode
    morphology: dict | None = None
    level: int = 1

class LanguagePack(Protocol):
    code: LanguageCode
    name: str
    native_name: str
    direction: Literal["ltr", "rtl"]
    pack_version: str
    scripts: tuple[ScriptSpec, ...]
    default_script: ScriptSpec
    level_scale: LevelScale
    asr: ASRProfile
    tts: TTSProfile

    def normalize(self, text: str) -> str: ...
    def tokenize(self, text: str) -> list[Token]: ...
    def romanize(self, text: str, scheme: str | None = None) -> str: ...
    def lemma_key(self, text: str) -> str: ...
    def validate_text(self, text: str, *, kind: TextKind = "sentence") -> ValidationResult: ...
    def validate_item(self, candidate: ItemCandidate) -> ValidationResult: ...
    def morphology_schema(self, family: str) -> dict: ...
    def pronunciation_target(self, text: str) -> PronunciationTarget: ...
    def curriculum(self) -> CurriculumSource: ...
```

`CurriculumSource` is a thin read interface over the pack directory:

```python
class CurriculumSource(Protocol):
    def seed_items(self) -> list[ItemCandidate]: ...
    def script_lessons(self) -> list[dict]: ...
    def scenes(self) -> list[dict]: ...
    def sound_gym(self) -> dict: ...
    def first_utterance(self) -> dict: ...
    def goals(self) -> list[dict]: ...
    def experience_levels(self) -> list[dict]: ...
```

### 3.2 Provider protocols

Location: `app/services/providers/base.py`.

```python
@dataclass(frozen=True)
class TranslationRequest:
    text: str
    source_lang: LanguageCode
    target_lang: LanguageCode
    context_item_ids: tuple[int, ...] = ()
    register: str | None = None

@dataclass(frozen=True)
class TranslationResult:
    text: str
    provider: str
    model: str
    confidence: float | None = None
    raw: dict | None = None

class TranslationProvider(Protocol):
    name: str
    def translate(self, request: TranslationRequest) -> TranslationResult: ...

@dataclass(frozen=True)
class TTSRequest:
    text: str
    language: LanguageCode
    profile: TTSProfile
    voice_role: str = "default"
    response_format: Literal["mp3", "wav"] = "mp3"

@dataclass(frozen=True)
class AudioArtifact:
    path: str
    mime_type: str
    duration_ms: int | None

class TTSProvider(Protocol):
    name: str
    def synthesize(self, request: TTSRequest, destination: str) -> AudioArtifact: ...

@dataclass(frozen=True)
class ASRRequest:
    audio: bytes
    filename: str
    content_type: str
    language: LanguageCode
    profile: ASRProfile
    hints: tuple[str, ...] = ()

@dataclass(frozen=True)
class TranscriptResult:
    text: str
    provider: str
    model: str
    language: LanguageCode
    words: tuple[dict, ...] = ()
    confidence: float | None = None

class ASRProvider(Protocol):
    name: str
    def transcribe(self, request: ASRRequest) -> TranscriptResult: ...

@dataclass(frozen=True)
class PhonemeScore:
    phoneme: str
    expected: str | None
    observed: str | None
    score: float
    start_ms: int | None = None
    end_ms: int | None = None

@dataclass(frozen=True)
class PronunciationScore:
    overall: float
    acceptable: bool
    transcript: str
    phonemes: tuple[PhonemeScore, ...]
    prosody: dict
    provider: str
    model: str
    scoring_version: str

class PronunciationScorer(Protocol):
    name: str
    def score(self, audio: bytes, target: PronunciationTarget, *, language: LanguageCode) -> PronunciationScore: ...

@dataclass(frozen=True)
class ContentCandidate:
    language: LanguageCode
    item_type: str
    source_item_ids: tuple[int, ...]
    text: str
    gloss: str
    transliteration: str | None
    morphology: dict | None
    provider: str
    model: str
    prompt_version: str

class ContentValidator(Protocol):
    name: str
    def validate(self, candidate: ContentCandidate, pack: LanguagePack) -> ValidationResult: ...

@dataclass(frozen=True)
class DrillRequest:
    language: LanguageCode
    deck_id: int
    item_ids: tuple[int, ...]
    drill_type: str
    count: int = 1
    difficulty: str | None = None

class DrillGenerator(Protocol):
    name: str
    def generate(self, request: DrillRequest, pack: LanguagePack) -> list[DrillDraft]: ...

class TeacherEngine(Protocol):
    name: str
    def create_session(self, context: TeacherContext) -> TeacherSessionHandle: ...
    def mint_client_token(self, handle: TeacherSessionHandle) -> EphemeralToken: ...
    def handle_tool_call(self, session_id: int, call: ToolCall) -> ToolResult: ...
    def end_session(self, handle: TeacherSessionHandle, reason: str) -> TeacherSummary: ...
```

`TeacherContext`, `TeacherSessionHandle`, `EphemeralToken`, `ToolCall`, `ToolResult` are dataclasses in the same module; see §4.

### 3.3 Dependency injection with the existing extension pattern

Today’s pattern is exactly what we need:

- `app/__init__.py:300-304` installs `app.extensions["rate_limiter"]`.
- `app/services/ai.py:57-95` checks `current_app.extensions["openai_client"]` before lazily creating a real client.
- `tests/conftest.py:168` injects `FakeOpenAIClient` into that extension.

Proposed service registry:

```python
# app/services/registry.py
@dataclass(frozen=True)
class Services:
    translation: TranslationProvider
    tts: TTSProvider
    asr: ASRProvider
    pronunciation: PronunciationScorer
    validator: ContentValidator
    drills: DrillGenerator
    teacher: TeacherEngine | None

def get_services() -> Services:
    services = current_app.extensions.get("services")
    if services is None:
        services = build_services(current_app)
        current_app.extensions["services"] = services
    return services

def service_for(name: str):
    services = get_services()
    return getattr(services, name)
```

`build_services(app)` reads:

1. `app.extensions["service_overrides"]` (tests, always wins).
2. `app.extensions["service_factories"][name]` (plugins).
3. Config `AI_PROVIDER` / `TRANSLATION_PROVIDER` / `TTS_PROVIDER` / `ASR_PROVIDER` (deployment).
4. Default OpenAI adapters.

Per-language resolution happens at call time using the pack profile, not by rebuilding the service object:

```python
translation = get_services().translation
result = translation.translate(TranslationRequest(
    text=text,
    source_lang="en",
    target_lang=pack.code,
    context_item_ids=(...),
))
```

For providers that differ by language (e.g. Azure for Amharic ASR, OpenAI for Korean), add a router:

```python
class ProviderRouter:
    def __init__(self, mapping: dict[str, Provider], default: Provider): ...
    def for_language(self, lang: str) -> Provider: ...
```

`ASRProvider`/`TTSProvider` are stateless and receive the pack profile in the request; the router selects the vendor implementation. This keeps the call sites language-agnostic.

Backward compatibility:

- Keep `get_openai_client()` and `set_openai_client_for_testing()` (`app/services/ai.py:63-110`). OpenAI adapters call it internally.
- Keep module-level `translate_to_korean()` as a thin wrapper for one release; it resolves `pack("ko")` and calls the generic provider. Same for `score_audio`/`transcribe_audio`, which delegate to `get_services().asr` and pack normalization.
- Existing test fakes continue to work through `extensions["openai_client"]` because the OpenAI adapter uses the injected client.

### 3.4 Keeping content generation constrained to DB item IDs

This is non-negotiable for curriculum quality and prompt-injection safety.

**Rule:** every generated curriculum artifact must name existing `item_id`s in the same language, and must pass `ContentValidator` + `LanguagePack` before it is persisted. No free-text “invent a word” path in public APIs.

```python
def generate_drill(request: DrillRequest, *, pack: LanguagePack) -> list[DrillDraft]:
    allowed = Item.query.filter(
        Item.id.in_(request.item_ids),
        Item.language_id == language_id_for(pack.code),
        Item.deleted_at.is_(None),
        Item.status == "published",
    ).all()
    if len(allowed) != len(set(request.item_ids)):
        raise ContentValidationError("Drill requested unknown or out-of-language items")

    drafts = get_services().drills.generate(request, pack)
    for draft in drafts:
        if draft.source_item_id not in {item.id for item in allowed}:
            raise ContentValidationError("Model referenced an item outside the allowlist")
        result = get_services().validator.validate(draft.as_candidate(), pack)
        if not result.ok:
            raise ContentValidationError(result.issues)
    return drafts
```

Persistence:

- `translation` rows start `quality="machine"`, `is_human_reviewed=False`.
- `drill` rows start `validated=False` and `status="draft"`; `validated=True` only after `ContentValidator` and an optional native review.
- Any route that turns model output into learner-visible curriculum must check `validated` and `review_status`.
- Teacher tool calls use the same allowlist: `create_drill` accepts only `item_ids` returned by `search_dictionary` in that session or already in the session’s deck.
- Personal/teacher-only items are stored in a private deck with `status="user_private"`; they are never globally published and still go through the pack validator.

### 3.5 Config matrix

| Setting | Current | Target |
|---|---|---|
| `DEFAULT_LANGUAGE` | implicit `ko` | `ko` (env) |
| `LANGUAGES_ENABLED` | implicit all | `ko,am` (allowlist; packs discoverable) |
| `AI_PROVIDER` | implicit OpenAI | `openai`, `azure`, `gemini`, `local` |
| `TRANSLATION_PROVIDER` / `TTS_PROVIDER` / `ASR_PROVIDER` | global models/voices | provider names; per-language overrides in pack |
| `TTS_MODEL` / `SPEECH_TRANSCRIBE_MODEL` | global (`config.py:45, 68-70`) | deployment defaults; pack profile wins for language-specific model/voice |
| `SPEECH_ACCEPT_THRESHOLD` | 0.72 global (`config.py:72`) | default; pack may override per language/script |
| `TEACHER_ENABLED` | absent | `false` by default |
| `TEACHER_PROVIDER` | absent | provider name |
| `TEACHER_MAX_SESSION_MINUTES` | absent | 30 |
| `TEACHER_DAILY_BUDGET_MICROS` | absent | per-user cap |
| `TRANSLATION_CACHE_VERSION` | `translation-prompt-v2` (`app/services/translation.py:19`) | includes `pack_version` and target language |

---

## 4. Teacher subsystem architecture

### 4.1 Framework-agnostic building blocks

Three layers:

1. **Provider adapter** (`app/services/teacher/providers/<vendor>.py`) — knows how to create a realtime session, mint ephemeral client tokens, receive tool calls/events, and close a session. WebRTC vs WebSocket is an adapter detail.
2. **Teacher engine** (`app/services/teacher/engine.py`) — owns session state machine, persistence, tool allowlist, budget, and transcript policy.
3. **HTTP/UI layer** (`app/teacher/routes.py`, `app/templates/teacher_*.html`, `app/static/js/teacher.js`) — creates sessions, renders the text/voice panel, lists past sessions, exposes drill results.

### 4.2 Session lifecycle

```text
POST /api/teacher/sessions
  -> auth + CSRF + rate limit
  -> resolve language pack + course/deck
  -> TeacherEngine.create_session(ctx)
       -> insert TeacherSession(status="pending")
       -> provider.create_session() -> provider_session_id
       -> insert initial TeacherTurn(role="system", text=pack.teacher_intro)
  -> server mints ephemeral client token (short TTL)
  -> update token_expires_at, status="active"
  -> return {session_id, token, expires_at, provider, ws_url/rtc_config}
       (never returns the provider API key)

client connects directly to provider (or app WS relay)
  -> provider events / tool calls -> app webhook or WS control channel
  -> TeacherEngine.handle_tool_call(session_id, call)
       -> validate signature/session/user/language
       -> dispatch allowlisted tool
       -> append TeacherTurn(role="tool", tool_name=..., tool_args=..., tool_result=...)
  -> client transcript events -> append TeacherTurn(role="teacher"|"learner")

POST /api/teacher/sessions/<id>/end
  -> provider.close()
  -> optional summary generation from transcript
  -> TeacherSession.status="ended", ended_at, cost_micros, summary_text
  -> record_event("teacher_session_ended", language=..., turns=...)
```

Rules:

- `status` transitions only `pending→active→ended` or `pending→failed` / `active→failed`.
- `TeacherSession.provider_session_id` is the provider’s ID; `token_expires_at` is server time, not trusted from the client.
- A session is one language. Switching language creates a new session.
- Hard cap `TEACHER_MAX_SESSION_MINUTES`; background job (or `ended_at` check) expires abandoned sessions and marks failed.
- Raw audio is not stored, consistent with `SpeechAttempt` policy (`app/models.py:269`). Transcripts are stored; configurable retention.

### 4.3 Ephemeral token minting (server-side only)

- Only the backend holds provider credentials (`OPENAI_API_KEY` etc., `config.py:42`).
- `POST /api/teacher/sessions` calls `TeacherEngine.mint_client_token(handle)`.
- The token is scoped to one session, one user, one language, short TTL (e.g. 60 seconds to connect; session max 30 minutes).
- Return only `{session_id, token, expires_at, provider, connection_hints}`.
- Never log the token; store only its hash if audit is needed.
- Rate limit with `app.utils.rate_limit:78-121` and require auth/CSRF; teacher sessions are not available in local anonymous mode without an explicit owner.
- If token minting fails, mark session `failed`, no charge, and return 503.

### 4.4 Tool contracts

`app/services/teacher/tools.py` defines an allowlist. Each tool has a JSON schema, a handler, and a scope.

| Tool | Args (validated) | Returns | Side effects |
|---|---|---|---|
| `search_dictionary` | `query: str`, `pos: str?`, `limit: int ≤ 10` | `[{entry_id, item_id, headword, transliteration, senses, audio_url, level}]` | None (read-only) |
| `create_drill` | `item_ids: [int]` (≤ 5), `drill_type: enum`, `count: 1–3` | `[{drill_id, prompt, expected, item_id}]` | Inserts `drill` rows with `validated=false`; runs `DrillGenerator` + `ContentValidator` |
| `add_to_library` | `item_id?: int`, `dictionary_entry_id?: int`, `note?: str` | `{term_card_id, item_id?, entry_id?}` | Inserts/updates `TermCard`; if neither canonical ID exists, rejects (teacher cannot invent a global item) |
| `log_attempt` | `drill_id: int`, `response: str`, `score?: float`, `duration_ms?: int`, `client_attempt_id: str` | `{attempt_id, acceptable, review_card_id?}` | Inserts `DrillAttempt`; idempotent via unique key; may create/refresh `ReviewCard` |

Dispatcher:

```python
@dataclass(frozen=True)
class ToolContext:
    user_id: int
    language_id: int
    session_id: int
    allowed_item_ids: frozenset[int]
    allowed_deck_ids: frozenset[int]

class TeacherToolRouter:
    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> ToolResult:
        spec = TOOL_SPECS.get(name)
        if spec is None:
            return ToolResult.error("unknown_tool")
        try:
            validated = spec.schema.validate(args)
        except ValidationError as exc:
            return ToolResult.error("invalid_args", detail=exc)
        if spec.name == "create_drill":
            requested = set(validated["item_ids"])
            if not requested <= ctx.allowed_item_ids:
                return ToolResult.error("item_out_of_scope")
        return spec.handler(validated, ctx)
```

Tool results returned to the model are **text/JSON summaries**, never raw ORM objects or provider secrets. The model must not see other users’ data.

### 4.5 Persistence and transcripts

- Append-only `TeacherTurn` rows; `turn_index` monotonic per session.
- Tool calls and results are stored as JSON on the turn that invoked them.
- `TeacherSession.summary_text` is a short generated/curated summary; `metadata_json` stores provider metadata, not secrets.
- `cost_micros` is computed by the adapter from provider usage; use it for budgets.
- Add `event` rows for session start/end/tool calls/drill attempts for analytics, with `language_id`.
- Retention: `TEACHER_TRANSCRIPT_RETENTION_DAYS`; a CLI/job deletes old turns/summaries. No raw audio.

### 4.6 How drills flow back into FSRS

Do **not** build a second scheduler.

- `DrillAttempt` records the teacher-generated practice result.
- If the learner’s attempt is acceptable and the drill links to an `item_id`:
  - Find an existing `ReviewCard` for `(user, item, skill)`.
  - If absent, create one with `new_review_card(user_id, item_id, skill)` (`app/learning/scheduler.py:42-58`), due now, `reps=0`.
  - Do **not** call `apply_rating` from a teacher drill (that would fabricate a review). Let the next normal review grade it.
  - Optionally set a `review_hint`/priority flag on the card; store it in `DrillAttempt.review_card_id`.
- If the learner added a personal phrase via `add_to_library`:
  - It lives in a private deck as an `Item` with `status="user_private"` after pack/validator checks.
  - “Start practicing” creates the `ReviewCard`.
  - If the user only saved it, keep `TermCard` with no card.
- A teacher session summary can show “3 new cards added”; the Today page picks them up through the existing `available_cards()` query, scoped to the learner’s target language.

### 4.7 UI: dictionary/library feed

- `GET /api/dictionary?lang=am&q=...` searches `dictionary_entry`/`senses` scoped by `language_id`, returns display-ready fields and `item_id`/`entry_id`.
- `GET /api/library?lang=am` returns `TermCard` rows with item/entry data.
- `/library` template renders `TermCard` instead of raw `Phrase` rows (or renders both during transition).
- Search results and library entries expose a “Practice” action that filters the review queue by `item_id`/`deck_id` (e.g. `session["review_item_ids"]` or a `deck=` query param). No new scheduler semantics.
- Teacher panel and dictionary share the same `item_id`/`entry_id` identifiers; the model never sees opaque text-only IDs.

### 4.8 Failure, security, and abuse

- Provider unavailable: `POST /sessions` returns 503, no session row or a `failed` row; never mint a token.
- Tool failure: return `ToolResult.error` to the model; persist the failed tool turn; do not create partial content.
- Duplicate tool calls/retries: `client_attempt_id` and `turn_index` make `log_attempt` idempotent.
- Prompt injection: tool args are schema-validated; item IDs are intersected with the session allowlist; no SQL/paths from model text; dictionary results are data, never instructions.
- Auth: teacher sessions require a real user; the current local single-user mode is not sufficient for a public teacher.
- Budget: per-user daily minutes/cost; provider adapter reports usage; engine refuses new sessions above cap.
- Privacy: no raw audio storage; transcripts retention config; delete endpoint; no provider keys in browser.

---

## 5. Language pack layout

### 5.1 Concrete tree

```text
app/languages/
  __init__.py                 # discover_packs(), LanguageRegistry, get_pack(), current_pack()
  base.py                     # LanguagePack, ScriptSpec, LevelScale, Token, ValidationResult, protocols
  loader.py                   # JSON/py loading, schema validation, pack_version, content_hash
  errors.py                   # PackNotFound, PackValidationError
  ko/
    __init__.py               # exports KoreanPack
    manifest.json             # code, name, native_name, scripts, default_level_scale, pack_version
    pack.py                   # KoreanPack: normalize/tokenize/romanize/validate/curriculum
    romanization.py           # RR + Yale rules
    validation.py             # Hangul ranges, jamo/precomposed rules
    script/
      hangul.json             # script metadata, jamo units, unicode ranges
      lessons/
        01-letters.json
        02-vowels-and-blocks.json
        ...                   # 7 lessons total, moved from hangul_data.py
    curriculum/
      seed_items.json         # 30 items, generic keys
      scenes/
        cafe-order.json
        directions.json
        pharmacy.json
        workplace-intro.json
      goals.json              # Everyday, Travel, Work, K-drama, TOPIK, Family
      experience.json
    sound_gym/
      minimal_pairs.json      # 11 pairs
      production_prompts.json # 8 prompts
    morphology/
      particles.json          # 은/는, 이/가, 을/를, 에/에서 allomorphs
    assets/
      fonts.css               # optional @font-face for Hangul
  am/
    __init__.py
    manifest.json
    pack.py                   # AmharicPack: Ethiopic normalization, fidel segmentation, BGN/PCGN
    romanization.py
    validation.py
    script/
      fidel.json              # Ethiopic ranges, consonant/vowel-order metadata
      lessons/
        01-fidel-family.json
        ...
    curriculum/
      seed_items.json
      scenes/                 # optional at first
      goals.json
      experience.json
    sound_gym/
      minimal_pairs.json      # ejectives/glottalized contrasts
      production_prompts.json
    morphology/
      root_patterns.json
    assets/fonts.css
  es/
    ...                       # Latin alphabet, CEFR, gender/number, inverted punctuation
  ja/
    ...                       # mixed scripts, JLPT, kana/kanji, pitch/gemination
  shared/
    schemas/
      manifest.schema.json
      seed_item.schema.json
      scene.schema.json
      sound_gym.schema.json
      lesson.schema.json
      drill.schema.json
    prompts/
      translation.md
      conversation.md
      teacher.md
      drill_generation.md
```

### 5.2 Current → target file map

| Current | Target | Notes |
|---|---|---|
| `app/learning/hangul_data.py` (1,485 lines) | `app/languages/ko/script/lessons/*.json` + `script/hangul.json` | Keep a shim `app/learning/hangul_data.py` exporting `HANGUL_LESSONS = get_pack("ko").script_lessons` for one release so `routes.py:26` and `tests/test_hangul_data.py` do not break in Phase 2. |
| `app/learning/scene_data.py` (467 lines) | `app/languages/ko/curriculum/scenes/*.json` | Rename keys: `character_korean`→`character_text`, `character_english`→`character_translation`, `target_item.korean`→`target_item.text`, `target_item.english`→`target_item.gloss`, `kanji` none. |
| `app/learning/seed_data.py` (67 lines) | `app/languages/ko/curriculum/seed_items.json` + generic `app/learning/seed.py` | Keys: `text`, `gloss`, `transliteration`, `item_type`, `level`, `default_skill`, `notes`, `script`. |
| `app/learning/sound_gym_data.py` (214 lines) | `app/languages/ko/sound_gym/*.json` | Generic keys: `words[].text/transliteration/gloss`, `contrast`, `tip`, `level`. |
| `app/learning/scenes.py` | `app/learning/scenes.py` becomes pack-driven | `get_scene(pack, slug)`, `list_scenes_with_status(pack, ...)`, `_normalize` calls `pack.normalize`, `_create_debrief_cards` reads generic fields. |
| `app/learning/routes.py:26, 54` + `app/learning/scenes.py:11` imports | `app/learning/routes.py`/`scenes.py` import the registry, not data | `get_pack(lang)` per request. |
| `app/templates/hangul_index.html`, `hangul_lesson.html` | `app/templates/script_index.html`, `script_lesson.html` | Generic `lesson`, `script`, `pack`; route alias `/learn/hangul` redirects for ko. |
| `app/static/js/hangul.js` | `app/static/js/script_drills.js` | Reads `data-script`, `data-tts-lang`; no Hangul-specific logic. |
| `app/static/js/sound_gym.js` | `app/static/js/sound_gym.js` generic | `data-target`, `data-script`, `data-tts-lang`. |
| `hangul.py` (root) | `tools/translate_cli.py --lang` | Low priority; not on web path. |

### 5.3 Loader and registry (caching)

`app/languages/loader.py`:

```python
@lru_cache(maxsize=None)
def load_pack(code: str) -> LanguagePack:
    manifest = read_json(pack_dir(code) / "manifest.json")
    validate(manifest, MANIFEST_SCHEMA)
    module = import_module(f"app.languages.{code}.pack")
    pack = module.build_pack(manifest)
    validate_pack(pack)                 # scripts, level scale, asr/tts, curriculum
    return pack

class LanguageRegistry:
    def __init__(self, packs: Mapping[str, LanguagePack], enabled: set[str]): ...
    def get(self, code: str) -> LanguagePack: ...
    def all(self) -> list[LanguagePack]: ...
    def reload(self): load_pack.cache_clear()
```

- Primary key is `language.code` (`ko`, `am`); URL codes are the same.
- `pack_version` comes from `manifest.json`; bump it when content/behavior changes.
- `content_hash` is computed from JSON files + pack code version; used in caches and golden tests.
- Register in `create_app`:
  ```python
  from app.languages import LanguageRegistry
  app.extensions["languages"] = LanguageRegistry.from_config(app.config)
  ```
- `current_pack()` resolves: `g.language`/session/user target → path `lang` → `DEFAULT_LANGUAGE` → `ko`.
- Cache key for translation/audio includes `pack_version`, `target_lang`, `scheme`, `voice`.

### 5.4 Adding a language without touching core code

Checklist for `am`:

1. `mkdir app/languages/am` with `manifest.json`.
2. Implement `pack.py` (`AmharicPack`) with `normalize`, `tokenize`, `romanize`, `validate_text`, `validate_item`, `morphology_schema`.
3. Add `script/fidel.json` + `script/lessons/*.json`.
4. Add `curriculum/seed_items.json` (at least 30 reviewed items), `goals.json`, `experience.json`.
5. Add `sound_gym/minimal_pairs.json` + `production_prompts.json`.
6. Add `morphology/root_patterns.json`.
7. Add `assets/fonts.css` if needed.
8. Add `tests/golden/am/*.json`.
9. Add `am` to `LANGUAGES_ENABLED` (config/env) if an allowlist is used.
10. Run pack contract tests. **No edits to `app/models.py`, `app/learning/routes.py`, `app/templates`, or core services.**

The only core registration is auto-discovery (`pkgutil.iter_modules`) or an explicit `LANGUAGES` config list. Prefer auto-discovery with an allowlist for production; it prevents a stray directory from becoming live.

---

## 6. Phased refactor plan

### 6.1 Phase overview

| Phase | Deliverable | User-visible? | Migration | Effort | Risk |
|---|---|---|---|---|---|
| **1** | Additive language schema + ko backfill | **No** | 0011 create, 0012 backfill | S/M | Low |
| **2** | Language packs + content extraction (ko) | **No** | none | M | Low/Med |
| **3** | Dual-write + language-scoped reads | No (default ko) | 0013 NOT NULL/indexes | L | Med |
| **4** | Provider abstraction + content validator | No (same behavior for ko) | none | M/L | Med |
| **5** | Language-scoped URLs + generic UI/JS | Yes (language picker; ko unchanged) | optional | L | Med |
| **6** | Contract schema + soft delete/versioning | Minimal | 0014 contract | M | Med/High |
| **7** | Real-time teacher MVP (ko) | Yes (opt-in flag) | 0015 teacher | L/XL | High |
| **8** | Amharic pilot pack | Yes (new language) | none | L | Med |

### 6.2 Phase 1 — Additive schema + backfill (zero user-visible risk)

**Files**

- New `app/models_language.py` with `Language`, `Script`, `LanguageScript`, `LevelScale`, `Course`, `Deck`, `DeckItem`, `ItemForm`, `ItemGloss`, `DictionaryEntry`, `DictionarySense`, `Translation`, `TermCard`, `TeacherSession`, `TeacherTurn`, `Drill`, `DrillAttempt`, `PronunciationAttempt` (or `SpeechAttempt` extension).
- `app/models.py`: add nullable columns to existing classes; import `app.models_language` at the bottom so `db.metadata` sees new tables. Do not add properties or change `to_dict`.
- New migrations:
  - `migrations/versions/20261123_0011_language_core.py`
  - `migrations/versions/20261123_0012_backfill_korean.py`
- New CLI `flask backfill-content --language ko` for pack-based normalization/hash (does not run on boot).
- New tests:
  - `tests/test_migrations_multilingual.py` (old→new data migration)
  - `tests/test_language_backfill.py` (row counts, form text equals `item.korean`, gloss equals `item.english`, language rows)

**Explicit non-goals**

- Do not edit routes, templates, JS, or existing tests.
- Do not make new columns NOT NULL.
- Do not drop `korean`/`english`/`uq_item_content`.
- Do not change seed behavior.

**Risk and mitigation**

- SQLite migration failure: use `op.create_table` and plain `op.add_column`; no batch rebuild in Phase 1. Indexes can be created after backfill.
- Duplicate item text: the backfill copies; uniqueness is not enforced until Phase 3. Pre-flight query and report duplicates.
- CI: update expected table list; add old-schema→head test. `db.create_all()` still works because models are imported.

**Effort:** S/M. This is the first thing to ship.

### 6.3 Phase 2 — Language packs and content extraction

**Files**

- New `app/languages/{__init__,base,loader,errors}.py`, `app/languages/shared/schemas/*.json`.
- New `app/languages/ko/{__init__,pack,romanization,validation,manifest}.py/json`.
- Move data:
  - `hangul_data.py` → `ko/script/lessons/*.json` + `ko/script/hangul.json`.
  - `scene_data.py` → `ko/curriculum/scenes/*.json`.
  - `seed_data.py` → `ko/curriculum/seed_items.json`.
  - `sound_gym_data.py` → `ko/sound_gym/*.json`.
- Keep shims:
  ```python
  # app/learning/hangul_data.py
  from app.languages import get_pack
  HANGUL_LESSONS = get_pack("ko").curriculum().script_lessons()
  ```
  Same for `scene_data`, `sound_gym_data`, `seed_data` for one release.
- `app/__init__.py`: instantiate `LanguageRegistry` at `create_app`.
- Tests: `tests/languages/test_pack_contract.py`, golden files under `tests/golden/ko/`.

**Risk:** JSON schema drift. Mitigate with a `manifest.schema.json` + pack contract tests + golden content hashes. Shims keep the route tests green.

**Effort:** M. No user-visible change.

### 6.4 Phase 3 — Dual-write + language-scoped reads

**Files**

- `app/models.py`: add convenience properties (`Item.primary_form`, `Item.primary_gloss`, `Item.text`, `Item.gloss`) and SQLAlchemy event hooks or repository methods for dual-write.
- New `app/repositories/items.py` (or `app/learning/content.py`) for create/update.
- `app/learning/seed_data.py` / `seed.py`: `seed_content(language_id="ko")`; only seed when that deck is empty, not when all items are empty (`app/learning/routes.py:72-75`).
- `app/learning/service.py`: language/deck filters in `available_cards`, `stats`, `ensure_review_cards`, `skill_breakdown`, `recent_reviews`.
- `app/learning/scenes.py`: `SceneSession(user_id, language_id, scene_slug)`; read pack scenes; generic transcript fields.
- `app/routes.py` + `app/learning/routes.py`: resolve current language (session → user → default ko) and pass to services; URLs unchanged.
- Migration `0013_language_not_null.py`: add NOT NULL + new unique indexes after audit.
- Tests: add direct two-language unit tests (create `am` items, assert ko queries do not see them); keep existing 195 green.

**Risk:** dual-write divergence. Add a reconciliation CLI (`flask content-audit`) comparing legacy columns vs forms/glosses; log mismatches.

**Effort:** L.

### 6.5 Phase 4 — Provider abstraction + content validation

**Files**

- New `app/services/providers/{base,openai,azure,router}.py`.
- New `app/services/registry.py` (`Services`, `get_services`, `build_services`).
- New `app/services/content.py` (`ContentValidator`, candidate/persistence helpers).
- New `app/services/drills.py` (generator interface + OpenAI implementation).
- Rewrite `app/services/translation.py` into an adapter/facade; `translate_to_korean()` remains as a ko wrapper.
- Rewrite `app/services/speech.py` into `ASRProvider` + `PronunciationScorer` adapters; pack normalization; language from request.
- `app/services/audio.py`: `TTSProvider`/`generate_audio` accepts profile/voice; keep default signature.
- `app/utils/schemas.py`: generic request/response schemas; replace `contains_hangul` with pack validation; keep `korean_translation` aliases for one release.
- `app/__init__.py`: build services extension.
- Tests: provider contract suites with fakes; existing AI tests adapt to generic payload.

**Risk:** behavior changes in translation/speech. Keep exact response keys for ko and run both old/new assertions during transition.

**Effort:** M/L.

### 6.6 Phase 5 — Language-scoped URLs and UI/JS

**Files**

- Route registration: `/<lang_code>/learn/...`, `/<lang_code>/resources`, `/<lang_code>/welcome`, `/<lang_code>/library`; legacy `/learn/...` redirects to `/ko/learn/...` or resolves session default.
- `app/learning/routes.py`: `lang` from URL, pass `pack` into templates; generic `prompt_side`/labels; replace `/hangul` with `/script` but keep `/learn/hangul` alias.
- Templates: rename `hangul_*` → `script_*`; replace hard-coded copy with pack/UI strings; all `lang` attributes from `item_form.script` or explicit context; add `dir` attribute where needed.
- JS: shared `speak.js` helper reading `data-tts-lang`; remove five `ko-KR` literals; `data-target`/`data-script` in Sound Gym; generic translation fields.
- PWA: dynamic manifest endpoint (`/manifest.webmanifest?lang=ko`) or generic manifest; service worker push body generic.
- Onboarding/settings: language picker, pack goals/experience, `target_language_id`.
- Tests: parameterized route smoke per pack; `url_for` everywhere; language leakage guards.

**Risk:** URL/endpoint churn; keep old URLs as redirects for one release. Template copy regressions; add snapshot tests for ko pages.

**Effort:** L.

### 6.7 Phase 6 — Contract schema + soft delete/versioning

**Files**

- Migration `0014_contract.py` (batch alter/drop/rename; partial unique indexes).
- `app/models.py`: remove `korean`/`english`/`romanization`, rename `Phrase` fields, update `to_dict` and API compatibility.
- `app/routes.py`: map legacy API keys (`english_text`/`korean_text`) to `source_text`/`target_text` for one release.
- `app/services/*`: delete dual-write branches; use forms/glosses only.
- Tests: migration up/down, legacy API compatibility, content hash/golden.

**Risk:** SQLite table rebuilds and data loss on downgrade. Take a backup; run on a copy; ship after one release of dual-write. Downgrade is schema-reversible but not data-reversible.

**Effort:** M.

### 6.8 Phase 7 — Real-time teacher MVP (Korean first)

**Files**

- New models in `app/models_teacher.py` (imported by `models.py`): `TeacherSession`, `TeacherTurn`, `Drill`, `DrillAttempt`; migration `0015_teacher.py`.
- New `app/teacher/routes.py`, `app/teacher/tools.py`, `app/services/teacher/{engine,providers,vendor}.py`, `app/services/drills.py`.
- New templates `teacher_panel.html`, `teacher_summary.html`; `app/static/js/teacher.js`.
- `app/learning/service.py`: review queue filter by item IDs/deck for “practice this drill.”
- Config: `TEACHER_ENABLED=false`, provider, session limits, budget, retention.
- Tests: session lifecycle with fake engine, token minting (never leaks key), tool allowlist/scope, idempotent log_attempt, drill→ReviewCard, failure cleanup.

**Risk:** provider integration, latency, cost, privacy. Flag off by default; fake-provider tests; no raw audio; budget caps.

**Effort:** L/XL.

### 6.9 Phase 8 — Amharic pilot pack

**Files**

- New `app/languages/am/*` (see tree), golden files, tests.
- Config `LANGUAGES_ENABLED=ko,am`.
- No core code changes. If core changes are needed, the pack abstraction failed; fix the abstraction, not the language.

**Effort:** L. Then repeat for Spanish/Japanese.

### 6.10 What to do first, what to defer, what not to do

**Do first**

1. Phase 1 (additive schema + backfill) and Phase 2 (pack extraction). These remove the two hardest constraints without changing behavior.
2. Add the migration old→new test and CI gate **in the same PR** as Phase 1.

**Can be deferred**

- Contract migration (Phase 6) until one release of dual-write.
- Phoneme scoring (behind `PronunciationScorer`) until a vendor supports the target languages.
- Full UI localization; English UI + target-language content is viable.
- Dictionary multi-sense UI; schema can support it before UI uses it.
- Root `hangul.py` cleanup, cosmetic CSS class renames, DB filename.
- Teacher voice mode; start with text transcript + tool calls if provider latency/cost is uncertain.

**Do NOT do**

- Do not create a microservice per language or a separate realtime service now. The app is ~11.8k LOC and one process; a service boundary would add auth, deployment, and data consistency problems.
- Do not use a separate database or table per language. FSRS, analytics, and review UI would fragment.
- Do not adopt a generic EAV `item_attribute` table or a free-form JSON blob as the only content model. Use typed columns plus pack-validated JSON for morphology.
- Do not let an LLM invent item IDs, publish curriculum, or write directly to learner-visible content. All generated content is draft + validated.
- Do not rewrite the scheduler, media staging, or rate limiter. Reuse them.
- Do not drop `korean`/`english` columns before one release of dual-write and a content audit.
- Do not change `/learn` URLs and `/api/translate` response keys in the same release as the schema migration.
- Do not build a full CMS/native-review portal before there is a second language; versioned JSON + a review flag is enough for the pilot.
- Do not store raw audio or provider API keys in the browser.

---

## 7. Test strategy

### 7.1 Parameterize by pack, not by copy-pasting tests

Current suite: 144 test functions / 195 cases (`tests/*.py`; PROJECT_STATUS claims 195). Three test tiers:

1. **Pack/data tests** — run for every enabled pack. Parametrize with a `pack` fixture; use `pytest_generate_tests` to expand only tests marked `@pytest.mark.multilang`.
2. **Route/UI tests** — add an `app_for(lang)` fixture that creates the app, seeds that language’s deck, and sets `DEFAULT_LANGUAGE`/session language. Use `url_for` instead of hard-coded paths.
3. **Provider contract tests** — the same abstract test class runs against the real adapter with a fake transport and against a pure fake provider.

```python
# tests/conftest.py (target shape)
@pytest.fixture(params=["ko", "am"])
def pack(request):
    return get_pack(request.param)

@pytest.fixture()
def app_for(request):
    lang = getattr(request, "param", "ko")
    app = create_app("testing", overrides={...})
    app.config["DEFAULT_LANGUAGE"] = lang
    ...
```

Keep the default `pytest` run on `ko` only until the Amharic pack lands; CI then runs `ko` and `am` in a matrix or sequential parameterization. Add `pytest --lang=ko` for fast local runs.

### 7.2 Existing test hotspots and their target

| Test file | Current assumption | Target |
|---|---|---|
| `tests/conftest.py:56-64` | fake payload has `korean_translation`, `korean_text` | fake provider set keyed by `(source_lang, target_lang)`; generic `translation`, `target_text` |
| `tests/conftest.py:111-113` | transcription always `안녕하세요` | fake ASR returns a requested transcript; per-language fixture |
| `tests/test_speech.py:10-20, 57-67` | Korean exact/partial/wrong; non-Korean rejection | parametrized pack exact/partial/wrong; “wrong script for target language” per pack |
| `tests/test_ai_services.py:175-233, 267-285` | `korean_translation`, Hangul validator | generic schema + pack validator; keep ko alias tests |
| `tests/test_phase0_platform.py:341-351` | `test_translation_rejects_non_hangul_output` | `test_translation_rejects_wrong_script_for_target_language` with ko/am/es params |
| `tests/test_onboarding.py:25-26, 85, 113-128` | Korean copy, `/learn/hangul` | pack copy; `url_for("learn.script_index")`; old URL redirect test |
| `tests/test_resources.py:10, 14-21` | “Hangul bootcamp,” `q=커피` | pack sample term; `/ko/resources`, `/am/resources` if enabled |
| `tests/test_hangul_data.py:7-24, 112-129` | exact 7 lessons/88 drills | generic `test_script_pack` reads golden per pack; ko golden preserves those counts |
| `tests/test_scene_data.py:33-42` | `character_korean`, `korean`, `english` | scene schema v2; golden per pack |
| `tests/test_sound_gym_data.py:10-13, 59-67` | `korean`, `romanization`, `english` | `text`, `transliteration`, `gloss`; uniqueness per pack |
| `tests/test_learning_loop.py:12-20` | one global seed deck, all items get cards | per-deck seed; assert `deck`/`language` counts, not global |
| `tests/test_scene_speech.py:40-73` | `SCENES[0]`, Korean expected | `pack.scenes[0]`; fake transcript from scene data |
| `tests/test_routes_smoke.py` | paths `/learn`, `/resources` | `url_for` with default ko; legacy redirects |

**Strategy:** Phase 1/2 keep all legacy tests green via shims. Phase 3 adds new language-isolation tests. Phase 5 migrates route tests to `url_for`/pack fixtures. Do not do a big-bang test rewrite.

### 7.3 Provider contract tests with fakes

Create `tests/fakes/providers.py`:

```python
class FakeTranslationProvider:
    def __init__(self, responses): self.responses = responses; self.calls = []
    def translate(self, request):
        self.calls.append(request)
        return TranslationResult(text=self.responses[request.target_lang],
                                 provider="fake", model="fake-1")

class FakeASRProvider: ...
class FakeTTSProvider: ...
class FakePronunciationScorer: ...
class FakeContentValidator: ...
```

Contract suite (same assertions for every provider):

- request carries `source_lang`/`target_lang`; no implicit ko.
- output is validated by the target pack; wrong-script output is rejected.
- empty/oversized input raises `ValueError`/domain error, not 500.
- provider timeout/rate-limit maps to `ProviderError` → route 502/503.
- cache key includes language + pack version; two languages do not share a cache entry.
- no DB rows/files left on failure (extend `tests/test_phase0_platform.py:356-368`).
- ASR sends the pack’s `language_code`, not `"ko"`.
- TTS uses the pack voice map; fallback voice is explicit.

Keep `FakeOpenAIClient` (`tests/conftest.py:122-130`) as the transport fake for the OpenAI adapter; add higher-level fakes for the registry.

### 7.4 Golden-file tests for script/content data

- `tests/golden/ko/script_lessons.json`, `scenes.json`, `sound_gym.json`, `seed_items.json`.
- `tests/golden/am/...` when the pack lands.
- Each golden file stores a deterministic serialization plus `content_hash`.
- `pack.content_hash()` is stable across JSON key order (sort keys).
- Update only with `pytest --update-golden` (manual, reviewed diff); CI runs read-only.
- Golden tests assert:
  - lesson slugs/order/counts;
  - every drill has 4 unique options and answer in options (`tests/test_hangul_data.py:117-128`);
  - every scene has required fields and unique debrief card texts;
  - every seed item validates with `pack.validate_item`;
  - every `text`/`transliteration` round-trips through the pack normalizer.

### 7.5 Migration and CI gates

Add `tests/test_migrations_multilingual.py`:

1. **Empty DB:** `alembic upgrade head`; assert all expected tables/columns including new ones.
2. **Old → new:** `upgrade 20261019_0010`; insert a ko user/item/phrase/speech_attempt/scene_session/can_do; `upgrade head`; assert:
   - `language('ko')` exists;
   - every old row has `language_id`;
   - `item_form.text == item.korean`, `transliteration == item.romanization`;
   - `item_gloss.text == item.english`;
   - row counts preserved;
   - idempotent rerun does not duplicate forms.
3. **Contract:** upgrade head → downgrade to 0010 on a copy; assert schema restored (data loss documented).
4. **Parity:** `db.create_all()` metadata vs migrated schema: same table/column set (or an explicit allowlist for SQLite quirks). This catches the `phrase` baseline class of bug.

CI (`.github/workflows/ci.yml:30-74`):

- Keep the empty-DB migration gate.
- Add the multilingual test path (old schema + data → head).
- Update expected tables: `language`, `script`, `language_script`, `level_scale`, `course`, `deck`, `deck_item`, `item_form`, `item_gloss`, `dictionary_entry`, `dictionary_sense`, `translation`, `term_card`, `teacher_session`, `teacher_turn`, `drill`, `drill_attempt`.
- Prefer deriving the expected set from `db.metadata.tables` with an explicit exception list, so CI cannot pass with a model that has no migration.
- Run `ruff check` unchanged.

### 7.6 Isolation, leakage, and cache tests

- **Language leakage:** render `/am/learn` and assert no Hangul codepoints in the HTML, `lang` attributes match Ethiopic/Latin context, and no `ko-KR` TTS remains. Reverse for `/ko`.
- **Cross-language uniqueness:** insert the same text in `ko` and `am`; both succeed; duplicate within one language fails.
- **Review isolation:** an `am` learner’s `available_cards` never returns ko items; `stats.total_items` is language-scoped.
- **Cache isolation:** clear `app.utils.caching._cache`, `load_pack.cache_clear()`, and fake provider call logs between tests. Assert ko and am translation requests hit different cache keys.
- **Provider key safety:** teacher token response never contains `OPENAI_API_KEY`; browser JS never receives it.
- **Soft delete:** archived items are excluded from dictionary/search/new cards but existing `ReviewLog` rows remain.

---

## 8. Open questions / decisions needed (ranked)

1. **Which languages, in what order, and what counts as “Ethiopian languages”?**
   Amharic, Tigrinya, Oromo, Somali, and Ge’ez share scripts or regions but differ in grammar, lexicon, and ASR support. Decide whether “Amharic first” is one pack or a family roadmap. **Default recommendation:** Amharic (`am`) first; do not claim one pack covers Ethiopian languages. This determines the script/level/morphology design more than any other choice.

2. **Teacher provider and modality.**
   OpenAI Realtime vs Gemini Live vs a composed STT→LLM→TTS pipeline; voice-only vs text+voice; maximum session length; per-session cost ceiling. **Default:** build the provider-agnostic `TeacherEngine`/tool router, ship a single adapter (OpenAI Realtime) behind `TEACHER_ENABLED=false`, persist text transcripts, no raw audio.

3. **Pronunciation scoring depth.**
   Keep transcript matching, add forced alignment, or buy phoneme scoring (Azure/SpeechSuper/ELSA). Which vendors support Amharic, Tigrinya, and Japanese? **Default:** ship `PronunciationScorer` v1 = transcript gate; add phoneme evidence only where the vendor supports the language; never present a transcript match as a pronunciation grade.

4. **Content authority and native review.**
   Who signs off on generated translations, scenes, and drills? Are LLM drafts allowed in the public deck? What provenance fields are required? **Default:** LLM drafts only; `status=draft`, `validated=true` after pack validation, `is_human_reviewed=true` required for `published`; at least one native reviewer per launch language.

5. **Level scale policy.**
   Native scale per language (TOPIK, CEFR, JLPT, custom Amharic) or a unified CEFR mapping? How do existing `item.level=1..6` rows map? **Default:** per-language native scale + optional CEFR mapping; ko existing levels map to TOPIK bands; UI shows both.

6. **UI locale.**
   Is English the only UI language at launch? Will Amharic/Spanish/Japanese UI be translated? Any RTL language in scope? **Default:** English UI at launch; target-language content; per-language fonts; add UI locale later without schema changes (`User.ui_locale` already planned).

7. **Account model and teacher access.**
   The app is local single-user (`app/models.py:62-90`, `app/learning/service.py:34-50`). Teacher sessions and personal libraries need a real user. When do accounts land? **Default:** add `User.target_language_id` in Phase 1; require accounts before a public teacher; keep local mode for development.

8. **API compatibility.**
   Are `/api/phrases`, `/api/translate`, `/library` public contracts? Can `english_text`/`korean_text` keys change? **Default:** keep legacy keys as aliases for one release, add `source_text`/`target_text`/`target_lang`, then version `/api/v2`; do not break the PWA mid-refactor.

9. **Audio storage and voice policy.**
   Flat `/static/audio` vs `/<lang>/<voice>/`; TTS vs native audio; voice licensing; CDN. **Default:** `AUDIO_DIR/<lang>/<voice>/<stem>.mp3`; keep media audit recursive; native audio for core decks, TTS for generated/teacher content.

10. **Cost and abuse controls.**
    Per-user daily TTS/translation/teacher budgets; per-language rate limits; cache retention. **Default:** per-user daily quotas and per-session teacher caps; cache by `(text, target_lang, voice, pack_version)`; rate limit with the existing limiter.

11. **Data retention and privacy.**
    Teacher transcripts, drill responses, and speech attempts are learner data. GDPR/COPPA obligations? **Default:** no raw audio; configurable transcript retention; delete/export endpoints before public teacher launch.

12. **Migration window and rollback policy.**
    Is one release of dual-write acceptable? Can the app tolerate a maintenance window for the SQLite contract rebuild? **Default:** dual-write for one release, backup before contract, accept schema-reversible/data-lossy downgrade; document it.

---

## Appendix A — “Release gates” checklist

**Gate 1 (after Phase 1):**

- [ ] `flask db upgrade` on empty DB builds all old + new tables.
- [ ] Old schema with data upgrades and backfills `ko`.
- [ ] All 195 legacy tests pass unchanged.
- [ ] CI expected-table gate updated.
- [ ] No route/template/JS diff in the Phase 1 PR.

**Gate 2 (after Phase 3):**

- [ ] `flask content-audit` reports zero legacy/form mismatches.
- [ ] A second language can be inserted in a test without violating a unique constraint.
- [ ] `stats()`/`available_cards()` are language-scoped.
- [ ] Existing ko pages byte-for-byte equivalent except intentional copy changes.

**Gate 3 (after Phase 4):**

- [ ] Provider contract tests pass for all fakes.
- [ ] No provider key reaches the browser.
- [ ] Wrong-script output is rejected per language.
- [ ] Translation/speech routes return the same ko response shape as today.

**Gate 4 (after Phase 6):**

- [ ] Contract migration up/down tests pass on SQLite and Postgres.
- [ ] Legacy API aliases tested.
- [ ] Backup/restore runbook reviewed.

**Gate 5 (after Phase 7):**

- [ ] Teacher session lifecycle test with fake provider.
- [ ] Tool allowlist rejects out-of-language/out-of-scope item IDs.
- [ ] `log_attempt` is idempotent and creates at most one `ReviewCard`.
- [ ] No raw audio stored; transcript retention job tested.

**Gate 6 (after Phase 8):**

- [ ] Amharic pack passes the same contract/golden tests as ko.
- [ ] Amharic pages contain no Hangul and no `ko-KR`.
- [ ] A learner can complete onboarding, review, one scene, and one teacher drill in Amharic with only pack data.

---

## Appendix B — Why not the obvious alternatives

**Why not per-language tables (`korean_item`, `amharic_item`)?**
Every query, FSRS card, review UI, analytics metric, and migration would need a language branch. The existing `ReviewCard` unique `(user,item,skill)` (`app/models.py:135-141`) already gives per-item scheduling; adding `language_id` preserves it. Table-per-language is a scaling decision for a database with hundreds of millions of rows, not an 11k-LOC app.

**Why not a separate microservice for realtime teacher?**
The teacher needs the same DB, auth, content validator, review scheduler, and dictionary. Splitting it adds network auth, duplicate models, and consistency bugs before there is load. Start with an in-process `TeacherEngine` behind a provider adapter; extract only if session concurrency or provider WebSocket handling demands it.

**Why not a generic `item_attribute(key,value)` EAV?**
You lose typed uniqueness (`language_id, item_type, key_normalized`), joins for review/search, and pack validation. Typed columns + a narrow `morphology` JSON field is the right balance.

**Why not store all content in JSON and skip DB content tables?**
You need per-item FSRS FKs, dictionary search, user term cards, and analytics. Pack JSON is the authored source; DB rows are the runtime identity. Seed/import copies JSON into DB; it does not query JSON at request time.

**Why not let the LLM create new curriculum items directly?**
It cannot be trusted for orthography, register, morphology, or level, and it breaks the “content constrained to DB IDs” invariant. Draft + validator + human review is slower but is the only way to keep a language-learning product credible.

---

## Appendix C — Key file:line evidence index

| Claim | Evidence |
|---|---|
| Item is Korean/English columns | `app/models.py:92-129` |
| Item unique constraint | `app/models.py:95-98` |
| Phrase columns | `app/models.py:8-31` |
| SpeechAttempt shape | `app/models.py:268-307` |
| SceneSession/CanDo slugs | `app/models.py:204-265` |
| ReviewCard uniqueness | `app/models.py:132-172` |
| User has no language | `app/models.py:62-90` |
| Hangul curriculum | `app/learning/hangul_data.py:14-1485` |
| Scene data/keys | `app/learning/scene_data.py:20-466` |
| Sound Gym data | `app/learning/sound_gym_data.py:12-213` |
| Seed data | `app/learning/seed_data.py:12-67` |
| Scene normalization | `app/learning/scenes.py:16-17` |
| Global stats/cards | `app/learning/service.py:63-102, 117-160, 215-238` |
| Hangul-only schema | `app/utils/schemas.py:25-27, 52-105` |
| Korean translation prompt | `app/services/translation.py:64-86, 130-146` |
| ASR language ko | `app/services/speech.py:26-28, 80-86` |
| TTS default voice | `app/services/audio.py:21-31` |
| Lazy client/extension | `app/services/ai.py:57-95` |
| Global TTS/STT config | `config.py:43-47, 66-73` |
| Template `has_hangul` | `app/__init__.py:342-349` |
| Korean routes | `app/learning/routes.py:483-505` |
| Prompt sides | `app/learning/routes.py:559-572` |
| Speech validation | `app/learning/routes.py:404-410` |
| Resource search | `app/routes.py:99-136` |
| Translation route | `app/routes.py:263-319` |
| Conversation route | `app/routes.py:341-450` |
| Onboarding goals | `app/onboarding/routes.py:24-84` |
| Korean template copy | `app/templates/base.html:2-6, 52-58`; `learn_review.html:19-65`; `resources.html:8-48`; `scene_play.html:23-66` |
| `ko-KR` in JS | `app/static/js/{onboarding,review,scene,hangul,sound_gym}.js:23/78/13/39/19` |
| PWA name | `app/static/manifest.webmanifest:2-4` |
| Legacy migrations | `migrations/versions/20261019_0002_learning_core.py:31-53`; `0007:23`; `0008:22-32`; `0009:22-29` |
| CI migration gate | `.github/workflows/ci.yml:30-74` |
| Test fake/DB bootstrap | `tests/conftest.py:56-64, 122-130, 173-174` |
| Korean test assertions | `tests/test_onboarding.py:25-26, 113-128`; `tests/test_speech.py:10-67`; `tests/test_ai_services.py:175-233`; `tests/test_hangul_data.py:7-24` |
