# Competitive Research: Real-Time AI Teacher, On-Demand Drills, and the Personal Term Library (Nov 2026)

**Scope.** Extends `04-competitive-teardown.md`; does not repeat its Duolingo/Teuida/Speak/Praktika/TTMIK/Anki/LingQ/HelloTalk profiles except where the 2025–26 state changed. Focus: the mechanics of *real-time teacher + generated drills + dictionary*, plus Ethiopian-language coverage, human-tutor benchmarks, gap analysis, packaging, and metrics.

**Method.** Vendor help centers and pricing pages first, independent reviews second, user reviews third. Prices are US list, checked 13–23 Nov 2026 unless noted. Claims marked **✓ verified** (primary source), **~ reported** (credible secondary), **△ inference** (my reasoning, not a sourced fact).

---

## 0. What actually changed in 2025–2026

| # | Shift | Evidence | Consequence for Kiku |
|---|---|---|---|
| 1 | **Real-time voice stopped being a premium feature.** Duolingo cut Video Call inference from ~$0.30 to **under $0.01 per call**, then put unlimited Video Call into Super and **sunset Max entirely** (stopped selling new Max in Nov 2026) [1][2][61] | ✓ | You cannot charge $30/mo for "AI conversation" alone. AI voice is now table stakes at ~$13/mo. |
| 2 | **Memory became the headline.** Speak's Oct 2026 AI Tutor Call: "Your tutor knows what you talked about last time"; Duolingo's Lily "remembers details from earlier calls"; Langua has optional long-term memory [4][6][7][9][10] | ✓ | Memory is the feature reviewers now use to separate products. This is Kiku's stated moat — ship it visibly. |
| 3 | **Mistake → generated lesson is now a shipped loop,** not a demo: Speak's "Takeaways" from Free Talk/Roleplay errors become "Made For You" lessons; HanDa turns recurring mistakes into "the next day's practice" [8][9][11] | ✓ | The loop (error → drill → card → reappearance) is the unit of competition, not the chat screen. |
| 4 | **Hands-free / background mode.** Speak AI Tutor Call is screen-off, 8–10 min; Tutor Lesson v2 has Background mode (Live Activity); Langua's Oct 2026 call mode is full-duplex with barge-in [7][12][13] | ✓ | Design for walking/commuting, not for staring at an avatar. |
| 5 | **Correction intensity became a setting:** Langua (subtle / every error / after the call), Praktika (soft / balanced / strict), HanDa (four teachers with four correction styles) [9][14][15] | ✓ | One correction policy cannot fit anxious beginners and B1 fixers. Make it a dial. |
| 6 | **Single-number pronunciation scores are being discredited** by the better products: Langua deliberately gives no score; HanDa argues a "78%" score tells you nothing [9][11] | ~ | Kiku's phoneme-level approach is directionally right; never show one number. |
| 7 | **Korean-only AI tutors arrived.** HanDa, Chamelingo, Lingory, KSI's AI tutor, EBS Topik Ssam, HelloTalk's "Korean Ai" — all 2025–26 [11] | ~ | Korean depth is now *contested*, not an empty field. "Korean" alone is no longer a wedge; Korean *memory + register + proof* is. |
| 8 | **The English-speaking-app long tail commoditized:** ISSEN, Jumpspeak, Pingo, Teacher AI, LinguaLive, SpeakShark, TalkDrill, BetterSpeak — near-identical feature lists at $69–120/yr [16][17] | ~ | Feature parity is cheap. Distribution and a specific learner identity are not. |
| 9 | **AI moved down-market, not up-market.** Duolingo puts AI in Super (~$13/mo); TalkPal's in-app first year is $59.99 [1][18] | ✓ | Price the teacher at $10–15/mo core, not $30. Charge for depth (minutes, exam, workplace), not for "AI". |
| 10 | **Ethiopian languages remain a phrasebook market.** No mainstream app teaches Amharic; only TalkPal claims realtime AI in Amharic/Oromo/Somali, with no script-aware feedback [19][20][21] | ✓ | A credible realtime Amharic tutor is a genuine white space — but a different buyer and a harder data problem (see §2). |

---

## 1. AI conversation/tutor products — current state

### 1.1 Comparison table

Legend: **RT** = real-time spoken interaction; **Drills** = generates practice from your errors on demand; **Mem** = documented cross-session memory; **Dict** = word/phrase capture with review; **Amh** = Amharic support.

**Session length where documented:** Speak AI Tutor Call 8–10 min; Duolingo Video Call capped by a hidden "Closer" (exchanges often 30s, a few turns); Langua 30 min/day cap on Standard; Pimsleur conversations end on their own; most others do not publish a length.

