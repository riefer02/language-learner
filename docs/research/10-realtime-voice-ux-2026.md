# 10 — Real-time voice UX: turn taking, barge-in, and staying connected

**Status:** Research note · 26 November 2026
**Applies to:** the live Teacher (`app/services/teacher.py`, `app/static/js/teacher.js`).
**Question:** the voice teacher works, then quality drifts — turns get cut, replies
stop, the transcript runs off screen. Which parts are tuning, which are protocol,
and which are provider limits we cannot fix?

**Method.** Re-read `07-realtime-teacher-stack.md` for the vendor comparison and
did not re-derive it. Added the current OpenAI Realtime guidance on voice
activity detection, community reports of VAD/tool-call interactions, and what
our own stored sessions showed. Sources in §8. Tags: **[D]** provider docs,
**[C]** community report, **[O]** observed in our data.

---

## 1. Turn detection is the biggest quality lever

**[D]** Two modes:

| Mode | How it ends a turn | Good for |
|---|---|---|
| `server_vad` | fixed silence window after speech | predictable, cheap, tunable |
| `semantic_vad` | classifier decides you finished your sentence | hesitant speakers, fewer mid-sentence cuts |

**[D]** Config for `server_vad`: `threshold` (0–1, higher = needs louder audio),
`prefix_padding_ms`, `silence_duration_ms` (shorter = snappier, longer = fewer
fragments). For `semantic_vad`, `eagerness: low|auto|high` — `low` waits for the
speaker.

**What we saw [O]:** one learner sentence became three separate turns
(`Eshi, amme segenni nalehu.` / `Eshi, amasegina lahu.` / `ama seginna lahu.`) and
the tutor answered fragments instead of the sentence. Default 700 ms of silence
was short for a beginner assembling a phrase.

**Decision:** stay on `server_vad` (predictable latency, well understood) but
tune for learners: **threshold 0.4, silence 900 ms**, both configurable
(`TEACHER_VAD_THRESHOLD`, `TEACHER_VAD_SILENCE_MS`). Recorded in
`07-realtime-teacher-stack.md` is the warning that `semantic_vad` at default
eagerness costs ~4.5 s per turn; if we experiment, it must be with
`eagerness: high` and a measured A/B, not by flipping the default.

## 2. Barge-in is a product decision, not a default

**[D][C]** With WebRTC the provider truncates its own audio when the learner
starts speaking; a truncated reply arrives as `response.done` with
`status: "cancelled"`. A bridge (WebSocket) would have to send
`conversation.item.truncate` itself.

**Trade-off:** interruption feels natural for an advanced speaker and hostile
for a beginner who repeats themselves while thinking. **[O]** In session 7 the
learner took five turns with zero tutor turns: each repeat cancelled the answer
still being generated.

**Decision:** `interrupt_response: false` by default
(`TEACHER_INTERRUPT_RESPONSE`). A 12-word reply always finishes. Revisit when
learners are consistently producing full sentences.

## 3. Status must narrate the three states

Learners cannot see latency, only silence. The panel now distinguishes:

| State | Signal |
|---|---|
| listening | `input_audio_buffer.speech_started` → "Listening…" |
| thinking | response created, no audio yet → previous status stays |
| speaking | `response.output_audio.delta` → "Kiku is speaking…" |
| done | `response.done` completed → "Listening…" |
| failed / cut | `response.done` failed / incomplete → explicit message |
| no reply | 15 s watchdog after a learner turn → feedback/dropped-call hint |

**[C]** `cancelled` is a normal barge-in, not an error; it must not be reported
as a failure. We only surface `failed` and `incomplete`.

## 4. Sessions end; the UI must survive that

- **[D]** OpenAI Realtime caps a session at 60 minutes. Our own cap is 15
  minutes per call and 20 minutes per day, enforced server-side.
- **[O]** When our server marks a session ended mid-call, audio keeps flowing
  (it is peer-to-peer) but tool calls start returning 404. The learner sees a
  teacher that talks but cannot drill.
