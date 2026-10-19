# Kiku — Product & Learning Blueprint

**The Korean tutor that remembers you.**

Version 1.0 · 19 October 2026 · Working name: **Kiku** (聞く, "to listen")

This document is the synthesis of four research streams: a codebase audit, the learning-science evidence base, Korean-specific pedagogy, a 27-product competitive teardown, and a technical/AI capability review. Supporting detail and citations live in `docs/research/`.

---

## 0. Executive summary

The current repository is a **translation-and-audio prototype**, not yet a learning product. It can translate an English phrase, generate Korean TTS, store it in a library, and generate a short two-voice conversation. That is the entire loop. There is no account, no review queue, no Hangul onboarding, no pronunciation feedback, no grammar explanation, no leveling, no personalization, and no honest measure of learning. The README claims practice exercises and progress tracking; the code does not contain them.

The redesign is not "add flashcards to the existing app." It is a change of product category:

- **From translation tool → to retrieval-and-feedback engine.** The learner should produce Korean, not request it.
- **From content generator → to curriculum + memory.** Generated content is a supply input, never the product.
- **From anonymous global feed → to a persistent learner model.** Every attempt, error, interest, and scene feeds one model.
- **From XP and streaks → to proof of ability.** The scoreboard is unrehearsed can-do performance at 7 and 30 days.
- **From audio player → to voice-first coaching.** Listening and speaking are the core, with text as scaffolding.

**The Kiku loop** is a 10-minute daily session: retrieve → notice → speak in a mission → debrief → keep three cards → see one win. It is wrapped in a humane habit system (2-minute minimum, flexible streak, user-owned notifications) and powered by FSRS-6 scheduling, an Elo/BKT learner model, and a validated Korean content graph.

**The wedge:** Korean apps are crowded at the gamified-vocabulary extreme and the unstructured-AI-chat extreme. Almost nobody owns the middle: a guided, voice-first Korean path with **trustworthy Korean, a memory of the learner, and pronunciation coaching that is honest about what it can and cannot hear.**

**The first 90 days** should ship: a safe, tested platform; Hangul + pronunciation bootcamp; a 10-minute daily loop; 30 validated scenes; FSRS review; a persistent learner model; and a can-do progress artifact. Not a social network, not a mascot, not 6,000 words of scraped content.

---

## 1. Where the project actually is

### 1.1 Inventory

| Area | What exists | Maturity |
|---|---|---|
| Translation | EN→KO via `gpt-4.1-nano`, one string, no alternatives or gloss | Prototype |
| Audio | OpenAI `tts-1`, one voice / two voices for dialogue, local MP3 | Prototype |
| Library | Paginated list of saved phrases, replay only | Prototype |
| Conversations | 2–4 line LLM dialogue, per-line + merged audio | Prototype |
| Persistence | SQLite: `phrase`, `conversation`, `conversation_line` | Prototype |
| Users | None. All data is global and anonymous | Missing |
| Learning loop | None: no review, quiz, SRS, mastery, or goal | Missing |
| Hangul | None: Korean text is displayed, never taught | Missing |
| Pronunciation | Output only; no microphone, ASR, or feedback | Missing |
| Grammar | None: no parse, particles, register, or explanation | Missing |
| Assessment | None: no placement, level, or can-do statements | Missing |
| Mobile / offline | Responsive CSS only; no PWA, manifest, or service worker | Missing |
| Tests / CI | Zero tests, no CI, no linter/type checks | Missing |
| Deployment | Local Flask dev server; no container, health check, or migration gate | Missing |

Live data at audit time: 13 phrases, 3 conversations, 7 lines, 31 static MP3s of which 15 are orphaned (54% of audio bytes). Six duplicate audio variants exist for one conversation line. These are symptoms of the missing transaction/job design, not cosmetic issues.

### 1.2 The ten findings that matter most

1. **No learning loop.** A learner can generate content but cannot study it. This is the product-level gap; everything else is secondary.
2. **No learner model.** No `user_id` anywhere. Personalization, retention, and honest progress are impossible without it.
3. **OpenAI clients are created at import.** The app, migrations, and tests fail without a live key.
4. **Timeouts and retries multiply.** SDK defaults (600 s, 2 retries) × three manual attempts can hold a worker for a very long time and duplicate spend.
5. **Media is written outside the DB transaction.** Failures leave orphan files; retries create duplicates.
6. **SQLite holds a write lock across network calls.** `busy_timeout=0`, no WAL, no foreign keys. Concurrent use will produce `database is locked`.
7. **DOM XSS.** `new_conversation.js` injects LLM-controlled strings with `innerHTML`.
8. **The migration baseline is broken.** The only migration omits the `phrase` table; `db.create_all()` masks it. A fresh `flask db upgrade` cannot build the app.
9. **Rate limiting is an unbounded, thread-unsafe, per-process dict** shared across endpoints and blind to proxies.
10. **No tests.** The failure-prone paths — generation, files, scheduling, auth, scoring — have no regression safety.

The audit also found genuine positives: ORM-only data access, sanitized filenames with UUIDs, Jinja autoescaping, a reasonable app-factory/blueprint scaffold, and a working happy path. The foundation can be evolved; it does not need a rewrite.

### 1.3 What this means

Do **not** start by adding features to the current surface. First make the platform safe and truthful (Phase 0), then build the learning core (Phase 1), then add speech and scenes (Phase 2). The detailed audit, with file:line evidence and a prioritized debt table, is in `docs/research/01-codebase-audit.md`.

---

## 2. The evidence base in twelve laws

These are the design constraints that follow from the research. Each is a product rule, not a slogan.

1. **Retrieval beats review.** Practice testing outperforms restudying (g ≈ 0.61). Production and cloze are default interactions; recognition is a scaffold.
2. **Spacing beats massing.** Spaced retrieval beats massed (g ≈ 0.74). Use FSRS-6, not fixed boxes. Default retention 0.90; 0.85 for casual, 0.95 for exam prep.
3. **Review before new.** 60–80% of session time on due review; 5–10 new items/day. New items are a budget, not a binge.
4. **Target ~85% success.** Below 75%, add scaffolds; above 92%, raise difficulty. Failure should signal room to grow, not shame.
5. **Interleave contrasts, block vocabulary.** Mix grammar/sound categories; keep new word sets together. Interleaving helps concepts and hurts raw word lists.
6. **Teach chunks, not isolated words.** Store collocations, speech-level endings, and honorific chunks as single items with audio.
7. **Worked example → completion → generation → transfer.** Never open grammar with cold production. Fade the supports.
8. **Dual-code with discipline.** Relevant image + L1 gloss + audio. No decorative art on cards; it competes for attention.
9. **Train perception with many voices.** High-variability phonetic training (5–8 talkers), minimal pairs, immediate feedback, then production. ASR feedback helps (g ≈ 0.69), but ASR is not a pronunciation grade.
10. **Input is necessary, not sufficient.** Aim for 95–98% known-word coverage in reading/listening, then add noticing, pushed output, and feedback.
11. **Motivation is need-supportive, not punitive.** Autonomy (choice), competence (mastery bars), relatedness (bounded pods). Gamification effects are small and unstable; loss-framed streaks are a dark pattern.
12. **Measure delayed, unrehearsed performance.** Primary metric: can the learner do it 7 and 30 days later without cues? XP is a guardrail, not an outcome.

**Myths Kiku must never ship:** learning styles, left/right-brain learners, "10% of your brain," Brain Gym, sleep-learning audio, "adults can't learn like children," "native accent is the goal," "streak = learning," and "more hours is always better." The evidence and citations are in `docs/research/02-learning-science.md`.

---

## 3. Who Kiku is for

### 3.1 Personas