| Product | RT / interaction | Who drives | Correction style & timing | Drills on demand | Mem | Dict | Amh | Free tier | Price (US) | Main complaint |
|---|---|---|---|---|---|---|---|---|---|---|
| **Speak** | ✓ hands-free call; also tap-to-speak lessons | Learner picks topic (call) or app path (course) | In-call + end-of-session "Takeaways"; badges, not phoneme scores (except English coach) | ✓ Made For You: Targeted Practice, Takeaways, Vocab Skill Errors | ✓ "knows what you talked about last time"; mistakes return into calls | Partial: Takeaways, no true personal dictionary | ✗ | None; 7-day trial | $17.99/mo, $83.99/yr; Plus $39.99/mo, $164.99/yr [8][22][23] | ASR false negatives; nonsensical transcript once accepted; shallow feedback [22][24] |
| **Duolingo (Super, ex-Max)** | ✓ Video Call with Lily (avatar video), tap-to-speak; guided "Falstaff" calls for beginners | Lily opens on a topic tied to your last lesson, then free | Transcript with inline comments after the call; no pronunciation scoring | Partial: Practice Hub + course mistakes, not generated from the call | ✓ Lily remembers earlier calls | ✗ (course word list only) | ✗ | Yes, but not Video Call | Super ~$13/mo; Max was ~$30/mo, now retired [1][5][58] | Calls auto-end after a few turns; gets cut off mid-sentence; repetitive persona [5][6][25] |
| **TalkPal** | ✓ Call Mode (audio), chat, roleplay, characters, debates, photo mode | Learner picks a mode; AI keeps turns going | Reactive grammar corrections; pronunciation "score" claimed | Partial: Word/Sentence/Dialogue modes | ✗ / undocumented | Partial: Word Mode, vocab lists | ✓ Amharic, Oromo, Somali (claimed) [19][20] | ✓ 10 min/day | $19.99/mo; $119.99/yr; in-app $59.99 first year [18][26] | Robotic voices, shallow at B1+, aggressive upsell pop-ups, asked to rate on day 1 [26][27] |
| **Loora** | ✓ voice call, single tutor persona | AI drives with a daily lesson | Gentle correction; "judgment-free" positioning | Partial: daily lesson only | Partial | ✗ | ✗ | 1 lesson/day (~10 min), 24h lockout | ~$119.99/yr [28] | Aggressive paywall; one persona; no accent choice [28] |
| **Univerbal** (ex-LangAI) | ✓ voice + text, scenario/quest based | Learner picks a real-life scenario | Real-time correction after each message | ✓ custom scenarios/quests | Partial | Partial | ✗ | Limited chats | ~$19.99/mo, $120/yr (prior teardown; not re-verified) [29][58] | Breadth over depth; feedback thinner than Langua |
| **Gliglish** | ✓ voice chat, "retry this turn" | Learner | Correction with retry loop | ✗ | ✗ | Partial (translation) | ✗ | 10 min/day | ~$29/mo (prior teardown) [58] | Expensive for a single mode |
| **Pimsleur Voice Coach / AI convo** | ✓ word-level voice coach + short AI conversation | App drives (audio lesson logic) | Immediate word score; AI convo feedback after | ✗ | ✗ | ✗ | ✗ | 7-day trial (select markets) | $20.95/mo all-access; $164.95/yr [30] | Deliberately mispronounced word still scored 100%; conversations short, end on their own [30] |
| **Rosetta Stone Sapphire** | ✗ typed Chat Missions; TruAccent word scoring | App drives | Green inline corrections in text | ✗ | ✗ | Partial: 500+ flashcard sets | ✗ | 7-day trial; first lesson free | $19.99/mo; $159/yr [31][32] | "No open-ended spoken conversation"; grammar minimal [31] |
| **Memrise** | Partial: MemBot/AI Buddies are chat-first, voice input | Learner picks a Buddy | Reactive; Conjugation Buddy made errors in test | Partial: Grammar/Conjugation/Role-play Buddies | ✗ | Partial: My Words + SRS | ✗ | 1 speaking session/day; 50 review words/day | $24.99/mo; $61.99/yr [33][34] | UI confusion; AI pushed hard; wrong-answer marking; billing complaints [33][34] |
| **Babbel / Babbel Speak** | Partial: scripted speak-back; Babbel Speak scenarios | App drives | Scripted | ✗ | ✗ | ✗ | ✗ | First lesson free | $8.95–17.95/mo | No Korean at all; scripted rather than conversational [35] |
| **Langua** (LanguaTalk) | ✓ best-in-class call mode; **full-duplex since Oct 2026**; can search web mid-call | Learner, or scenario/debate/grammar mode | 5 modes: subtle / every error / end-of-call; post-call report (text + audio) | Partial: grammar drills, AI stories from saved words | ✓ optional long-term facts | ✓ long-press or **say "save that"**; SRS flashcards | ✗ | Short free chat, no card | $19.99/mo or $149.99/yr (30 min call/day); Unlimited $29.99/$199.99 [9][10][13][36] | Bugs/UI "should be in beta"; AI too complex for beginners; currency-pricing complaint [36][37] |
| **Seyo (TTMIK)** | ✓ Seyo Call (topic-based call-style), Scenario Chat | Learner picks topic; structured path drives | Instant pronunciation + grammar + accuracy report | Partial: scenario chat + review | Partial: level check, reports | Partial: phrase review | ✗ | 7-day trial (card required) | IAP; not published on site [38] | 4.2★/182 ratings; early product, small catalog [38] |
| **Teuida** | ✓ POV scene, repeat-after-actor, ASR | App drives (scripted) | Immediate ASR accept/reject | ✗ | ✗ | ✗ | ✗ | Limited free | ~$14.90/mo [39] | ASR false negatives "demoralizing"; short content [39][40] |
| **HanDa** | ✓ chat/voice with 4 AI teachers | Learner, inside 300 roleplays | Four styles: recast / rule-naming / casual slang / explicit drill | ✓ recurring mistakes become next day's practice | ✓ | ✓ 1,798 words, 720 patterns as reference | ✗ | None | $10/mo; $49.99/6mo [11] | New, no free tier, phone-only (vendor-stated) [11] |
| **ChatGPT voice / Gemini Live** | ✓ full-duplex, free-form | Learner must prompt/steer | On request only ("correct me as I go") | ✗ (you must ask) | Partial (chat memory, not a learner model) | ✗ | ✓ can converse; quality unverified | ChatGPT free limited; Gemini Live free tier | $20/mo Plus [16][41] | No curriculum, no error ledger, no drills, no progress proof [16][41] |
| **italki / Preply** | ✓ human video | Human tutor | In-the-moment + homework | Human | ✓ (the tutor) | ✗ | ✓ italki: 29 Amharic tutors, $5–15/hr [42] | Trial lesson | Korean $8–30/hr; Preply $15–50/hr [43][44] | Cost, scheduling, quality variance |

### 1.2 Product notes that matter for Kiku

**Speak is the most important competitor, and it just moved onto Kiku's turf.**
- **AI Tutor Call** launched 20 Oct 2026: no topic list, open-ended, hands-free, "feedback during and after the call", "builds on sessions over time", mistakes become practice lessons, average **8–10 minutes**, learners speak **2× more** than anywhere else in Speak. Available to **English and Spanish Premium Plus** learners; Premium gets one trial call [7]. Korean is *not* in the call rollout yet — only English/Spanish.
- **Tutor Lessons** exist for Korean (Elementary/Intermediate), and **Tutor Lesson v2 beta started with Korean Elementary**: free-form back-and-forth, "can you say that more slowly?", "give me a hint", background mode [12]. So Speak's Korean teacher is real but gated to Elementary+; true beginners get the scripted course.
- **The mistake pipeline is explicit**: Targeted Practice from course mistakes; Takeaways from Free Talk/Roleplay; Vocab Interest; Teach New Vocab; Vocab Skill Errors from low proficiency + misuse patterns. Premium = 3 Made For You lessons/day; Plus = unlimited + study plan + frequent-mistake targeting [8][22].
- Weaknesses to attack: no permanent free tier; pronunciation coach is English-only; feedback is badges ("Perfect/Good") not diagnosis; ASR failures break the loop; no personal dictionary — Takeaways are lesson-shaped, not a library the learner owns [8][11][22][24].

**Duolingo's strategic move is the single biggest pricing signal of 2026.** Max is gone; unlimited Video Call is being given to all Super subscribers by end-2026; Max individuals migrate to Super Family at the same price; Max is now a small share of paid subscribers and bookings [1][2]. Two caveats: (a) Video Call's current help page lists only English, French, Spanish, Italian, German, Portuguese — **Korean is not listed**, though Korean was supported at launch; verify in-app before citing Korean Video Call as live [3][4]; (b) the call design caps length with a hidden "Closer" and no pronunciation scoring, which users experience as abrupt endings [5][6].