- The client now watches `connectionstatechange` and the data channel, and on
  `failed` / `disconnected` it says "The call dropped. Press Start speaking to
  reconnect." and resets the controls. There is no resume: a new call is the
  cheap recovery.

## 5. Transcript UX

- **[O]** Appending the English translation after the turn rendered left the
  list scrolled above the new line. The list is a `max-height` scroll container,
  so `scrollIntoView` on the turn is not enough — anything appended *later*
  needs its own scroll.
- Rule: stick to the bottom unless the learner has scrolled up (48 px
  threshold). Applied on new turns, live partials, and late translations.
- Live partials and the final transcript should not duplicate: the partial
  element is removed before the final turn is appended (existing behaviour).
- `aria-live="polite"` on the list: fine for turns, but do not put the
  suggestion card inside the live region or every keystroke of a translation
  announcement queues.

## 6. Cost and tokenization

- Audio output tokens are coarse: a "short" reply is tens of tokens, and the
  provider can spend a minute of speech in 800 tokens.
- **[O] Ethiopic tokenizes badly.** With `max_output_tokens: 200`, Amharic
  replies came back at 25–32 characters, cut mid-word (the learner heard a
  fragment and the transcript looked broken). Korean was fine at the same cap.
- Budgets are per language: Korean 600, Amharic 1200, override with
  `TEACHER_MAX_OUTPUT_TOKENS`. Brevity comes from the prompt, not the cap.

## 7. The language wall (provider, not us)

- **[D]** The realtime transcription endpoint's accepted languages do not
  include Amharic: `af, ar, az, be, bg, bs, ca, cs, cy, da, de, el, en, es, et,
  fa, fi, fr, gl, he, hi, hr, hu, hy, id, is, it, iw, ja, kk, kn, ko, lt, lv,
  mi, mk, mr, ms, ne, nl, no, pl, pt, ro, ru, sk, sl, sr, sv, sw, ta, th, tl, tr,
  uk, ur, vi, zh`. `whisper-1` and `gpt-4o-transcribe` reject it in this
  endpoint too. Sending `language: am` fails session creation with 400
  `invalid_value` (verified by posting the session config directly).
- Auto-detection therefore runs for Amharic and can mislabel it (one turn came
  back in Thaana script). The live conversation is unaffected — the model hears
  audio — but the on-screen transcript and anything derived from it (the coach
  hint) degrade. The coach prompt now says learner turns are rough phonetic
  transcripts.
- **[D]** `07` found Gemini Live is the only realtime model listing Amharic.
  Until that changes (or we add a second provider with the user's explicit
  agreement), Amharic voice quality should be described as *working, not
  native-checked*.

## 8. Checklist

Implemented: tuned server VAD; interruption off by default; per-language token
budgets; explicit failed/incomplete messaging; 15 s no-reply watchdog;
connection-state recovery; transcript stick-to-bottom; speaking indicator;
provider errors surfaced verbatim.

Deferred, with reasons: `semantic_vad` (needs measurement, may add seconds);
session resume (new call is cheaper); streaming partial translations (cost per
delta); Amharic realtime voice quality (provider support gap).

## Sources

- OpenAI, *Voice activity detection* — https://developers.openai.com/api/docs/guides/realtime-vad [D]
- OpenAI, *Realtime conversations* — https://developers.openai.com/api/docs/guides/realtime-conversations [D]
- OpenAI community, *Using server_vad breaks tool use in realtime API* — https://community.openai.com/t/using-server-vad-breaks-tool-use-in-realtime-api/1362139 [C]
- Dograh, *How to build a voice agent with the OpenAI Realtime API* (barge-in, truncation, `cancelled`) — https://www.dograh.com/hub/blogs/build-voice-agent-openai-realtime-api [C]
- Repo, `07-realtime-teacher-stack.md` (vendor comparison, Amharic support, semantic-VAD latency) [D/M]