| Persona | Situation | Job to be done | What fails them today |
|---|---|---|---|
| **Mina, 24 — K-culture beginner** | Watches dramas, knows a few phrases, free 10 min/day | "I want to understand without subtitles and say something back." | Apps teach words, not listening; AI chat is unstructured; pronunciation feedback is absent. |
| **Daniel, 34 — Traveler/relocator** | Moving to Seoul in 6 months, needs survival Korean | "I need to order, ask directions, handle a doctor's appointment." | Courses are topic-of-the-week, not mission-shaped; no rehearsal under pressure. |
| **Sarah, 29 — Intermediate plateau** | A2/B1, understands more than she can say, particles fossilized | "I want to speak without freezing and fix my recurring errors." | Gamified content is too easy; tutors are expensive; no diagnosis or targeted practice. |
| **Joon, 19 — Heritage learner** | Understands family Korean, cannot read/write formally | "I want to sound like an adult, not a child, and pass TOPIK." | Placement assumes zero or native; no receptive→productive bridge; no formal register. |
| **Alex, 41 — Workplace/professional** | Needs honorifics, meetings, email, industry vocabulary | "I need to be competent and appropriate at work." | Consumer apps stop at travel; human tutors are the only option; no discreet 10-minute format. |

### 3.2 Jobs and emotional states

Learners do not want "content." They want three feelings:

- **"I can handle that situation."** → mission-based scenes with success criteria.
- **"I am getting better, and I can prove it."** → can-do artifacts, before/after audio, skill map.
- **"This respects my time and intelligence."** → short sessions, no shame, no fake scores, no childish theater.

The churn moment is rarely "I lost motivation." It is a **failed value proof**: the learner cannot see, hear, or feel that they are becoming someone who speaks Korean. Kiku must manufacture that proof in the first two minutes and then make it visible every week.

### 3.3 Non-goals for v1

- An open social network or language-exchange marketplace (safety, moderation, cold start).
- A mascot-driven game for children.
- A general-purpose AI chatbot with no curriculum.
- A dictionary or translator (useful utilities, not the product).
- Every TOPIK level at launch. Depth at A1–B1 first; breadth later.
- A native mobile app before the PWA proves retention.

---

## 4. Product thesis and positioning

### 4.1 Positioning

> **For learners who freeze when a Korean person speaks to them, Kiku is the voice-first Korean tutor that takes you from Hangul to real conversation — with native-validated Korean, phoneme-level pronunciation coaching, and a memory of every mistake you have made.**
>
> Unlike Duolingo, it does not just keep you busy. Unlike AI chat apps, it remembers you and never invents the language.

### 4.2 The five must-wins

1. **Hangul and pronunciation fluency in week one.** By day 7, read a real sign and introduce yourself. By day 30, be intelligible in 8–10 transactional phrases.
2. **Persistent learner memory.** One model across lessons, scenes, review, and content. Every correction becomes a card; recurring errors trigger targeted scenes.
3. **Grounded, trustworthy Korean.** A curated canonical layer, LLM generation constrained to slots, morphological/register validation, and native review. Never ship unvalidated generated Korean.
4. **Goal-shaped paths with proof.** Everyday, travel, TOPIK, workplace, K-drama, heritage. Can-do statements, skill map, mock assessments.
5. **Ethical retention and fair pricing.** Flexible streak, user-owned notifications, a free tier that actually teaches, monthly plans, no shame copy.

### 4.3 Brand and tone

Kiku means "to listen." The brand should feel **calm, curious, and precise** — a knowledgeable friend, not a clown or a drill sergeant. Korean visual cues (Hangul typography, paper textures, muted celadon/ink palette) without tourist-shop clichés. Copy is direct and adult: "You can now order coffee." "Try the final consonant." "That was clear." No "Oops!" no "You lost a heart!" no fake urgency.

### 4.4 Product principles

1. **Speak first, explain second, decorate never.**
2. **One primary action per screen.**
3. **Every session ends with a win the learner can hear.**
4. **The learner should never wonder what to do next.**
5. **When in doubt, reduce scope and raise quality.**
6. **Never punish a learner for the app's uncertainty** (ASR false negative, content ambiguity).
7. **Show the work:** why this item, why now, why this correction.
8. **Accessibility is a learning feature**, not a compliance checkbox.

---

## 5. The Kiku learning engine

### 5.1 The competency graph

Kiku tracks six strands, each with receptive and productive state. A single "level" is a lie; the graph tells the learner where they actually are.

| Strand | What it measures | Example evidence |
|---|---|---|
| **Decoding** | Hangul reading accuracy and speed | Read 100 syllables/min; decode batchim and liaison |
| **Perception** | Discriminating Korean sounds and connected speech | Minimal-pair accuracy across 5–8 voices |
| **Pronunciation** | Intelligibility and prosody in production | Word-level ASR gate + phoneme evidence + rhythm |
| **Vocabulary** | Recognition and recall of words/chunks | Meaning recall, form recall, production in context |
| **Grammar** | Comprehension and production of patterns | Cloze, transformation, constrained output |
| **Interaction** | Pragmatics, fluency, repair strategies | Mission success, turn latency, register choice |

Each strand has a mastery estimate with uncertainty, not a percentage. The UI shows "solid / shaky / new" and a next action, never a false-precision score.

### 5.2 Item and card taxonomy

Every item is a first-class content object. Every **skill × item** pair gets its own FSRS state. One lexeme can have separate recognition, listening, and production cards.

| Item type | Example | Card skills | Notes |
|---|---|---|---|
| **Lexeme** | 커피 (coffee) | recognize, recall, listen, produce | Image + audio + gloss + example |
| **Chunk** | 커피 한 잔 주세요 (one coffee, please) | recall, produce | Stored as one unit; not word-by-word |
| **Grammar pattern** | -아/어서 (cause/sequence) | understand, produce | Worked example → completion → generation |
| **Minimal pair** | 불 / 뿔 / 풀 | perceive, produce | Audio discrimination, 5–8 voices |
| **Shadowing line** | 천천히 말해 주세요 | produce, prosody | Record, compare, band feedback |
| **Scene line** | "여기 앉으세요." | listen, respond | Part of a mission, not isolated |
| **Cloze sentence** | 커피 한 잔 ___ 주세요. | recall | Tests particle/ending choice |
| **Translation** | "Where is the bathroom?" → 화장실이 어디예요? | produce | EN→KO; reverse for comprehension |
| **Typing** | 안녕하세요 | decode, type | Hangul IME practice |
| **Reading** | Graded story at 96% coverage | read, infer | Tap-to-define, clip-to-card |

**Card design rules:** one target per card; audio always; relevant image only; no decorative art; no more than one new concept; answer options must be plausible and similar in length; production cards never show the answer before the attempt.

### 5.3 The adaptive stack

Use the simplest model that supports the decision. Do not build deep knowledge tracing before there is data.

| Decision | Model | Why |
|---|---|---|
| **When** to review | FSRS-6 (`py-fsrs` 6.x) | Best-supported scheduler; 21 parameters, power forgetting curve; 90% retention default |
| **How hard** is an item | Elo with decaying K, initialized from frequency/length/grammar complexity | Cheap, online, cold-start friendly |
| **What** is mastered | BKT per skill/pattern with exponential forgetting | Interpretable, 4 parameters, works at small scale |
| **Which** item next | Contextual bandit / Thompson sampling over FSRS-due + prerequisites + target skill | Balances review, new material, and engagement |
| **Placement** | 10–15 item adaptive Elo test + self-report + content priors | Fast, tolerant of uncertainty |
| **Leeches** | 4+ lapses or ≥8 reviews at <50% | Intervene (simplify, split, add mnemonic, suspend), don't drill harder |

**FSRS configuration:** desired retention 0.90 (0.85 casual, 0.95 exam); learning steps 1 min / 10 min; max interval 36,500 days; fuzzing on; optimize per user only after 400–1,000 reviews, otherwise population defaults; re-optimize monthly or when reviews double.

**Why not deep KT:** published comparisons put logistic regression around 0.77 AUC vs DKT/SAKT around 0.76 on 50k students. Deep models need 100k+ interactions and hurt interpretability. Revisit at scale.

### 5.4 The session planner

The planner is the product. It turns a learner's state into a 2-, 10-, or 25-minute session.

```
plan(user, minutes, context):
  due      = fsrs.due(user, now)
  weak     = bkt.weak_skills(user, threshold=0.6)
  goal     = path.target(user)            # can-do, not "lesson 14"
  interests= user.topics                  # drama, food, travel, work
  budget   = time_budget(minutes)

  blocks = []
  blocks += warmup(retrieve(due[:3]))                  # 60–90 s
  blocks += interleaved_review(due[3:], 55–70% budget)
  if user.speech_goal_due or weak includes perception:
      blocks += sound_gym(minimal_pairs, voices=5–8)   # 2–4 min
  blocks += scene(goal, target_chunks, interests, 3–5 min)
  blocks += debrief(scene, max_corrections=3)          # 60–90 s
  blocks += artifact(record_one_can_do)                # 20–30 s

  adapt(blocks):
    if rolling_success < 0.75: insert scaffolds (word bank, slower audio, L1 hint)
    if rolling_success > 0.92: fade scaffolds, raise difficulty
    if due_load > budget: defer low-priority cards, show forecast
    if new_items > 10: stop new, keep review
  return blocks
```