**Langua is the mechanic leader, not the scale leader.** Its Oct 2026 call mode hears voice directly (not waiting for transcription), tolerates barge-in, searches the web mid-call, admits uncertainty ("déjame revisar eso para no inventar"), and saves phrases **by voice** into SRS flashcards with the original context [9][13]. Correction is a three-way setting; post-call you get a written + audio report. It has ~30k active learners and 23 languages [36]. Its weakness is beginner structure: reviewers say the menu of modes does not tell a beginner what to learn first, and the AI sometimes speaks above level [36][37]. That is exactly the gap a curated Korean path fills.

**Correction style is now a product surface.** HanDa's four teachers (recast / rule-naming / casual / explicit drill) and Praktika's soft/balanced/strict show the market converging on "same engine, different pedagogy" [11][14]. Most products still default to *interrupt-and-correct*, which research says is the wrong default: recasts alone produce g≈0.70, and feedback content matters far more than timing (timing g≈0.03 in CAL) [45]. Kiku should default to recast-in-flow + explicit debrief, cap fixes at 2–3, and expose intensity.

**Nobody has a real personal dictionary.** The closest are Langua's save-any-word-with-context + SRS, Memrise's My Words, LingQ's known-word counter, and Migaku's mining. Speak's Takeaways are generated lessons, not a learner-owned lexicon. This is an open wedge, and Kiku already has the primitives (`Item`, `ReviewCard`, `Phrase`) to own it.

### 1.3 Verbatim complaints (what to design against)

| Quote | Product | Source |
|---|---|---|
| "In the video calls with Lily I often get cut off while responding to her." | Duolingo | Reddit [25] |
| "Sometimes her sentences are not audible at all… The comments give advice on pronunciation and grammar. Many times they are not helpful." | Duolingo | Blog review [6] |
| "A visibly nonsensical transcript was once accepted as complete." | Speak | Copycat review [23] |
| "The amount of breaking bugs and minor UI issues I experienced means this should be in beta still." | Langua | Trustpilot [37] |
| "This App does not encourage beginners or even students with limited knowledge." | Langua | Trustpilot [37] |
| "I even deliberately pronounced a word slightly off and still got a 100% score." | Pimsleur Voice Coach | Lingtuitive [30] |
| "Content remains shallow even at advanced levels, grammar is addressed only reactively, and the feedback system doesn't give you the detailed, actionable guidance you need." | TalkPal | LanguaTalk review [26] |
| "It never captured what I said… demoralizing." | Teuida | Play Store, via 04 teardown [58] |

The pattern: **turn-taking failures, ASR false negatives, generic feedback, and beginner-hostile pacing** — not "the AI isn't smart enough." These are engineering and UX problems, which is good news for a solo dev.

---

## 2. Ethiopian / African language coverage (Amharic, Oromo, Tigrinya, Somali)

### 2.1 Who actually supports what

| Product | Amharic | Tigrinya | Oromo | Somali | What it actually is | Price |
|---|---|---|---|---|---|---|
| **Duolingo** | ✗ never offered | ✗ | ✗ | ✗ | No course, no published roadmap [46][47] | — |
| **TalkPal** | ✓ claimed | ✗ | ✓ claimed | ✓ claimed | LLM chat/call in 130+ languages; generic template page; no Fidel-aware feedback, no native validation disclosed [19][20] | $19.99/mo |
| **uTalk** | ✓ | ✓ | ✓ | ✓ | Phrasebook + games, native recordings; no grammar, no script course [21][48] | $7.99/mo; $49.99/yr ($4.17/mo) |
| **Ling** | ✓ | ✗ (not found) | ✗ | ✓ | Gamified lessons + dialogues, 70–82 languages; not built by Ethiopian speakers [49] | $16.99/mo; $89.99/yr |
| **Mango Languages** | ✗ (not in current 70+ index) | ✗ | ✗ | ✗ (only English *for* Somali speakers) | Conversation-first courses, strong library distribution. Third-party guides still describe a Mango Amharic course — treat as retired/absent, verify in-app [50] | ~$8–20/mo retail; often free via libraries |
| **Selam** | ✓ | ✓ (now shipping) | ✗ | ✗ | Native-built: 22 units, 242 words/phrases, 68 lessons, interactive Fidel trainer with vowel orders, cultural notes; first unit free; 4.8★ [46][51] | IAP (not published) |
| **50Languages** | ✓ | △ | △ | △ | 100 free audio lessons, phrasebook-level; no feedback [52] | Free / cheap |
| **Bluebird** | △ (164 languages) | △ | △ | △ | Audio-centric, bilingual subtitles; coverage unverified per language [17] | subscription |
| **Drops** | △ | ✗ | ✗ | ✗ | 5-min visual vocabulary; script-light, no grammar | ~$13/mo |
| **italki** | ✓ 29 tutors | △ | △ | △ | Human 1:1, $5–15/hr typical | $5–30/hr [42] |
| **ChatGPT / Gemini / YouTube** | ✓ (quality varies) | ✓ | ✓ | ✓ | Free-form conversation, no curriculum, no script feedback, no error ledger | $0–20/mo [41] |

### 2.2 Assessment

- **Duolingo does not have Amharic and never has.** This is confirmed by both Duolingo-adjacent coverage and every Amharic-app guide; there is no published roadmap [46][47]. Treat "Duolingo will add Amharic" as folklore.
- **The market is phrasebooks plus one native-built course.** uTalk is the broadest (four Ethiopian languages, native audio, $4/mo annual) but is a phrasebook. Selam is the only structured, native-authored course — and it is *small* (242 items) and self-admittedly early [46][51].
- **TalkPal is the only realtime AI claim.** It lists Amharic, Oromo and Somali, and its Amharic landing page exists [19][20]. But the page is generic marketing copy; nothing documents a Fidel-aware pronunciation model, vowel-order handling, ejective consonants, or native-rated output. △ Expect LLM-quality Amharic with English-shaped pedagogy, hallucinated spelling, and weak ASR — i.e. exactly the failure mode Kiku's grounding layer is designed to prevent. **There is no verified, credible realtime Amharic tutor in Nov 2026.**
- **The demand is asymmetric.** The visible 2026 AI activity is *English for Ethiopians* (e.g. Amiora AI, launched at Web Summit Lisbon Nov 2026; coverage unverified, and the demo is framed around a free certified English course) [53]. Amharic-for-outsiders demand is mostly diaspora heritage: family conversation, respect registers, Fidel literacy. That is a real but narrow buyer, and the buyer is not the same person as the Korean learner.
- **The de facto realtime Amharic partner today is a general assistant, not a language product.** Gemini Live's native audio lists Amharic, and ChatGPT voice can hold a basic conversation [41]; neither has a curriculum, an error ledger, script-aware feedback, or pronunciation scoring. That is the honest competitive bar: "better than a free chatbot" is a low bar, but clearing it requires Fidel-level data work.
- **Script is the gate.** Amharic is an abugida with ~200+ character variants and seven vowel orders; apps that collapse ሰ/ሴ to "se" teach wrong pronunciation permanently [46]. Any credible product must teach Fidel from day one and score at the character/vowel-order level. That is a 6–12 month data project for a solo dev — not a language-pack switch.
- **△ Recommendation:** do **not** add Amharic to Kiku in 2026. Instead, treat it as a *second product* or a licensing/partnership play once the Korean engine (grounded generation + phoneme scoring + term library) is proven. If the owner wants a low-cost probe: publish a free Fidel trainer + 50 diaspora-family phrases, measure waitlist conversion, and only then build the teacher. The reusable asset is the engine, not the content.

