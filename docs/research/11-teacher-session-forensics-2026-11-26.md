# 11 — Teacher session forensics, 26 November 2026

**Status:** Post-incident note · evidence from the local SQLite database.
**Question:** the live teacher "breaks after a while". What actually happens in a
session, and what did we change because of it?

## What the data showed

Seven sessions were stored on 26 November. The two that ran long enough to show
the failure are the useful ones.

### Session 7 — 72 seconds, 11 turns (8 learner, 3 tutor)

```
1  learner  سلام.
2  teacher  እንዴት ነው! የተለምዱበትን ስራ ደስ ይበላችሁ? በ        ← 32 chars, cut mid-word
3  learner  سلام.
4  teacher  ሰላም!በቀላሉ መግባሪያ ላይ በመራዳት እችላለሁ።
5  learner  De hene neg amsege nanalu.
6  teacher  እጅግ እባክህ፣ ያጠውለው የበቆሎና የገን         ← cut mid-word
7  learner  Ishi, amme segenni nalehu.
8  learner  Eshi, amasegina lahu.
9  learner  Eshi amasegi nalahu.
10 learner  ama seginna lahu.
11 learner  އަމަސްገንጠላሁ.                            ← Dhivehi script
```

Three separate faults in one minute of audio:

1. **Tutor replies cut mid-word** (25–32 Ethiopic characters). `max_output_tokens`
   was 200. Ethiopic tokenizes badly, so 200 tokens bought about five words and
   the response stopped. The learner heard a fragment, then nothing.
2. **Five learner turns with no tutor turn.** The learner was repeating one
   phrase. `interrupt_response: true` cancelled each reply while it was still
   being generated, so the repeats ate the answers.
3. **Transcription mislabelled the language** — one turn came back in Thaana
   script. Auto-detect had chosen Dhivehi for Amharic.

### Session 10 — 6.5 minutes, 49 turns

This one is about content quality, not plumbing. Sample tutor turns:

```
ሰላም! እባብን ያድርጉ፣ ምን መምረት እንደምን እናምር?
"hibako" ማለት ምን ነው? እርስዎ ተግባሩ ሊትከለሉኝ እባክዎን ይህንን እንዴ? I d
አማርኛ መጠቀም በሚያውቁኝ ነው? ስለ እናንተ አሳካችሁ በአንድ ሰከው ቃለብስ ማድረግ ትችላላችሁ።
```

Ungrammatical, mixes English mid-sentence, invents phrases, and drifts between
formal and familiar address. This is not a bug we can fix in code: the provider's
realtime model does not list Amharic (see `07` §1.2), and its transcription
endpoint rejects `am` outright. The ceiling is the model.

Learner transcripts are equally rough (`Hebako yidigîmû.`, `سلام۔`), which is
expected when auto-detect runs on a language the transcriber does not know.

## What we changed

| Fault | Fix |
|---|---|
| Amharic cut mid-word | Per-language output budget: Korean 600, Amharic 1200 (`TEACHER_MAX_OUTPUT_TOKENS=0` = per-language) |
| Repeats cancelling replies | `interrupt_response: false` by default (`TEACHER_INTERRUPT_RESPONSE`); benign "active response" errors are ignored |
| Fragmented learner turns | VAD tuned for learners: threshold 0.4, silence 900 ms (`TEACHER_VAD_*`) |
| Dhivehi / wrong script | Cannot pin `am` (provider rejects it); the coach hint now says learner turns are rough phonetic transcripts, and the UI says so too |
| Garbled Amharic | Prompt now forbids English inside Amharic sentences, anchors to deck phrases (ሰላም, አመሰግናለሁ, እባክህ/እባክሽ), and asks for repetition instead of translation |
| "Disconnected" with no recovery | Connection state and data-channel close both say what happened and reset to Start speaking; the session row is closed server-side on drop |
| Daily minutes exhausted by an old row | `expire_if_over_limit` charges the 15-minute cap, not wall-clock hours |
| No call time limit in the UI | `create_session` returns `expires_at` / `max_minutes`; the client ends the lesson at the cap and the page states it |
| Transcript not following new text | Stick-to-bottom scrolling on turns, live partials, and late translations, with a 48 px threshold so scrolling up is respected |
| Screen reader spam | `aria-live` moved off the transcript list to one `role="status"` announcer updated per finalized turn |
| Silent tool failures | Tools get an 8 s abort; only read-only tools retry (writes are never repeated); unexpected handler errors return a tool error instead of an HTML 500 |

## What is left, and why

- **Amharic voice quality.** Provider limitation. The code path is right; the
  model is weak. Adding a provider that lists Amharic (Gemini Live per `07`) is
  a product decision the repo's rules reserve for an explicit ask.
- **Session resume.** A dropped call starts a fresh session; resuming would need
  provider-side conversation state we do not have.
- **Latency metrics.** `latency_ms` is stored but never populated; measuring
  speech-end → first audio would be the next instrumentation step.
- **Semantic VAD.** A real candidate for hesitant learners, but `07` measured a
  4.5 s turn-end at default eagerness. It needs an A/B, not a blind switch.