**Hard constraints:** reviews before new; 5–10 new items/day; no more than 2–3 corrections per scene; no session longer than the learner chose; always end on a success the learner can hear or read.

### 5.5 Feedback and correction policy

Correction is where most apps destroy confidence. Kiku separates **flow** from **debrief**.

| Moment | What happens | Why |
|---|---|---|
| **During a scene** | One implicit recast if meaning is unclear; otherwise let it flow | Interrupting every sentence kills fluency and increases anxiety |
| **During review** | Immediate, explicit feedback with the smallest sufficient explanation | Retrieval needs a clear answer; ambiguity wastes the rep |
| **Pronunciation** | Name the feature, show a diagram/contour, ask for one retry | "Aspirated ㅋ: more air," not "78/100" |
| **Debrief** | 2 strengths, 1 priority fix, 3 cards | Bounded, memorable, actionable |
| **Recurring error** | Add a targeted mini-scene and a contrast card | Fossilization needs focused, spaced intervention |
| **ASR uncertainty** | Say "I heard X — was that right?" and offer retry/type/skip | Never punish the learner for model error |

**Register and politeness:** default to 해요체 with unfamiliar adults; teach 합니다체 for public/professional first contact; introduce 반말 only with relational licence. Correct honorific misuse explicitly because it is socially costly.

### 5.6 Scaffolding ladder

Fade support as competence rises:

1. Full model + audio + translation.
2. Audio + Korean + word bank.
3. Audio + Korean + first-syllable hint.
4. Audio + Korean only.
5. English prompt → Korean production.
6. Situation prompt → free production.

If the learner fails twice at a level, drop one rung. If they succeed twice, climb one. The ladder is per skill, not per user.

### 5.7 Assessment that tells the truth

- **Placement:** 10–15 adaptive items across decoding, listening, vocabulary, grammar, and production; 3–5 minutes; outputs a band with uncertainty and a recommended starting point.
- **Weekly check:** 5 unseen items from the current path, plus one 30-second speaking prompt. Not a grade; a calibration.
- **Monthly assessment:** 10 minutes, unseen items, 7-day delayed retest for a subset. This is the only source of the "retained" number.
- **Can-do artifacts:** a recorded sentence or short dialogue tagged to a real-world task ("order coffee," "ask for directions," "apologize for being late"). Stored with date and audio; the before/after comparison is the emotional payoff.
- **TOPIK/CEFR:** report separate receptive and productive estimates mapped to TOPIK/CEFR with explicit uncertainty. Never claim a precise level from a 10-item quiz.

---

## 6. Curriculum

### 6.1 The honest timeline

Korean is FSI Category IV: roughly 2,200 classroom hours to ILR 3 for a native English speaker. Guided apps can compress input and feedback, but not retention. Kiku should promise:

| Milestone | Guided hours | Calendar at 15 min/day | What the learner can do |
|---|---|---|---|
| **Read Hangul** | 8–12 | 7–10 days | Read signs, names, menus; type their name |
| **A1** | 60–80 | 3–4 months | Introduce, order, shop, ask directions, simple past |
| **A2** | 150–200 | 8–12 months | Phone, transport, appointments, routines, short stories |
| **B1** | 350–450 | 18–24 months | Narrate, explain, opine, handle most daily situations |
| **TOPIK 4–6** | 800–1,500+ | 3–5 years | News, work, abstract discussion, academic writing |

These are defensible ranges, not guarantees. Marketing should say "A1 in about 3 months at 15 minutes a day," not "fluent in 90 days."

### 6.2 Onboarding and placement (first 5 minutes)

1. **Goal** — one tap: travel, family/partner, K-culture, work, TOPIK, heritage.
2. **Time** — 3 / 10 / 25 minutes per day.
3. **Experience** — never / know Hangul / some conversation / intermediate.
4. **Adaptive check** — only if experience > never: 8–12 items, 2 minutes.
5. **First win** — teach 안녕하세요, have the learner record it, play it back with one specific compliment ("Your vowel length was clear"). No account wall before this.
6. **Implementation intention** — "When ___ , I will do my 10 minutes at ___." Two taps.
7. **Account** — email/Apple/Google; save the artifact and the plan.

No 12-screen survey. No mascot selection. No paywall before the first spoken sentence.

### 6.3 Hangul Bootcamp — 7 days, 15–20 min/day

The promise: **"Read anything by Sunday."** Recognition is not reading; the bootcamp teaches decoding fluency, batchim, liaison, and typing.

| Day | Content | Practice | Check |
|---|---|---|---|
| **1** | 14 basic consonants, 6 vowels (ㅏㅓㅗㅜㅡㅣ), CV blocks | Build 30 syllables; 안녕하세요, 감사합니다, 네/아니요 | Read 30 CV blocks aloud |
| **2** | Remaining vowels and glides; compound vowels | 40 blocks; 저는 ___이에요/예요 | Read 40 blocks; say your name |
| **3** | Batchim; the seven final sounds [ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ]; unreleased stops | 20 CVC words; 뭐예요? | Read 20 CVC words without epenthesis |
| **4** | Liaison (연음); 은/는 vs 이/가 | 한국어, 옷이, 꽃을; self-intro | Read 10 liaison words; 3-sentence intro |
| **5** | 있어요/없어요; 이/그/저; Sino-Korean numbers 1–10; counters intro | 10 nouns + 5 locations; "여기 있어요" | Point-and-name 10 objects |
| **6** | 해요체 present with 10 high-frequency verbs; 안 + verb | 10 verbs × 3 persons; café phrases | Produce 10 present-tense sentences |
| **7** | Review, typing drill, 40-word dialogue, recorded self-intro | Read a real sign/menu; type your name and address | 2-minute recording; 90% jamo accuracy |

**Teaching rules:** teach letters in CV blocks, not isolation; teach tense/aspirated as a contrast set with audio; teach batchim as *sounds*, not letters; teach liaison as restoration of hidden sounds; delay double batchim to A2; teach typing early.

### 6.4 The 90-day A1 path — "Everyday Korean"

| Week | Grammar core | Vocabulary | Scenes / missions | Assessment |
|---|---|---|---|---|
| **1** | Hangul bootcamp | 50 words | Self-intro, read a menu | Read-aloud + intro recording |
| **2** | 을/를, 에/에서, 도/만; past -았/었- | 120 | Café, convenience store, directions | 5-item check |
| **3** | ㅂ/ㄷ/ㅅ/르/ㅎ irregulars; -(으)ㄹ 거예요; -고 싶다 | 200 | Taxi, restaurant, shopping | 5-item check |
| **4** | -고, -아서/어서, -지만, -는데; comparatives | 280 | Phone call, appointment, pharmacy | 30-day can-do |
| **5–6** | -고 있다; -겠-; -(으)ㄹ까요?/-ㄹ래요; counters | 350–420 | Market, bank, post office, doctor | 10-item check |
| **7–8** | -시- and lexical honorifics; speech levels; request forms | 450–500 | Workplace intro, asking a favor, polite refusal | Roleplay |
| **9–10** | Relative clauses intro; -다고; -기 때문에; -면서 | 500–600 | Storytelling, plans, explaining a problem | 10-item check |
| **11–12** | Spiral review; repair strategies; pronunciation consolidation | 600–700 | Unscripted 5-minute conversation; 8–10 scenarios | 90-day can-do + recorded artifact |

**A1 outcomes:** 600–700 words, 40–50 patterns, 8–10 transactional scenes, 5-minute daily-life conversation, intelligible pronunciation, Hangul reading at 100+ syllables/min.

### 6.5 Beyond A1