---

## 3. Mechanics deep-dive: how the best loops actually work

### 3.1 Speak — "course rail + call + takeaways"

1. **Onboarding.** Pick target language, native language, goal, level. Korean course only for English speakers [54].
2. **Placement.** Level selector (Beginner/Elementary/Intermediate); no long adaptive test. Tutor Lessons unlock at Elementary+ [12].
3. **First session.** Video lesson (2–5 min) teaches phrases → speaking drills → "Apply" conversation. The learner speaks from the first minute; no blank-page chat [24].
4. **Who decides next.** The course path decides; the AI adapts within the lesson. Open topics only in Free Talk / AI Tutor Call [7].
5. **Errors → review.** Course mistakes → Targeted Practice; Free Talk/Roleplay mistakes → Takeaways (end-of-lesson screen) and Made For You lessons; low-proficiency vocab + misuse patterns → Vocab Skill Errors. Smart Review reschedules course material [8][22].
6. **Dictionary.** No personal dictionary. "Takeaways" are generated lessons; vocabulary is course-owned.
7. **Proof.** Path progress + level; no CEFR certificate; no before/after audio.
8. **Retention.** Daily path, streak, "Made For You" novelty, study plan (Plus). The 8–10 min call is the new habit unit [7].
9. **UI patterns worth copying.** (a) End-of-lesson "Takeaways" card with 2–3 fixes; (b) "Example / You" A-B audio comparison; (c) call scheduling with a notification ("your tutor will call at 7pm"); (d) hands-free mode with live activity; (e) visible level, not a score.

### 3.2 Duolingo — "habit first, conversation as a reward"

1. **Onboarding.** Goal + daily time; no placement in most courses.
2. **First session.** Tap-based lesson; speaking is one exercise type.
3. **Who decides.** The path. Video Call is a node/side quest, opened by Lily on a topic from your last lesson [4][6].
4. **Errors → review.** Practice Hub, mistakes review, Explain My Answer (free to all since early 2026) [5].
5. **Call mechanics.** Lily avatar video, tap-to-speak to signal turn end, XP counter during call, hidden "Closer" caps length, transcript after with inline comments (often generic or unhelpful per reviewers) [5][6].
6. **Memory.** Lily references earlier calls and prior lesson vocabulary [4][6].
7. **Dictionary.** Course vocabulary list; no capture from conversation.
8. **Proof.** Streak, XP, league, path position. Not ability.
9. **Steal / avoid.** Steal: the 3-minute contract and "speaking inside an existing habit". Avoid: capped calls, single persona, no pronunciation feedback, XP as progress.

### 3.3 Langua — "call + capture + review" (best mechanic set)

1. **Onboarding.** Pick language, level, tutor voice/accent (5–6 voices even in smaller languages; 20+ Spanish dialects) [9].
2. **First session.** Free short chat, no card; then choose guided course, roleplay, debate, grammar, vocab game, or custom scenario [9][36].
3. **Who decides.** The learner, mostly. "My Path" brings back saved words and targets grammar you keep getting wrong; a 40-lesson A1–A2 course exists but is secondary [9][36].
4. **Correction.** Three live modes (subtle / every error / after the call) + written and audio report [9][13].
5. **Dictionary (the model to copy).** Long-press any word → save with the original sentence as context; or say **"save that"** out loud mid-call; saved items become SRS flashcards; AI can generate sentences/stories containing your saved words; post-call flashcard suggestions [9][13].
6. **Memory.** Optional long-term facts ("you're preparing for a meeting"), explicitly toggleable [9].
7. **Proof.** Saved-word count, reports, before/after recordings; no formal CEFR.
8. **Retention.** Daily conversation, streak, novelty of modes, voice quality.
9. **Weakness to exploit.** No beginner spine; AI speaks above level; bugs; pricing confusion [36][37].

### 3.4 HanDa — closest Korean-specific analogue

- Four AI teachers with **different correction methods** (recast / rule-naming / casual slang / explicit drill), 300 role-plays with **speech levels enforced**, 159 readings mapped to TOPIK 1–6, 720 grammar patterns, 1,798 words, pronunciation scored **sound by sound**, and **recurring mistakes become the next day's practice** [11].
- Vendor-authored, so treat feature claims as marketing; but the *design* is the most Kiku-shaped in the market and confirms the four levers: correction style, register enforcement, TOPIK mapping, error carry-forward.
- Gaps it leaves: no free tier, phone-only, no personal dictionary, no workplace track, English-centric explanation languages (7, but no proof of quality).

### 3.5 Cross-product UI patterns worth stealing

| Pattern | Who does it well | Why it works | Kiku implementation |
|---|---|---|---|
| **Live transcript with inline corrections** | Duolingo, Langua | Lets the learner *see* what the ASR heard and revisit fixes without breaking flow | After each call, render turns with diff-style highlights; tap a highlight → one-line "why" |
| **Tap-a-word-to-save (with sentence context)** | Langua, LingQ | Capture happens at the moment of noticing; context makes the card retrievable | Bottom sheet: word, romanization, register, audio, the sentence you heard, "Save to My Korean" |
| **Voice-save** | Langua | Removes the phone-fumble mid-conversation | "Kiku, save that" → confirmation chip, undo |
| **End-of-session drill cards (2–3, not 10)** | Speak Takeaways, HanDa | Converts a pleasant chat into a measurable change | "3 things to fix" → 90-second drill each → schedule cards |
| **Pronunciation strip per syllable** | HanDa, Pimsleur (syllable-backwards) | Tells you *what* to fix, not a fake number | Color the syllable strip; tap → minimal-pair drill; re-record |
| **"Mistakes you fixed" recap** | none at scale (△) | Proof of change is the retention lever | Weekly: errors that stopped recurring, with before/after audio |
| **Can-do artifact** | Kiku already has `CanDoArtifact` | A durable, shareable proof | Auto-generate after a scene: "I can refuse politely" + 15s audio |
| **Correction dial** | Langua, Praktika, HanDa | Anxiety management | 3 settings, persisted per learner, shown in debrief |
| **Scheduled call notification** | Speak | Creates an appointment without a human | "Tomorrow 7:00 — ordering at a pharmacy" with one-tap reschedule |

