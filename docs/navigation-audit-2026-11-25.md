# Navigation and IA audit — 25 November 2026

**Scope:** the header, every learner surface under `/<lang>/`, and the
course/lesson flows. **Method:** route and template inventory, nav state audit,
and desktop/390px browser checks.

**Verdict:** the app has good individual pages but no single answer to “where do
I go next?”. The nav mixes four different kinds of work under **Practice**,
**Words** carries four overlapping lookup surfaces, and courses hide their own
progress. The fix is not more pages; it is fewer doors and one obvious lookup.

**Update, 25 November:** the IA below shipped. A later styling pass also added
one `ASSET_VERSION`, shared header typography, the token sweep, and a style
contract test; see `styling-system-decision-2026-11-25.md`.

## What was wrong

| Finding | Why it hurt |
|---|---|
| **Practice was a junk drawer** | Teacher (speaking), Scenes (roleplay), Hangul/Fidel (script course), and Sound Gym (ear training) all shared one label. Script is learning content, not practice. |
| **Four word surfaces** | Dictionary and Resources both searched the deck; Translate was the free-association lookup but sat last under Words; My terms was the saved list. “Where do I type a word?” had no obvious answer. |
| **No global lookup** | Looking up a word meant: open Words → find Translate → type → submit. The user wanted type-anywhere → translation + audio. |
| **Courses had no progress spine** | The Hangul lesson said “Day 3 of 7” but offered only Back and Next. You could not see or jump to another lesson. Fidel had a drill bar but no lesson map. |
| **Today repeated the nav** | A footer row of Mission scenes, Hangul, Sound Gym, Resources, Settings duplicated the header and made Today longer. |
| **Amharic dead ends** | Teacher stayed in the nav even though realtime Amharic speech is unsupported. Korean-only links could still appear on an Amharic page. |
| **Settings was the odd one out** | Every other destination was a disclosure group; Settings was a flat link. Minor, but it read as unfinished. |

## The IA now

| Group | Contents | Rule |
|---|---|---|
| **Learn** | Today, Review, Progress, Hangul/Fidel | Anything that advances the curriculum. Script sits here. |
| **Practice** | Teacher, Scenes, Sound Gym | Korean only. Hidden for Amharic rather than shown and rejected. |
| **Words** | Look up, Dictionary, My terms | One verb per surface: translate/lookup, search the deck, saved terms. |
| **Settings** | one page | Language, goal, timezone, reminders. |

**Resources** is no longer a top-level destination. It remains a deeper browse
view linked from the dictionary. The page and route are unchanged for existing
links.

## Look up

A search field now sits in the header on every page. Submitting it goes to
`/<lang>/translate?q=…`; the page pre-fills the query and **runs automatically**,
so “type a word, get the translation and audio” is one action. The page and nav
label now say **Look up**, not Translate.

This is still the AI phrase path, not a dictionary merge. That is deliberate:
the dictionary is a free, deck-scoped search; Look up is the generative path for
anything not in the deck. Phase 2 can merge them behind one box: deck matches
first, “translate this” as the fallback.

## Course progress

Hangul and Fidel lesson pages now carry a **clickable stepper** at the top:

- one node per lesson, current node highlighted and `aria-current="step"`;
- every node is a link, so you can jump anywhere;
- numbers keep the row legible on mobile; the page heading names the lesson;
- Hangul drills also gained a `0 / N read` progress bar, matching Fidel’s.

Progress is position, not completion. There is no lesson-completion table, and
inventing one from “you opened the page” would be dishonest. If completion is
wanted later, write it when the last drill is answered, not when the page loads.

## What shipped in this pass

- Nav regrouped: script under Learn, Practice limited to speaking/listening,
  Words reduced to Look up / Dictionary / My terms, Resources demoted.
- Amharic hides Practice and Teacher entirely; Fidel is in Learn.
- Header lookup + `?q=` auto-run + “Look up” copy.
- Clickable course stepper on Hangul and Fidel lessons.
- Hangul drill progress bar.
- Today’s duplicated footer link row removed; its tutorial step is
  language-aware.
- `.nav-lookup` and `.course-stepper` added to `docs/DESIGN.md` and `/design`.

## Open questions

1. **Merge Dictionary and Look up?** One box that searches the deck first and
   offers AI translation when there is no match would be the cleanest end state.
   It needs a result model that can hold both an `Item` and a `Phrase`.
2. **Lesson completion.** Position is visible; completion is not. Decide whether
   finishing the last drill should write an `Event` or a small progress row.
3. **Scenes stepper.** The 3-step roleplay still says “Step 1 of 3” without
   nodes. A visual stepper would orient; jumping ahead would spoil the scene, so
   only completed steps should be clickable.
4. **Asset versioning.** Shipped 25 Nov: one `ASSET_VERSION` drives every
   static include, and the style contract rejects hardcoded versions.

## Verification

- `ruff` clean; full pytest suite green.
- Header lookup, nav groups, stepper, and 390px layout checked in Chrome.
- Header lookup posts to the language-aware Look up page and auto-runs.