| Phase | Focus | Content | Outcome |
|---|---|---|---|
| **A2 (months 4–8)** | Fluency, listening, connected speech, past narratives | 30 more scenes, graded stories, 1,500–2,000 words, 80 patterns | Handle most daily situations; understand slow native speech |
| **B1 (months 8–18)** | Opinions, abstraction, relative clauses, reported speech, honorific systems | News, short essays, drama clips, 3,000–4,000 words | Narrate, explain, argue; TOPIK 3–4 readiness |
| **B2+ (18+ months)** | Register, genre, idiom, speed, writing | Editorials, workplace, debate, 5,000+ words | TOPIK 5–6; professional/academic use |

### 6.6 Specialized tracks

- **Travel:** 20 missions, survival phrases, listening to announcements, reading signs.
- **Workplace:** honorifics, email, meetings, phone, indirect requests, industry vocabulary.
- **TOPIK:** level diagnostic, timed reading/listening, writing templates, mock exams, error log.
- **K-drama:** licensed/curated clips, scene vocabulary, shadowing, pragmatics notes, no subtitle crutch.
- **Heritage:** receptive→productive bridge, formal register, reading/writing, identity-affirming content.

### 6.7 Vocabulary and grammar sequencing

- Sequence by **frequency and coverage**, not textbook topic. Top 1,000 lemmas ≈ 75–80% of everyday spoken tokens; 2,000 ≈ 88–92%; 3,000 ≈ 93–95%; 5,000 ≈ 96–98%.
- Teach **Sino-Korean morphemes** at B1 (학, 전, 문, 비, etc.); one morpheme unlocks dozens of words.
- Teach **numbers as a selection rule**: Sino for dates/money/phone/minutes; native for counters/hours/age/small quantities.
- Teach **particles by discourse function**, not translation: 은/는 topic/contrast vs 이/가 new/identificational subject. Particle errors are ~28% of beginner errors, mostly omission and substitution.
- Teach **conjugation as slots**: stem + pre-final + final (honorific, tense, aspect, mood). Do not front-load tables; teach 3–4 high-frequency forms per verb and let the paradigm fill in.
- Teach **speech levels as formality/distance**, not a politeness ladder. Default 해요체; 합니다체 for public/professional; 반말 only with licence.
- Teach **zero-anaphora** from A2: who is the omitted subject, and what does the particle signal?

The full Korean-specific brief, with phonology tables and a 0→TOPIK 6 map, is in `docs/research/03-korean-pedagogy.md`.

---

## 7. Experience design

### 7.1 Information architecture

Five destinations, one primary action:

1. **Today** — the daily plan, review load, next can-do, streak.
2. **Practice** — review queue, Sound Gym, weak-skill drills.
3. **Scenes** — mission library and roleplay.
4. **Immerse** — graded stories, drama clips, listening.
5. **You** — progress, artifacts, notebook, settings.

The nav is a bottom tab bar on mobile and a slim sidebar on desktop. No hamburger for primary navigation. The current page is always obvious.

### 7.2 Screen-by-screen specification

#### Today

- Greeting with the learner's name and local time.
- **One primary card:** "Today's 10 minutes" with a 3-block preview (Review 4 min · Café mission 4 min · Debrief 1 min).
- **Review load forecast:** "23 cards due · ~6 min." If overloaded: "You're 2 days behind. Here's a 4-minute catch-up."
- **Next can-do:** "Order coffee without English." Progress ring: 2 of 3 mission criteria met.
- **Words you can use:** 312 (coverage meter for the current path).
- **Secondary:** "2-minute minimum" button, "Continue yesterday's scene."
- No feed, no leaderboard, no ad.

#### Review

- Full-screen card, one target per screen.
- Prompt first: audio or English/Situation; answer hidden.
- Input modes: speak (push-to-talk), type (Hangul IME), tap word bank, or reveal.
- After answer: correct/almost/incorrect with the smallest explanation, audio, and a "why" drawer (particle, register, literal gloss).
- Grade buttons: Again / Hard / Good / Easy; auto-grade when ASR is confident, always allow override.
- Keyboard: Space = play, Enter = submit, 1–4 = grade, H = hint.
- Progress: "7 of 23" with a thin bar; no hearts, no timer pressure.
- "I don't know" is a first-class button; it teaches instead of punishing.
- Leech cards are intercepted: "This one keeps slipping. Let's make it easier." → recognition variant, mnemonic, or split.

#### Sound Gym

- 3–5 minutes, 8–12 reps.
- **Perception:** "Which did you hear?" with 3 minimal-pair options (불/뿔/풀), 5–8 voices, immediate feedback and replay at 0.75×.
- **Production:** record a word/sentence; show waveform + pitch contour against a native reference; band feedback ("clear," "almost — release the final consonant," "try again").
- **Feature coaching:** mouth/tongue diagram, short video, one cue ("ㅋ: more air").
- **No global score.** Show per-feature evidence: "Coda release: improving; ㅓ/ㅗ: shaky."
- End with a 10-second "best take" the learner can keep.

#### Scene (mission roleplay)

- **Mission card:** persona, goal, success criteria, 2–3 target chunks, register constraint ("use polite Korean").
- Example: "You're at a café. Order one iced Americano and ask for a receipt. Use 해요체."
- **Voice-first:** push-to-talk; transcript appears; "what I heard" is editable.
- **Scaffolds:** hint, word bank, "say it for me," slower replay, type instead.
- **AI character** responds in character, not as a narrator. It should not ask a question every turn.
- **Branching is a goal state machine**, not free chat: the scene ends when the goal is met or the learner exits. This keeps cost and quality bounded.
- **No mid-scene grade.** One implicit recast if needed; corrections wait for the debrief.
- **Debrief:** "You ordered, asked for a receipt, and stayed polite. Two things: (1) ... (2) ... Try this one line again." Three cards added; one "say it better" retry.
- **Replay:** full audio, line-by-line, hide English, hide Korean, shadow mode.

#### Immerse

- Graded story or clip with a **coverage meter**: "96% of words known."
- Listen-first mode: audio plays before text; text reveals on tap.
- Tap a word: gloss, audio, morphology, "add to Kiku."
- **Clip-to-card:** select a sentence → card with audio, source, and context.
- Dual subtitles with blur; Korean-first default at A2+.
- End with 3 comprehension questions and 2 mined cards. No passive binge.

#### You (progress)

- **Can-do list** with dates and audio artifacts: "Order coffee — 12 Oct 2026."
- **Skill map:** six strands with solid/shaky/new states and one next action each.
- **Retention:** "You remembered 87% of items introduced 30 days ago." This is the honest scoreboard.
- **Words you can use:** count + coverage of top 1K/2K/3K.
- **Before/after audio:** play day 1 vs today.
- **Weekly recap:** "You fixed 은/는 vs 이/가 in 4 of 5 tries. Next: coda release."
- **TOPIK/CEFR estimate** with uncertainty and the date of the last assessment.
- **Notebook:** saved words, sentences, scenes; search; tags; export.
- No XP total as the hero metric.

#### Settings

- Daily time, reminder time, notification off, vacation mode, streak repair.
- Correction intensity (light / balanced / thorough).
- Audio speed, voice preference, auto-play, haptics.
- Korean-first vs English-first UI at A2+.
- Accessibility: reduced motion, high contrast, large text, captions, screen-reader labels.
- Data: export, delete, voice retention (default 24–72 h), privacy notice.

### 7.3 The first 5 minutes, precisely

| Time | Screen | What happens |
|---|---|---|
| 0:00 | Welcome | "You'll speak Korean in the next two minutes." One CTA. |
| 0:10 | Goal | Six cards; one tap. |
| 0:25 | Time | 3 / 10 / 25 minutes. |
| 0:35 | Experience | Four options; skip placement if "never." |
| 0:45 | First sound | Teach 안녕하세요 with audio + mouth cue. |
| 1:15 | First speak | Record; playback; one specific compliment. |
| 2:00 | Micro-win | "That's your first Korean sentence." Save artifact. |
| 2:20 | Plan | "Your first week: read Hangul by Sunday." |
| 2:40 | Account | Save progress; implementation intention. |
| 3:00 | Today | First session ready. |

### 7.4 Motivation system

**Do:**
- Days practiced, not "streak or die."
- One planned rest day per week; vacation mode; repair by practice, not payment.
- 2-minute minimum day; 10-minute default; 25-minute deep day.
- Mastery bars and can-do artifacts.
- Weekly recap with one specific improvement.
- Optional 5-person pod for accountability (later); no open DMs.