---

## 4. Human tutor marketplaces (the benchmark Kiku is judged against)

| | italki | Preply |
|---|---|---|
| Korean price | Community $8–10/hr; professional $15–30+/hr [43] | $14–40/hr; clusters $15–50 [44] |
| Amharic price | 29 tutors; $5–15/hr typical ($5, $11, $15 on page 1) [42] | Thin/absent |
| Session length | 30/45/60 min; 30-min trials common | 50 min standard; trial at tutor rate |
| Model | Pay per lesson, no subscription | Subscription packages, 1–5 hrs/week |
| AI | italki Plus AI tools, classroom | Lesson Insights, Daily Exercises, Scenario Practice (beta) [55] |
| What learners pay for | Correction + accountability + a person who notices | Structure + recurring slot + progress nudges |

**What learners say AI lacks.** The most consistent formulation, from a long-term Langua reviewer: *"A real person gives you connection, accountability and a kind of feedback AI can't"* [9]. Reddit and review threads add: someone waiting for you, someone who remembers your life, and the mild social cost of not showing up.

**Behaviors an AI can credibly replicate:**
1. **Wait time.** Tunable VAD (1.5–4s) with a visible "I'm listening" pulse. This alone fixes the "it talks over me" complaint [25].
2. **Recasts.** Repeat the correct form in the next turn without stopping; g≈0.70 [45].
3. **Scaffolded hints.** "Word bank → sentence starter → hint → translation → free production", fading as accuracy rises [45].
4. **Bounded accountability.** A scheduled 7-minute call, a named plan, a weekly recap, and a "you missed yesterday — here's the 3-minute version" (no shame).
5. **Consistent patience and zero social risk.** The real advantage for anxious learners [36].
6. **Perfect recall of errors** — better than most humans.