**Don't:**
- Hearts that block learning.
- Loss-framed notifications ("You're about to lose...").
- Leaderboards for beginners.
- Pay-to-repair streaks.
- Fake urgency or "you're behind" shame.
- XP as the primary progress metric.

**Implementation intentions:** during onboarding and monthly review, capture "When [cue], I will do [10 minutes] at [place]." Send the reminder at the chosen time only; max one per day; value-carrying; easy opt-out.

### 7.5 Accessibility and inclusion

- Mark Korean text with `lang="ko"`; UI language with `lang="en"` until localized.
- Visible focus states; no `outline: none` without replacement.
- Contrast ≥ 4.5:1 for body text; don't use white on orange.
- `prefers-reduced-motion`; no autoplay audio without a visible control.
- Captions/transcripts for all audio; adjustable speed; mono option for listening.
- Screen-reader labels for every audio/repeat/record control; live regions for status, not hidden ones.
- Keyboard-only operation; Hangul IME guidance; mobile thumb zones.
- No color-only feedback; icons + text.
- Dyslexia-friendly font option; large-text mode.

### 7.6 Mobile and PWA

- PWA first: installable, offline review queue (IndexedDB), media caching, push where supported.
- Touch targets ≥ 44 px; bottom-sheet interactions; one-hand reach for the primary CTA.
- Record button is large, central, and forgiving; VAD tolerates pauses; cancel is obvious.
- iOS limitations (background audio, push, storage) are acceptable for v1; move to Expo only if >30% of WAU are iOS and push/offline is a proven churn driver.
- Desktop: wider layout, keyboard shortcuts, side-by-side transcript/debrief, focus mode.

---

## 8. Content and AI system

### 8.1 Content architecture

Three layers, in order of trust:

1. **Canonical layer (truth):** curated words, chunks, grammar patterns, dialogues, register rules, audio. Native-reviewed. Versioned. The LLM may not invent outside it.
2. **Generative layer (variation):** LLM creates examples, distractors, explanations, and scene turns **within slots** defined by canonical items. Strict JSON schema; item IDs required.
3. **Validation layer (gate):** Hangul/syllable checks, Kiwi morphology, deterministic particle/conjugation/register rules, krdict lookup, frequency-band check, romanization by rule engine, dedupe, native review for new patterns.

**Never ship raw LLM Korean.** The model proposes; the pipeline disposes.

### 8.2 Generation pipeline

```
prompt + retrieved item IDs + level + register + scene goal
  → LLM (strict json_schema, temperature 0.2–0.4)
  → Pydantic / JSON Schema validation
  → Hangul range + syllable-block validation (U+AC00–U+D7A3)
  → Kiwi morphology + POS checks
  → deterministic rules: particles, endings, honorific agreement, spacing
  → krdict lookup (lemma, POS, pronunciation, level)
  → frequency-band check (wordfreq / KLI list)
  → romanization by rule engine (Revised Romanization; never the LLM)
  → dedupe (hash + embedding)
  → native review queue for new patterns
  → publish with content hash + version
```

**Failure policy:** if any gate fails, fall back to a curated line. A slightly less varied correct sentence beats a fluent wrong one. Log every rejection; a rising rejection rate is a content-quality alarm.

### 8.3 Audio pipeline

- **Pre-generate** all core lexemes, examples, grammar patterns, and dialogue lines at publish time. 3,000 items × ~40 chars ≈ 120k chars ≈ $2–$10 one-time.
- **Cache by content hash:** `sha256(normalized_text|voice|model|speed|style|format)`. Immutable, CDN-served.
- **Normalize** to −16 LUFS; store Opus + MP3 fallback; generate 1.0× and time-stretch 0.7–1.1× client-side.
- **Voices:** clear adult Korean voices; 5–8 talkers for perception training; two-voice dialogue for scenes; avoid caricature.
- **Korean pitfalls:** liaison, ㅎ aspiration, nasalization, tensification, loanwords, numbers/counters, hanja readings. Pre-pass G2P (`g2pk`/`g2pkk`) or use a custom lexicon; native A/B on new patterns.
- **Dynamic TTS** only for scene turns and explanations; cap per user; use a cheaper model for free tier.

### 8.4 Speech and pronunciation

**Three-stage design:**

1. **Comprehensibility:** `gpt-transcribe` or Azure STT → word diff, latency, pause count. This is the gate for "did the learner say the intended words?"
2. **Pronunciation evidence:** Azure Pronunciation Assessment (`ko-KR`) for phoneme/word accuracy, fluency, completeness; SpeechSuper for Korean rhythm/syllable feedback where needed. Note: Azure syllable aggregation and prosody are en-US only.
3. **Prosody in-house:** pYIN F0, syllable-duration ratios, speech rate, pauses; DTW against a native reference; banded feedback ("phrase break too early"), not a fake 0–100.

**Hard rules:**
- ASR is not a pronunciation grade. L2 Korean ASR can show near-zero WER while correlating weakly with human ratings; it silently repairs the errors you want to detect.
- Show what was heard; allow retry, type, or skip.
- Score intelligibility and comprehensibility, not "nativeness."
- Calibrate on L2 Korean; maintain a false-negative budget (<2%).
- Delete raw audio within 24–72 h by default; opt-in to save; never build speaker ID.

**90-day shippable scope:** 20–30 minimal pairs; word-level intelligibility gate; F0/duration contour comparison; formant scatter for ㅓ/ㅗ and ㅡ/ㅜ; band feedback. No global pronunciation score.

### 8.5 Evaluation harness

The eval harness is the moat, not the prompts.

- **Gold set:** 500–1,000 items stratified by TOPIK level and grammar point, each rated by 2–3 native speakers on grammaticality, naturalness, level fit, translation fidelity, and romanization.
- **Metrics:** agreement (Krippendorff's α), error rate by category, regression deltas per release.
- **Adversarial suite:** particles, honorifics, translationese, spacing, romanization, counter/number selection, register mixing.
- **LLM judge calibration:** only after ≥300 human labels; never replace native review for new patterns.
- **Release gate:** <1% native-rated error rate on the gold set; no regression >0.5%.

### 8.6 Content operations

- **Editorial calendar:** 30 scenes for launch, 5 new per week after.
- **Native reviewer pool:** 2–3 Korean teachers; paid per reviewed item; clear rubric.
- **Versioning:** every item has a content hash, author, reviewer, and status (`draft`, `reviewed`, `published`, `retired`).
- **Correction path:** in-app "report a problem" on every card; triage within 48 h; fix propagates to all learners; log the correction.
- **Licensing:** krdict (CC BY-SA 2.0 KR), KLI/TOPIK lists, licensed media; no scraping Naver; attribute sources.

---

## 9. Technical architecture

### 9.1 Principles

1. **Evolve, don't rewrite.** The Flask app factory is salvageable. Strangle the prototype; don't restart.
2. **Postgres for learner data.** SQLite is fine for a single-user demo; it is not fine for concurrent review writes.
3. **Async for anything slow.** LLM, TTS, merge, and scoring are jobs, not request handlers.
4. **Content-addressed media.** DB stores keys, not public URLs; signed playback.
5. **Every write is user-scoped.** No global tables without `user_id`.
6. **Every model output is untrusted.** Validate, then render with `textContent`/safe templating.
7. **Every expensive call is metered.** Vendor, model, units, cost, latency, user, job.
8. **Offline-tolerant review.** Client-generated event IDs, idempotent replay.

### 9.2 Target architecture

```
PWA (Jinja/HTMX or Next.js)
  MediaRecorder · WebAudio · IndexedDB (Dexie) · Workbox
        │ HTTPS / WSS
  API gateway: auth · rate limits · feature flags · cost budgets
        │
  ┌─────┴──────────────┬──────────────────┐
  Flask web/app        FastAPI AI sidecar  Event ingest
  content, review,     ASR · TTS · LLM ·   (PostHog +
  billing, admin       pronunciation       append-only)
  └─────┬──────────────┴────────┬─────────┘
        │                       │
  Postgres 16 + pgvector   Redis (cache/queue)
        │                       │
  RQ workers                Object storage (R2/S3)
  TTS · batch PA · FSRS     audio · signed URLs
  optimize · generation     lifecycle rules
        │
  Vendors: OpenAI · Azure · SpeechSuper · krdict
```

**Stack for the first 90 days:** Flask 3 + Jinja/HTMX + Tailwind/Alpine; Postgres 16 + pgvector; SQLAlchemy 2 + Alembic; Redis + RQ; `py-fsrs`; `kiwipiepy`; `g2pk`/`g2pkk`; `wordfreq`; krdict client; Azure Pronunciation Assessment + `gpt-transcribe`; Azure/OpenAI TTS; PWA with Dexie/Workbox; Sentry, PostHog, Stripe, R2, GitHub Actions.

**Why not Next.js yet:** one codebase, one deploy, server-rendered pages are enough for the core loop. Revisit after the first 500 users if the interaction complexity demands it.

### 9.3 Data model

| Table | Key fields |
|---|---|
| `users` | id, email, auth_provider, created_at, locale, timezone, status |
| `profiles` | user_id, display_name, goal, daily_minutes, correction_intensity, interests |
| `enrollments` | user_id, path_id, level, started_at, target_date |
| `items` | id, type, surface, normalized, level, freq_rank, metadata jsonb, content_hash, status |
| `item_relations` | parent_id, child_id, relation (prereq/contains/contrasts) |
| `senses` | item_id, gloss, pos, examples, audio_asset_id |
| `grammar_points` | pattern, level, prerequisites, explanation, register |
| `audio_assets` | content_hash, voice, model, storage_key, duration_ms, loudness, license |
| `review_cards` | user_id, item_id, skill, stability, difficulty, due, state, reps, lapses, leech |
| `review_logs` | card_id, rating, reviewed_at, elapsed_ms, scheduled_days, stability, difficulty |
| `attempts` | user_id, item_id, skill, modality, response, correct, score, latency_ms, audio_asset_id, model_version |
| `phone_scores` | attempt_id, phone, expected, observed, score, start_ms, end_ms |
| `skill_mastery` | user_id, skill, theta, mastery_prob, alpha, beta, updated_at |
| `scenes` | id, title, level, goal, persona, success_criteria, target_items, register, status |
| `scene_turns` | scene_id, order, speaker, korean, english, audio_asset_id, hints |
| `scene_sessions` | user_id, scene_id, started_at, completed_at, success, transcript jsonb, debrief jsonb |
| `sessions` | user_id, plan jsonb, started_at, completed_at, minutes, success_rate |
| `session_items` | session_id, item_id, skill, order, result |
| `artifacts` | user_id, type, label, audio_asset_id, created_at, can_do_id |
| `can_dos` | path_id, level, statement, assessment_method |
| `events` | user_id, name, props jsonb, session_id, schema_version, created_at |
| `api_usage` | vendor, operation, units, cost_usd, user_id, job_id, created_at |
| `consents` | user_id, type, granted_at, revoked_at, version |
| `jobs` | id, type, payload, status, attempts, run_at, error, idempotency_key |

**Key constraints:** unique `(user_id, item_id, skill)` on cards; unique `(conversation/scene_id, order)`; unique `(user_id, normalized_text)` where appropriate; foreign keys on; UTC timestamps; soft delete for learner content.

### 9.4 API surface (v1)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/auth/*` | Sign up/in (Clerk/Supabase or Flask-Login) |
| `GET` | `/v1/me/today` | Daily plan, due count, next can-do |
| `POST` | `/v1/sessions` | Start a session; returns blocks |
| `GET` | `/v1/sessions/{id}/next` | Next item in the session |
| `POST` | `/v1/attempts` | Record a review/answer; returns grade + next |
| `POST` | `/v1/audio/score` | Upload utterance; returns transcript + evidence |
| `GET` | `/v1/content/{id}` | Item detail, audio URL, notes |
| `GET` | `/v1/scenes` | Mission library filtered by level/goal |
| `POST` | `/v1/scenes/{id}/sessions` | Start a roleplay |
| `POST` | `/v1/scenes/{id}/turns` | Send a turn; returns character reply + transcript |
| `POST` | `/v1/scenes/{id}/debrief` | Generate debrief + cards |
| `GET` | `/v1/progress` | Skill map, retention, can-dos, artifacts |
| `GET` | `/v1/placement` | Start placement; `POST` answers |
| `POST` | `/v1/events` | Batched analytics events |
| `GET` | `/v1/notebook` | Saved items, search, tags |
| `POST` | `/v1/reports` | Content problem report |
| `GET` | `/admin/review` | Native review queue (staff only) |

**Conventions:** JSON envelope with `data`/`error`; request IDs; idempotency keys on writes; `202 + job_id` for slow operations; pagination with stable `(created_at, id)` ordering; versioned schema; OpenAPI.

### 9.5 Migration from the current repository

| Current | Target | Action |
|---|---|---|
| `Phrase` | `items` + `senses` + `audio_assets` | Migrate text/audio; add level, freq, type, content hash |
| `Conversation` | `scenes` | Add goal, persona, success criteria, target items, status |
| `ConversationLine` | `scene_turns` | Add speaker enum, hints, audio asset FK |
| `app/static/audio` | Object storage | Upload, hash, sign; delete orphans; remove from git |
| `Phrase.uuid` | `items.public_id` | Keep stable public IDs |
| CLI `hangul.py` | Thin client / deprecated | Point at the same service or remove |
| No users | `users` + `profiles` | Add auth and backfill a single demo user |
| No review | `review_cards` + `review_logs` | Seed from curated items; no card for every phrase automatically |

**Do not** migrate the current global data into a multi-user product without assigning ownership. Start with a clean seed and, if needed, a one-time import for the owner.

### 9.6 Security, privacy, and operations

- **Rotate the exposed OpenAI key now.** It is in `.env`; assume compromise.
- Server-side secrets only; per-environment scope; quarterly rotation.
- Auth on every learner route; authorization check on every object; no IDOR.
- CSRF protection for session/cookie flows; strict CSP; HSTS; secure cookies; `ProxyFix` behind a proxy.
- Rate limit by user + IP with Redis; separate buckets per endpoint; `Retry-After`; cost budgets per user/day.
- Validate all input and model output; render with `textContent`/Jinja autoescape; sanitize if rich text is ever allowed.
- Signed, short-lived audio URLs; strip metadata; no public static audio directory.
- Voice is personal data. Raw audio deleted 24–72 h after scoring by default; explicit opt-in to save; no speaker identification; minors: age gate + verifiable parental consent under 13; COPPA 2025 / GDPR / PIPA review.
- Structured logs with request/job IDs; redact text and audio; Sentry; PostHog; cost/latency dashboards.
- Backups, restore drills, migration gate in CI, health check, runbook.
- Dependency hygiene: upgrade Flask/Werkzeug/SQLAlchemy/gunicorn; `pip-audit`; Dependabot.

### 9.7 Cost model

Per monthly active learner: 400 study minutes, 160 speech minutes, 1,200 reviews, 150 LLM calls, 20k dynamic TTS chars.

| Line | Low | High |
|---|---|---|
| ASR + pronunciation | $1.00 | $3.00 |
| TTS (dynamic) | $0.30 | $1.60 |
| LLM + embeddings | $0.11 | $1.55 |
| Storage + egress | $0.10 | $0.40 |
| Infra share | $0.30 | $0.80 |
| **Total** | **$1.81** | **$7.35** |

At $14.99/month, gross margin is 51–88% before Stripe and CAC. Target <$4 variable cost (~73%). Levers: pre-generate core audio, batch scoring, cache by content hash, Azure commitment tiers, on-device WhisperKit for the free tier, cheaper models for free users.

---

## 10. Roadmap

### 10.1 Phase overview

| Phase | Time | Goal | Exit criteria |
|---|---|---|---|
| **0. Stabilize** | Weeks 1–2 | Make the prototype safe and truthful | Key rotated; no import-time clients; timeouts; XSS fixed; WAL/FK; temp cleanup; tests + CI; migration baseline; auth gate or local-only; README corrected |
| **1. Learning core** | Weeks 3–6 | Ship the daily loop | Postgres + users; 300 items + 20 scenes seeded; FSRS review; Today/Review/You screens; onboarding + first spoken sentence; 20 alpha users; 80% test coverage on services |
| **2. Speech + scenes** | Weeks 7–12 | Make it voice-first | Push-to-talk; pronunciation evidence; Sound Gym; 30 scenes; debrief → cards; 5–8 voices; native eval harness; <2% ASR false negatives |
| **3. Adaptive + beta** | Weeks 13–20 | Make it personal and measurable | Elo/BKT/bandit; placement; leech intervention; PWA/offline; can-do artifacts; retention dashboards; 100–500 beta users; D30 ≥ 15% |
| **4. Expansion** | Months 6–12 | Depth and business | TOPIK/workplace/K-drama/heritage tracks; writing feedback; human review; pricing; B2B pilot; B2 boundary |

### 10.2 Phase 0 checklist (do this first)

**Security and truth**
- [ ] Rotate the OpenAI key; remove the live key from the working tree; confirm `.env` is ignored.
- [ ] Fail closed on missing config; no module-level `OpenAI()`.
- [ ] Set explicit timeouts (connect 5 s, read 20 s) and `max_retries=0/1`; retry only 429/5xx/timeouts with backoff.
- [ ] Fix `new_conversation.js` XSS: build nodes with `textContent`; add CSP.
- [ ] Add auth or bind to localhost; add CSRF if cookies are used.
- [ ] Fix API 404 → 500; stop returning `str(e)` to clients.
- [ ] Validate conversation prompts and LLM output with a schema; enforce 2–4 lines, speaker ∈ {1,2}, string lengths, Hangul presence.

**Data integrity**
- [ ] Enable WAL, `busy_timeout=5000`, `PRAGMA foreign_keys=ON`.
- [ ] Stage media in a temp dir; commit metadata; delete staged files on failure; add an orphan sweeper.
- [ ] Add unique/normalized keys and content-hash audio; stop regenerating duplicates.
- [ ] Fix the migration baseline; remove `db.create_all()` from startup; run `flask db upgrade` in deploy.
- [ ] Delete the 15 orphan MP3s and untrack audio from git.

**Engineering**
- [ ] Add `pytest`, `pytest-flask`, `respx`, `freezegun`, `Playwright`, `ruff`, `mypy`, `pip-audit`.
- [ ] Add `TestingConfig` with in-memory DB and temp audio; inject fake OpenAI/clock/storage.
- [ ] Cover failure paths: TTS fails on line N, merge fails, commit fails → zero rows and zero files.
- [ ] Add CI: lint, type, test, migration-on-empty-DB, orphan-file check.
- [ ] Update README to match reality; remove false claims.

### 10.3 Phase 1 — the core loop (4 weeks)

**Week 3: foundation**
- Postgres + Alembic; user/profile/enrollment tables; auth.
- Content schema: items, senses, grammar_points, audio_assets, scenes, scene_turns.
- Seed 300 items (frequency-ordered, level-tagged) and 20 scenes; pre-generate audio.
- Event tracking and a minimal admin review queue.

**Week 4: review engine**
- `py-fsrs` integration; one card per (item, skill).
- Review API + UI: prompt, answer, grade, explanation, keyboard/IME.
- Today screen with due count and time forecast.
- Retention and load dashboards (internal).

**Week 5: onboarding + first win**
- Goal/time/experience flow; 8-item placement; first spoken sentence.
- Implementation intention; account creation after the win.
- Hangul day 1–3 lessons; typing drill.

**Week 6: alpha**
- Hangul bootcamp days 4–7; 10-minute daily plan.
- Can-do artifact + You screen (skill map, words known, retention).
- Invite 20 alpha users; instrument activation and D1/D7; weekly interviews.

**Exit:** a new learner can sign up, speak Korean in under 2 minutes, complete a 10-minute session, review tomorrow, and see one can-do artifact. No crashes; no orphan files; p95 review < 200 ms.

### 10.4 Phase 2 — speech and scenes (6 weeks)

**Weeks 7–8: voice capture + scoring**
- MediaRecorder, push-to-talk, upload, waveform, retry.
- `gpt-transcribe` for word-level intelligibility; Azure PA for phoneme/word evidence; store `phone_scores`.
- "What I heard" transcript; retry/type/skip; false-negative logging.
- 20 minimal-pair drills; 5–8 voices.

**Weeks 9–10: Sound Gym**
- Perception and production modes; F0/duration contour; formant scatter for ㅓ/ㅗ and ㅡ/ㅜ.
- Band feedback + mouth/tongue diagrams; no global score.
- Weekly pronunciation artifact.

**Weeks 11–12: scenes + debrief**
- Scene engine: goal state machine, persona, target chunks, success criteria.
- LLM character turns constrained to canonical slots; validator + fallback.
- Debrief: 2 strengths, 1 fix, 3 cards; one retry.
- 30 scenes across café, taxi, directions, shopping, phone, doctor, market, bank, workplace intro.
- Native eval harness (500 items) and release gate.

**Exit:** learner can hold a 3–5 minute mission, get intelligible feedback, and see errors become tomorrow's cards. <1% native-rated content errors; <2% ASR false negatives; p95 speech feedback < 3 s.

### 10.5 Phase 3 — adaptive + beta (8 weeks)

- Elo calibration; BKT mastery; Thompson-sampling selection.
- Placement test with uncertainty; recommended start.
- Leech intervention; scaffold automation; difficulty targeting.
- PWA: install, offline review queue, media cache, push (where supported).
- Can-do progress, weekly recap, before/after audio.
- Streak ethics: rest day, repair by practice, vacation, notification controls.
- Beta 100–500 users; retention and learning dashboards; interviews; pricing test.
- Security/privacy review; DPA; voice retention; age gate.

**Exit:** D1 ≥ 45%, D7 ≥ 25%, D30 ≥ 15% (aspirational for a niche learning app), 30-day item retention ≥ 85%, variable cost < $4/MAU, NPS ≥ 40.

### 10.6 Phase 4 — expansion (months 6–12)

- TOPIK track: diagnostic, timed sections, writing templates, mock exams.
- Workplace track: honorifics, email, meetings, phone, industry vocabulary.
- K-drama track: licensed clips, scene mining, shadowing, pragmatics.
- Heritage track: receptive→productive bridge, formal register, literacy.
- Writing feedback: rubric-based LLM + human escalation.
- Human review marketplace: native teachers for async feedback.
- B2B pilot: universities, heritage schools, employers.
- Native mobile app only if PWA data justifies it.

### 10.7 Metrics tree

**North star:** **Weekly Can-Do Proofs (WCP)** — the number of learners per week who demonstrate at least one unrehearsed can-do at their target level (recorded/spoken, assessed, not self-reported).

| Layer | Metric | Target |
|---|---|---|
| **Activation** | % who speak a Korean sentence in first 2 min | ≥ 80% |
| | % who complete first session | ≥ 60% |
| **Engagement** | Sessions/week | ≥ 4 |
| | Median session length | 8–12 min |
| | Review adherence (due cards done) | ≥ 75% |
| **Learning** | 30-day item retention | ≥ 85% |
| | Can-do pass at 7 / 30 days | ≥ 70% / ≥ 60% |
| | Vocabulary coverage of top 1K/2K | path-specific |
| **Quality** | Native-rated content error rate | < 1% |
| | ASR false-negative rate | < 2% |
| | Correction acceptance rate | ≥ 60% |
| **Retention** | D1 / D7 / D30 | 45% / 25% / 15% |
| **Business** | Variable cost / MAU | < $4 |
| | Gross margin | ≥ 70% |
| | LTV:CAC | ≥ 3 |
| **Guardrails** | Notification opt-out | < 10% |
| | Self-reported anxiety | stable or down |
| | Refund rate | < 5% |

**Experiments:** onboarding length, first-win type, correction timing (flow vs debrief), session length (5 vs 10 vs 15), streak framing (days vs streak), audio-first vs text-first, free-tier AI minutes. Pre-register hypotheses; learning outcomes primary; engagement guardrails; never A/B test shame or paywalls on vulnerable learners.

### 10.8 Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope creep (too many tracks/features) | High | High | One path (Everyday A1) until D30 ≥ 15%; kill non-core work |
| Content errors destroy trust | Medium | High | Canonical layer, validation, native review, <1% gate, report button |
| ASR false negatives demoralize | High | High | Show transcript, retry/type/skip, calibrate on L2, <2% budget, never grade |
| AI cost exceeds margin | Medium | High | Pre-generate, cache, cheap models for free tier, caps, cost dashboards |
| Solo-dev bandwidth | High | High | Ruthless MVP; buy auth/billing/infra; no custom ML early |
| Retention stays low | Medium | High | First-win onboarding, can-do proof, weekly recap, user interviews |
| Privacy/regulatory issue | Low | High | Voice retention, consent, age gate, DPAs, legal review before beta |
| Competition copies features | High | Medium | Moat = learner model + validated content + outcome data, not features |
| Korean linguistic errors in generated scenes | Medium | High | Slot-constrained generation, validator, fallback, native review |
| Burnout / ethical debt | Medium | Medium | No dark patterns; rest days; measure anxiety; ship smaller |

**Kill criteria:** if after 8 weeks of beta D30 < 8% and can-do pass < 40%, stop adding content and re-run onboarding/value-proof interviews before building more. If content error rate cannot get below 2%, pause generation and ship curated-only.

### 10.9 Team and cadence

Minimum viable team: 1 product engineer + 1 Korean content lead (part-time native teacher) + 1 designer (part-time) + 1 advisor in SLA/assessment. A solo dev can ship Phase 0–1; Phase 2 needs content review capacity.

Cadence: weekly ship, biweekly learner interview, monthly native content audit, monthly metrics review. Public changelog; no silent breaking changes.

---

## 11. The ultimate vision (12–36 months)

**Year 1 — "It works."** A1–B1 Everyday path, voice-first scenes, FSRS memory, honest can-do proof. 10k–50k active learners. The product is trusted because it never teaches wrong Korean and never lies about progress.

**Year 2 — "It knows me."** Persistent learner model across tracks; TOPIK/workplace/heritage; writing feedback; human review marketplace; creator-authored scenes with native validation; B2B pilots. The moat is the learner graph: every error, interest, and successful mission makes the next session better.

**Year 3 — "Korean operating system."** A life-wide learning companion: prepare for a meeting, rehearse a doctor's visit, understand a drama, pass TOPIK, onboard at a Korean company. APIs for schools and employers. Certification partnerships. The brand promise remains the same: **listen, speak, remember.**

**What must never change:**
- Grounded Korean over generated fluency.
- Proof over points.
- The learner's time and dignity over engagement metrics.
- One honest next step, always.

---

## Appendix A — The 10-minute session, minute by minute

| Time | Block | What the learner does | What the system does |
|---|---|---|---|
| 0:00–0:30 | Warm-up | Recalls 2–3 due items | Selects highest-value due cards; audio-first |
| 0:30–4:00 | Review | Retrieves 8–12 items; speaks/types | Grades, schedules, logs errors, adapts difficulty |
| 4:00–6:30 | Sound Gym | Discriminates 4–6 minimal pairs; records 2 lines | Plays multiple voices; scores evidence; gives one cue |
| 6:30–9:00 | Scene | Completes a mission with 2–3 target chunks | Plays a character; recasts once; tracks goal state |
| 9:00–9:45 | Debrief | Hears 2 strengths + 1 fix; retries one line | Creates 3 cards; tags error; updates mastery |
| 9:45–10:00 | Win | Records one can-do sentence | Saves artifact; shows progress delta; schedules tomorrow |

## Appendix B — Sample cards

**Lexeme — recognition**
- Audio: 커피
- Prompt: What does this mean?
- Answer: coffee
- Reveal: image, example (커피 한 잔 주세요), hanja note if relevant.
- Skills: recognize → recall → produce (separate cards).

**Chunk — production**
- Prompt: "One coffee, please." (café icon)
- Expected: 커피 한 잔 주세요.
- Scaffolds: word bank → first syllable → full model.
- Feedback: "Polite request with 주세요. 한 잔 is the counter for cups."

**Grammar — completion**
- Prompt: 비가 와___ 우산을 가져갔어요. (Because it rained, I took an umbrella.)
- Options: 서 / 니까 / 지만
- Feedback: "-아서/어서 expresses cause/sequence; it cannot precede an imperative. Here it is correct."

**Minimal pair — perception**
- Audio: [불] (one of 불/뿔/풀)
- Prompt: Which word did you hear?
- Feedback: "Lenis ㅂ: relaxed, low pitch at vowel onset. Tense ㅃ: tighter, higher pitch."

**Pronunciation — production**
- Prompt: 천천히 말해 주세요.
- Record; compare waveform + pitch contour to native.
- Feedback: "Clear. The final /ju/ was a little long; keep the last syllable short."

**Scene turn**
- Persona: barista
- Goal: order an iced Americano and ask for a receipt.
- Learner: 아이스 아메리카노 한 잔 주세요.
- Character: 네, 사이즈는 어떻게 해 드릴까요?
- Constraint: 해요체; target chunks: 한 잔 주세요, 영수증.

## Appendix C — Scene specification template

```yaml
id: cafe_order_01
title: Order coffee
level: A1
goal: Order one drink and ask for a receipt
persona: Barista at a busy café (friendly, slightly hurried)
success_criteria:
  - Order a drink with a counter
  - Answer the size question
  - Ask for a receipt
target_items: [커피, 한 잔, 주세요, 사이즈, 영수증]
register: haeyo
constraints:
  - Use polite Korean
  - No English
turns:
  - speaker: barista
    korean: 어서 오세요, 뭐 드릴까요?
    english: Welcome, what can I get you?
  - speaker: learner
    expected: 아이스 아메리카노 한 잔 주세요.
  - speaker: barista
    korean: 네, 사이즈는 어떻게 해 드릴까요?
  - speaker: learner
    expected: 큰 걸로 주세요.
  - speaker: barista
    korean: 네, 영수증 필요하세요?
  - speaker: learner
    expected: 네, 영수증 주세요.
debrief:
  strengths: 2
  fix: 1
  cards: 3
fallback: curated_lines_only
```

## Appendix D — Glossary

- **FSRS** — Free Spaced Repetition Scheduler; models stability, difficulty, retrievability.
- **BKT** — Bayesian Knowledge Tracing; per-skill mastery estimate.
- **Elo** — pairwise ability/difficulty rating; cheap adaptive item calibration.
- **HVPT** — High-Variability Phonetic Training; perception training with many talkers.
- **Lenis / aspirated / tense** — Korean's three-way stop contrast (ㅂ/ㅍ/ㅃ, etc.).
- **Batchim** — syllable-final consonant; seven surface sounds.
- **Liaison (연음)** — final consonant resyllabifies before a vowel.
- **해요체 / 합니다체 / 반말** — informal polite / formal polite / casual speech levels.
- **Can-do** — a observable real-world task used as the unit of progress.
- **WCP** — Weekly Can-Do Proofs; the north-star metric.

## Appendix E — Decisions and open questions

**Decided**
- Keep Flask and evolve; Postgres + Redis + RQ; PWA first.
- FSRS-6, Elo, BKT, bandit; no deep KT at launch.
- Canonical content + constrained generation + native review; never raw LLM Korean.
- Voice-first, text-scaffolded; no global pronunciation score.
- One path (Everyday A1) until retention is proven.
- Ethical streak: 2-minute minimum, rest day, repair by practice.

**Open**
- Brand name: "Kiku" is a working title and a Japanese word; confirm with Korean-market testing (alternatives: 들어, 소리, 말랑, 이어).
- Free-tier AI minutes: 3 vs 5 vs 10 per day; test willingness to pay and cost.
- Scene engine: state machine vs constrained chat; start state machine, expand only if quality holds.
- Human review marketplace: build vs partner (italki/Preply-style).
- TOPIK writing: LLM rubric vs native grading; likely hybrid.
- Whether to keep the CLI as a power-user tool or deprecate it.
- iOS native timing: after 500 WAU or after push/offline proves to drive retention.

---

*Supporting research:*
- `docs/research/01-codebase-audit.md` — full audit, file:line evidence, debt ranking.
- `docs/research/02-learning-science.md` — memory, retrieval, spacing, motivation, measurement.
- `docs/research/03-korean-pedagogy.md` — Hangul, phonology, morphosyntax, curriculum.
- `docs/research/04-competitive-teardown.md` — 27 products, gaps, pricing, retention patterns.
- `docs/research/05-tech-and-ai.md` — ASR/TTS, validation, adaptive engines, architecture, cost.