**Behaviors it cannot replicate (don't pretend):**
1. **Genuine relationship/trust** and the motivation that comes from not wanting to disappoint a person.
2. **Cultural insider judgment** — when a phrase is technically right but rude/odd for this specific person and situation.
3. **Affect reading** — distinguishing "confused" from "bored" from "embarrassed" reliably.
4. **High-stakes register/nuance** (workplace hierarchy, age, in-law speech) without a human check.
5. **Improvisation with real stakes** (a real doctor's appointment, a real meeting).

**Positioning implication.** Sell the AI as *"the practice you do between human conversations"*, and make export to a human easy (a one-page "what we worked on / what to ask your tutor" summary). This is credible, reduces the "AI vs $20 tutor" value comparison, and is a differentiator no competitor ships well.

---

## 5. Gap analysis

### 5.1 Matrix

| Product | Real-time voice | On-demand drills | Cross-session memory | Personal dictionary | Amharic | Price/mo |
|---|---|---|---|---|---|---|
| Speak | ✓ | ✓ | ✓ | ✗ (Takeaways) | ✗ | $17.99 / $39.99 |
| Duolingo Super | ✓ (Korean unlisted) | Partial | ✓ | ✗ | ✗ | ~$13 |
| Langua | ✓ (full-duplex) | Partial | ✓ | ✓ | ✗ | $19.99 / $29.99 |
| TalkPal | ✓ | Partial | ✗ | Partial | ✓ (claimed) | $19.99 |
| Praktika | ✓ (avatar) | ✓ | Partial | ✗ | ✗ | ~$10 |
| Loora | ✓ | Partial | Partial | ✗ | ✗ | ~$10 |
| Univerbal | ✓ | ✓ | Partial | Partial | ✗ | $19.99 |
| Gliglish | ✓ | ✗ | ✗ | Partial | ✗ | ~$29 |
| Pimsleur | ✓ | ✗ | ✗ | ✗ | ✗ | $20.95 |
| Rosetta Stone | ✗ | Partial | ✗ | Partial | ✗ | $19.99 |
| Memrise | Partial | Partial | ✗ | Partial | ✗ | $24.99 |
| Seyo | ✓ | Partial | Partial | Partial | ✗ | IAP |
| Teuida | ✓ | ✗ | ✗ | ✗ | ✗ | $14.90 |
| HanDa | ✓ | ✓ | ✓ | ✗ | ✗ | $10 |
| ChatGPT/Gemini | ✓ | ✗ (on ask) | Partial | ✗ | ✓ | $0–20 |
| italki/Preply | ✓ human | Human | ✓ | ✗ | ✓ italki | $8–50/hr |
| **Kiku (today)** | ✗ | Partial (scenes/SRS) | ✓ (FSRS + events) | Partial (`Phrase` library) | ✗ | — |
| **Kiku (target)** | ✓ | ✓ | ✓ | ✓ | ✗ (deliberate) | $12 / $24 |

### 5.2 The opening

The market is saturated on **"AI you can talk to"** and thin on **"AI that changes what you can do, and proves it."** Specifically:

1. **A learner-owned dictionary with context and SRS is missing everywhere.** Langua is closest; Speak and Duolingo have none. Kiku's existing `Item` + `ReviewCard` + `Phrase` make this cheap.
2. **Nobody closes the loop inside one session**: talk → 2–3 fixes → 90-second drill → cards → reappearance next session. Speak does fragments of this across screens; HanDa does it across days; Langua leaves the drill to you.
3. **Korean register (존댓말/반말) is treated as content, not as a runtime constraint.** Only HanDa enforces speech levels; nobody *detects* a register error and drills it.
4. **Proof is weak industry-wide.** Streaks and XP measure attendance. Before/after audio + can-do artifacts + "mistakes you fixed" is rare and cheap.
5. **Beginner + anxious learner is underserved by the AI-first products.** Speak gates tutor lessons to Elementary+; Langua admits the AI talks above beginner level. A beginner-safe teacher that never blocks progress is a real wedge.
6. **Ethiopian languages: no credible realtime tutor.** Real gap, wrong first market for a solo dev (content + ASR + script data).

### 5.3 Seven differentiators, ranked by impact/effort

| Rank | Differentiator | Effort | Impact | The specific UX mechanic |
|---|---|---|---|---|
| 1 | **One-session closed loop** | S–M | ★★★★★ | End call → "3 things to fix" (not a score) → each opens a 90-second generated drill using *your* sentence → "Add to review" creates FSRS cards with the sentence as the prompt. Next call opens with one of them. |
| 2 | **"My Korean" term library** | M | ★★★★★ | Tap any word in transcript/subtitle → sheet (word, romanization, register, audio, source sentence, date) → save. Voice: "Kiku, save that." Review uses your sentence, not a dictionary example. Group by theme/register; export CSV/Anki. |
| 3 | **Plan-driven teacher (visible syllabus)** | M | ★★★★☆ | Card at call start: "Today: refuse politely (3 ways) — you'll use -기 싫어요." Progress chips; AI may not drift; call ends with a can-do check. Prevents the "random café chat" failure. |
| 4 | **Register guard (존댓말/반말)** | M | ★★★★☆ | Toggle "polite / casual" per scene; every AI line badged; if learner uses the wrong level, one-line fix + a 3-rep drill; recurring register errors become a "register" skill in the progress map. |
| 5 | **Proof artifacts + pronunciation heatmap** | S–M | ★★★★☆ | Syllable strip colored by error (not a number) → tap → minimal-pair drill; auto can-do artifact with 15s before/after audio; weekly "mistakes you fixed" recap. Reuse `CanDoArtifact`, `SpeechAttempt`. |
| 6 | **Correction dial + debrief discipline** | S | ★★★☆☆ | 3 settings (gentle / balanced / strict); cap 2–3 fixes per session; recast in flow, explicit in debrief; "why" is one sentence, not a grammar lecture. |
| 7 | **Bounded accountability** | S | ★★★☆☆ | One scheduled 7-minute call/day with a named topic; user-owned reminder; missed call → auto-offer a 3-minute version, never a guilt message. Optional "share with your tutor" summary. |

**Top 5 for the final answer:** #1, #2, #3/#4 (treat register as part of the plan), #5. I.e. closed loop, term library, plan+register, proof. #6 and #7 are cheap polish.

### 5.4 What NOT to build

| Don't build | Why (evidence) |
|---|---|
| **Video avatars / lip-sync personas** | Expensive, uncanny, and Duolingo/Praktika already own the novelty; users complain about one repetitive persona, not about lack of a face [5][6][14]. Voice + transcript is enough. |
| **Social feed, DMs, leaderboards** | Safety and moderation cost; HelloTalk/Tandem harassment is a known failure; solo dev cannot moderate [58]. |
| **6,000-word starter decks** | Breadth without context; Anki/LingQ/Memrise own it; Kiku's thesis is memory from *your* output [58]. |
| **Open-ended "talk about anything" as the primary mode** | It is the commodity; reviewers say it drifts, asks a question every turn, and gives shallow feedback [24][36]. Keep it as a paid unlock, not the product. |
| **A single pronunciation percentage** | Discredited by the best products; it cannot tell the learner what to fix [9][11]. |
| **Streak repair by payment / annual-only / trial-to-annual traps** | Trust is the brand; Langua's currency and trial complaints show how fast pricing erodes goodwill [37]. |
| **Multi-language expansion before Korean depth** | Every multi-language app is shallower in Korean; Korean-only depth is the defensible position [11]. |
| **Amharic in 2026** | Different buyer, different script/ASR data, 6–12 month content project; revisit as a second product (§2). |

### 5.5 Pricing and packaging for a solo dev

**Cost reality.** Managed realtime voice runs ~$0.06–0.30/min; a cascaded ASR + small LLM + cached/neural TTS pipeline can reach ~$0.01–0.05/min [58]. Duolingo's own number — under $0.01 per call after optimization — shows what is possible at scale, not for a solo dev [1][2]. Budget **$0.03–0.06 per conversation-minute** and design caps around it. Note that token-billed speech-to-speech providers re-send audio history every turn, so naive per-minute estimates understate a 10-minute session by 2–4×; the stack-level model is in `07-realtime-teacher-stack.md`.

| Tier | Price | Limits | Why |
|---|---|---|---|
| **Free** | $0 | Full Hangul + Sound Gym; 5 min teacher/day (one call); 1 drill set/day; **unlimited term capture + SRS**; 3 scenes/week | The free tier must teach and must create the memory asset. Capping the dictionary would kill the moat. |
| **Kiku Core** | **$11.99/mo or $79/yr** (≈$6.58/mo) | 20 min teacher/day; unlimited generated drills; full pronunciation detail; weekly recap; all scenes | Undercuts Speak ($17.99) and Langua ($19.99) while matching Duolingo Super (~$13). |
| **Kiku Teacher** | **$24.99/mo or $169/yr** | 45–60 min/day; scheduled calls; personalized study plan; TOPIK/workplace track; "share with your tutor" export | Anchors against a $20–30 human hour without pretending to replace it. |
| Add-ons | $8–12 one-time | TOPIK mock pack; workplace phrase pack | Low-risk revenue, no voice cost. |

**Rules.** Monthly available; annual ~35–45% off; PPP pricing for K-pop-heavy markets; **degrade, don't hard-stop** at the minute cap (switch to text drill + review, offer a 60-second voice top-up); no auto-selected 24-month plan (TalkPal's default-plan complaint is a cautionary tale [26]); show minutes remaining, not "credits".

---

## 6. Metrics: what the market implies, and what to instrument

### 6.1 Benchmarks

| Metric | Value | Source / status |
|---|---|---|
| Duolingo DAU / MAU | 58.7M / 140.6M ≈ **42%** (Q2 2026); 64.9M DAU, 13.1M paid (Q3 2026) | ✓ [1][56] |
| Duolingo paid conversion | ~**9% of MAU**, ~**20% of DAU** (13.1M / 140.6M; 13.1M / 64.9M) | ✓ derived [1][56] |
| Duolingo Video Call cost | ~$0.30 → **<$0.01 per call** | ✓/reported [2][61] |
| Duolingo Video Call usage | words spoken per user **more than doubled** YoY | ~ [16] (citing Q1 2026 letter) |
| Speak scale | 15M+ downloads; 4.8★ / ~61k US ratings; **AI Tutor Call sessions 8–10 min**, 2× speaking | ✓/reported [8][9][23] |
| Langua scale | ~**30k active** learners; Standard cap 30 min call/day | ~ [36][60] |
| Education retention | D1 ~14–15%, D7 ~6%, D30 ~2–3%; cross-category 25/11–13/5–7% | ~ [57] |
| Implied target for Kiku teacher | 6–10 min median session; ≥50% learner talk time; ≥70% first-session completion | △ from above |

### 6.2 What these numbers mean

- **Voice volume is not the metric; return is.** A 30-min/day cap at Langua is described by a daily user as "more than enough" [36]. Kiku should optimize for *sessions per week* and *errors fixed*, not minutes.
- **8–10 minutes is the proven unit** for a call (Speak). Kiku's 7-minute default is right; offer 3-minute "commute" and 15-minute "deep" variants.
- **Conversion happens after the first visible win,** not after a trial countdown. Instrument the win, not the paywall.

### 6.3 Instrumentation plan (fits existing `Event` + `record_event`)

Kiku already logs append-only events and has `ReviewCard`, `ReviewLog`, `CanDoArtifact`, `SceneSession.transcript`, `SpeechAttempt` (`app/learning/analytics.py`, `app/models.py`). Add these events; do not build a new warehouse.

| Event | Properties | Question it answers |
|---|---|---|
| `teacher_session_start` | plan_id, scene_slug, mode, level | Who starts, from where? |
| `teacher_first_turn_latency` | ms | Is the tutor too slow to feel real? |
| `teacher_turn` | role, asr_confidence, duration_ms, barge_in | Talk ratio, ASR failure rate, interruption behavior |
| `teacher_correction` | type (recast/explicit/register), severity, turn_index | Are we over-correcting? Which errors dominate? |
| `teacher_hint` | rung (word bank/starter/hint/translation) | Is scaffolding used and does it work? |
| `teacher_session_end` | turns, minutes, learner_talk_pct, completed, reason (user/plan/error) | First-session completion, drop-off point |
| `drill_generated` | source_error_id, skill, items | Drills per session (target 2–3) |
| `drill_completed` | accuracy, duration | Do drills actually get done? |
| `term_saved` | surface, source (tap/voice/import), has_context | Terms saved per session (target 2–3) |
| `term_reused` | term_id, surface | Does the library feed conversation/review? |
| `register_error` | expected_level, used_level | Korean-specific progress |
| `can_do_created` | scene_slug, label, has_audio | Proof artifacts per active learner |
| `weekly_recap_viewed` | errors_fixed_count | Is proof being seen? |

**Cohort definitions.** (a) teacher cohort = started ≥1 teacher session; (b) loop cohort = completed a session with ≥1 generated drill; (c) library cohort = saved ≥1 term. Compare D7/D30 and week-4 can-do creation across cohorts.

**Targets (first 90 days).** First-session completion ≥70%; median session 6–10 min; drills generated 2–3 per session; ≥60% of sessions produce ≥1 card; terms saved 2–3 per session; ≥40% of saved terms reappear in a later session or review; D7 teacher cohort ≥2× non-teacher; free→paid by day 7 ≥4%.

**Guardrail metrics.** ASR false-negative rate (<2% of turns require a retry that changes meaning); correction load (≤3 explicit fixes/session); time-to-first-spoken-word in onboarding (<90s); cost per session (<$0.35 at 8 min).

---

## 7. Implications for Kiku (concrete)

1. **Do not ship "AI chat". Ship a 7-minute lesson with a plan.** The chat screen is the commodity; the plan + debrief + cards are the product.
2. **Make the term library the retention surface, not a utility.** The blueprint's non-goal ("a dictionary or translator — useful utilities, not the product") is still right for a *generic* dictionary [59]. A **personal, contextual, SRS-backed term library** is the opposite: it is the memory made visible. Every saved term must carry the sentence, the source, the register, and its review state.
3. **Reuse the existing data model.** `Item(item_type="lexeme")` + `ReviewCard(skill="recognize"|"produce")` + `Phrase` for audio; add `source_type`, `source_id`, `context_sentence`, `register` to `Item` rather than a new table. `CanDoArtifact` already gives proof; add optional before/after audio.
4. **Default pedagogy:** recast in flow, explicit debrief, ≤3 fixes, correction dial. This is both evidence-based and the main differentiator from "interrupt every sentence" apps [45].
5. **Korean-specific moat:** register detection/enforcement, batchim/liaison feedback at the syllable level, and honorific drills for workplace learners. Multi-language competitors cannot cheaply copy this [11].
6. **Trust is a feature:** validate generated Korean, show uncertainty, and never invent a score. The market's #1 complaint is not "AI is dumb"; it is "AI confidently accepted/taught something wrong" [24][31].
7. **Distribution:** the wedge is not "learn Korean" (crowded) but "speak Korean without freezing, and prove you're improving" — the anxious beginner and the A2 plateau, with before/after audio as the shareable artifact.

---

## Sources

Accessed 13–23 Nov 2026 unless noted.

1. Duolingo Q3 2026 shareholder letter — https://investors.duolingo.com/static-files/e1ee336e-b024-486f-875c-afd722653067 (also SEC EX-99.2: https://www.sec.gov/Archives/edgar/data/1562088/000162828026069474/q3fy26duolingo9-30x26share.htm)
2. Duolingo Q3 2026 earnings call transcript (Video Call cost, 10× users, Max migration) — https://www.fool.com/earnings/call-transcripts/2026/11/04/duolingo-duol-q3-2026-earnings-call-transcript/
3. Duolingo Max help center (feature availability by language/platform) — https://www.duolingo.com/help/what-is-duolingo-max
4. Duolingo Max launch post (Korean Video Call support at launch) — https://blog.duolingo.com/duolingo-max/
5. PracticeMe, "Duolingo Max Review: Is Video Call Worth It?" (13 Jul 2026) — https://practiceme.app/vs/duolingo-max
6. The Owl and Me, "Review: Duolingo Max Video Calls" (10 Jan 2026) — https://theowlandme.blog/2026/01/10/review-duolingo-max-video-calls/
7. Speak blog, "Your tutor is one call away: introducing AI Tutor Call" (20 Oct 2026) — https://www.speak.com/blog/your-tutor-is-one-call-away-introducing-ai-tutor-call
8. Speak Help, "What are Made For You custom lessons?" (18 Dec 2025) — https://help.speak.com/en/articles/11565779-what-are-made-for-you-custom-lessons
9. Lingtuitive, "Langua Review: 2+ Years of Use" (Oct 2026) — https://lingtuitive.com/blog/langua-ai-tutor-review
10. Langua product overview — https://languatalk.com/ai-language-tutor
11. HanDa, "The Best AI Korean Tutor Apps in 2026" (12 Aug 2026, updated Oct 2026; vendor-authored) — https://handakorean.com/blog/best-ai-korean-tutor-apps
12. Speak Help, "What are Tutor Lessons?" (18 Dec 2025; v2 beta Korean) — https://help.speak.com/en/articles/11966855-what-are-tutor-lessons
13. Langua support, "See the latest updates on Langua" (call modes, flashcards, memory) — https://support.languatalk.com/article/152-see-the-latest-updates-on-langua
14. Praktika 4.0 product update — https://praktika.ai/blog/praktika-4-0
15. Copycat Cafe, "Langua Review 2026" (correction modes, pricing) — https://copycatcafe.com/blog/languatalk-review
16. Eppika, "10 Best AI Language Learning Apps in 2026" (2 Oct 2026) — https://eppika.com/en/blog/best-ai-language-learning-apps
17. Bubblegum, "Best Language Learning Apps in 2026" (long tail, Bluebird 164 languages) — https://bubblegum.la/blog/best-language-learning-apps
18. Copycat Cafe, "Talkpal Review 2026" (11 Nov 2026; pricing, upsells) — https://copycatcafe.com/blog/talkpal-review
19. TalkPal support, language list incl. Amharic/Oromo/Somali — https://talkpal.ai/support/how-many-languages-is-talkpal-ai-available-in/
20. TalkPal, "Learn Amharic with AI" — https://talkpal.ai/learn-amharic/
21. uTalk Oromo store page (Amharic, Tigrinya, Somali cross-sell) — https://utalk.com/store/oromo
22. Speak Help, "Premium vs Premium Plus" — https://help.speak.com/en/articles/5358417-what-s-the-difference-between-premium-and-premium-plus
23. Copycat Cafe, "Speak App Review 2026" (prices, ASR issues) — https://copycatcafe.com/blog/speak-app-review
24. SpeakShark, "Speak App Review 2026" (conversation-volume critique) — https://speakshark.com/blog/speak-app-review-2026
25. Reddit r/duolingo, "Recent and upcoming Duolingo updates" ("In the video calls with Lily I often get cut off while responding to her") — https://www.reddit.com/r/duolingo/comments/1niqy8y/recent_and_upcoming_duolingo_updates/
26. LanguaTalk, "TalkPal Review" (free tier, mode list) — https://languatalk.com/blog/talkpal-review/
27. Trustpilot, TalkPal — https://www.trustpilot.com/review/talkpal.ai
28. PracticeMe, "Loora AI Review 2026" (free tier, annual price) — https://practiceme.app/vs/loora
29. ICanLearn, "Univerbal Review (2026)" — https://www.icanlearn.com/univerbal/
30. Lingtuitive, "How to Use Pimsleur for Best Results" (2026; Voice Coach 100% on mispronunciation) — https://lingtuitive.com/blog/best-way-to-use-pimsleur
31. Copycat Cafe, "Rosetta Stone Review 2026" (11 Nov 2026; typed Chat Missions) — https://copycatcafe.com/blog/rosetta-stone-review
32. Forbes Advisor, "Rosetta Stone Review 2026" (prices, tutoring add-on) — https://www.forbes.com/advisor/education/student-resources/rosetta-stone-review/
33. Copycat Cafe, "Memrise Review 2026" (13 Nov 2026; free caps, prices) — https://copycatcafe.com/blog/memrise
34. Qlango, "Memrise Review 2026" (AI Buddies, billing complaints) — https://qlango.com/memrise-review/
35. PracticeMe, "Babbel Speak Review" — https://practiceme.app/vs/babbel-speak
36. Copycat Cafe, "Langua Review 2026" (beginner critique, pricing) — https://copycatcafe.com/blog/languatalk-review
37. Trustpilot, LanguaTalk (Nov 2026; bugs, currency, trial complaints) — https://www.trustpilot.com/review/languatalk.com
38. Seyo App Store listing (v1.2.4, 5 Nov 2026; Seyo Call, Scenario Chat, 4.2★/182) — https://apps.apple.com/us/app/seyokorean/id6657977758
39. Lingrow, "Teuida Review (2026)" (ASR failures) — https://lingrow.io/blog/teuida-review
40. Pulse/GrowthStock, "Not AI, But Person To Talk To: TEUIDA passes 6.3M downloads" — https://pulse.growthstock.app/teuida-1/
41. Medium, "ChatGPT Voice vs Gemini Live vs Speak vs Praktika" (2026) — https://medium.com/@thehumanmode/best-ai-language-learning-apps-in-2026-chatgpt-voice-vs-gemini-live-vs-speak-vs-praktika-d4ba80b68560
42. italki Amharic teachers (29 tutors; $5–15/hr examples) — https://www.italki.com/en/teachers/amharic
43. Preply, "Are Korean tutors worth it in 2026?" ($14–40/hr) — https://preply.com/en/blog/are-korean-tutors-worth-it/
44. italki vs Preply pricing 2026 — https://www.italki.com/en/blog/italki-vs-preply
45. Kiku, "Learning Science Brief" (`docs/research/02-learning-science.md`): recasts g≈0.70; feedback timing g≈0.03; scaffolding/85% success — internal synthesis of cited studies
46. Selam, "The Best Apps to Learn Amharic in 2026" (18 Aug 2026; Fidel/vowel orders, Duolingo absence; vendor-authored) — https://learnwithselam.com/best-amharic-apps
47. Ling, "No Amharic on Duolingo?" — https://ling-app.com/blog/no-amharic-on-duolingo/
48. uTalk Amharic plans ($7.99/mo; $49.99/yr) — https://utalk.com/plans/amharic
49. Ling Amharic course + pricing — https://ling-app.com/learn-language/amharic/ ; https://ling-app.com/pricing/
50. Mango Languages, available languages (no Amharic/Oromo/Tigrinya/Somali course in current index) — https://www.mangolanguages.com/available-languages
51. Selam download page (Amharic + Tigrinya) — https://learnwithselam.com/download
52. 50Languages Amharic — https://50languages.com/learn-amharic-in-10-minutes-a-day
53. Amiora AI at Web Summit Lisbon 2026 (coverage unverified) — https://www.facebook.com/eu4innovationeast/videos/learning-a-new-language-just-got-a-whole-lot-smarter-marcel-moraru-is-sharing-am/1082262748162739/
54. Speak Help, language availability — https://help.speak.com/en/articles/8880569-what-languages-can-i-learn-with-speak
55. Preply, "The future of language learning" (Lesson Insights, Daily Exercises, Scenario Practice) — https://preply.com/en/blog/the-future-of-language-learning/
56. Duolingo Q2 2026 DAU/MAU summary — https://lji.io/glossary/dau-mau-ratio ; https://okara.ai/blog/how-duolingo-grew
57. Phiture, retention benchmarks 2025–26 — https://phiture.com/mobilegrowthstack/managing-retention-rate-benchmarks-and-expectations/
58. Kiku, `docs/research/04-competitive-teardown.md` (prior teardown; prices and product profiles used where noted) — internal
59. Kiku, `docs/KIKU_BLUEPRINT.md` (non-goals, positioning) — internal
60. The Fabryk, "Langua Review 2026: My Verdict After Months of Daily Use" (30k+ active learners) — https://thefabryk.com/blog/langua-review
61. BigGo, "Duolingo Q3 2026 Earnings Call: Video Call costs plummet to under $0.01, Max sunset" (3 Nov 2026) — https://finance.biggo.com/news/US_DUOL_2026-11-03

**Confidence notes.** Duolingo's Max sunset, Speak's AI Tutor Call and Made For You mechanics, Langua's call/memory/dictionary mechanics, and the absence of Amharic on Duolingo are verified against primary or company sources. The "under $0.01 per Video Call" figure is a secondary summary of the Q3 2026 call; the $0.30 launch cost is quoted directly by the CEO [2][61]. Prices for Gliglish, Univerbal, and Praktika were not re-verified in Nov 2026 and are marked as carried from the prior teardown. Claims that TalkPal's Amharic is shallow, that Amharic ASR is weak, and that no credible realtime Amharic tutor exists are inference from the absence of documented capability, not from a benchmark; treat as hypotheses to test, not facts.
