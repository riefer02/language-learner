# Design audit — 25 November 2026

**Scope:** the learner-facing UI in `app/templates`, `app/static/css/style.css`,
and `app/static/js`, plus the contract in `docs/DESIGN.md`.

**Method:** static inspection of every template, stylesheet, and page script;
token and class census; contrast calculation; accessibility scan for headings,
landmarks, labels, focus, live regions, and reduced motion; breakpoint review;
and a feature design pass on one scene step. No browser screenshots were taken
in this pass; the last in-browser audit is recorded in `PROJECT_STATUS.md`.

**Verdict:** the interface is coherent and accessible at the page level. There
are **no blocking usability or accessibility defects**. The debt is systemic:
the design document has drifted from the app, and the token layer is only
partly applied. Fix the documentation and the asset pipeline before adding
more components.

## Scorecard

| Area | State | Evidence |
|---|---|---|
| Page framing | Good | Every page inherits the single `h1` and `<main>` from `base.html`; page titles are `h2`. |
| Navigation | Good, one doc drift | Grouped Learn / Practice / Words, mobile disclosure with `aria-expanded`/`aria-controls`, `aria-current` present. Settings is a flat link even though `DESIGN.md` calls it a group. |
| Accessibility | Strong | Skip link, global `:focus-visible` ring, labelled controls, native `<details>`, live regions, two `prefers-reduced-motion` blocks. |
| Color contrast | Pass | Lowest measured pair is white on `--primary` at **5.11:1**; body text is 5.7–11.8:1. |
| Tokens | Partial | 49 unique hex values; **34 unique hexes still appear outside `:root` in 126 declarations**. |
| Component catalogue | Behind the UI | `/design` and `DESIGN.md` document ~12 patterns; the stylesheet has **429 top-level class selectors**. |
| CSS hygiene | Fair | 3,031 lines; duplicate blocks for `.nav-container` and `.link-button`; ~13 wrapper classes have no rule. |
| Asset versioning | Weak | CSS and JS carry independent, hand-edited `?v=` values with no shared constant. |
| Language metadata | Good | Target text carries `lang="ko"`/`lang="am"` and TTS locales are language-scoped. |

## What is working

- The **progressive-enhancement contract holds**: review grading, the nav, the
  language switch, and scene answering all work without JavaScript.
- **Disclosure is the default pattern** for help, hints, answers, and drills.
  There are no hover-only tooltips and no custom modal traps.
- **Status is never color-only**: grades, drills, and speech checks pair color
  with text.
- **The review loop protects retrieval**: grade buttons are disabled until the
  answer is revealed, and the four ratings explain themselves in place.
- `lang` attributes, script-aware fonts (Hangul and Ethiopic), and RTL token
  `language.direction` are handled centrally rather than per page.
- Every page-level control I sampled has a visible label or an accessible name.

## Findings

### High — `DESIGN.md` is no longer the source of truth

`docs/DESIGN.md` says the navigation has a **Settings group** with Language,
goal, timezone, and reminders. The shipped nav renders Settings as one flat
link. The same document lists **Browse** under Words; the shipped item is
**Resources**, and the route is `/resources`, not `/browse`.

The component table covers about a dozen patterns. Real pages also depend on
`review-card`, `grade-*`, `bubble-*`, `teacher-*`, `scene-*`, `pair-*`,
`production-*`, `fidel-*`, and the review answer block, none of which are in
the table or on `/design`.

**Why it matters:** a contributor following the document will build a different
UI than the one users see. The live style guide is the only reliable reference.

**Fix:** treat `DESIGN.md` as a map, not a mirror. Add a "page families" table
that names the review, scene, teacher, fidel, and sound-gym blocks and points at
their templates. Correct the IA table to match the shipped nav, or change the
nav to match the intent. Do this before adding the next component.

### High — the token layer is only half applied

Measured in `app/static/css/style.css`:

- 49 unique hex values in the file; 34 of them still appear **outside** the
  `:root` block, in 126 declarations.
- 465 raw `px` lengths outside the spacing scale.
- 32 raw `rgb()`/`rgba()` values outside `:root`.
- `#5b6472` (the value of `--muted`) is repeated about 20 times instead of using
  the token.
- `--primary-ink: #27446b` is a raw hex inside the semantic block rather than a
  primitive alias.

Contrast is not the problem — the values are fine. The problem is that a future
palette change will miss most of the UI, and the document's claim that "47
unique hex values" remain is a snapshot that has already moved.

**Fix:** mechanical pass, one component family at a time. Replace `#5b6472`
with `var(--muted)`, `#3a5a8c` with `var(--primary-strong)`, and the grade
colors with the existing `--success-bg`, `--danger-bg`, and `--yellow-100`
tokens. Add a CI grep that fails when a new hex appears outside `:root`.

### Medium — asset versions drift between CSS and JS

`base.html` currently serves `style.css?v=20261125`; each page script carries
its own `?v=20261123`. The CSS value had already gained a manual `g` suffix
before this pass. Nothing enforces a bump when an asset changes, so a learner
can get new HTML with stale CSS.

**Fix:** expose one `ASSET_VERSION` (or a file-mtime hash) from a context
processor and use it in every `url_for('static', ...)` include. Remove the
per-page literal versions.

### Medium — two duplicated selector blocks and dead wrapper hooks

`.nav-container` and `.link-button` each have two separate rule blocks. They
work because the later block wins, but the duplication makes overrides
unpredictable. About 13 class names used in templates (`conversation-detail`,
`fidel-practice`, `learn-terms`, `phrase-input`, `stop-btn`, `teacher-empty`,
…) have no rule at all. They are harmless hooks today and misleading tomorrow.

**Fix:** merge the duplicate blocks; either style the wrappers or delete the
hooks. Keep hooks only when a page script actually targets them.

### Low — accessibility nits

- Every nav link emits `aria-current="false"`. That is valid, but it adds noise
  to the accessibility tree. Prefer omitting the attribute unless it is `page`.
- The teacher transcript is a `role="status"`/`aria-live="polite"` list that
  receives long streamed turns. Announce a short "Kiku replied" status and keep
  the transcript out of the live region, or cap what is announced.
- `theme-color` duplicates `--blue-500` as `#4a6fa5` in `base.html`. A `<meta>`
  tag cannot read a CSS custom property, so either accept it as an intentional
  exception and note it, or inject it from config.

### Low — breakpoint sprawl

The stylesheet defines max-width breakpoints at 900, 768, 700, 620, 600, 560,
and 480 px. They are internally consistent, but the set is larger than the
documented 900/390 story. Consolidate to a small named set (mobile, tablet,
desktop) when the legacy rules are touched.

## Feature shipped in this pass: hear a natural reply on a scene step

**Request:** while a scene character asks a question, see and hear a typical
reply so the learner can train their ear for responses.

**Design decision.** The scene step is the right home: the character line is a
real question, and the canonical learner line already exists in the scene pack
as `step.target_item` (with `step.expected[0]` as a fallback). The reply sits
between the character bubble and the answer form as a **collapsed** disclosure:

```html
<details class="help-tip scene-reply" data-speak-on-open>
  <summary>Hear a natural reply</summary>
  <div class="scene-reply-body">
    <p class="scene-reply-korean" lang="ko">…</p>
    <p class="scene-reply-romanization">…</p>
    <p class="scene-reply-english" lang="en">…</p>
    <button class="btn speak-btn" data-speak="…">Hear the reply</button>
  </div>
</details>
```

Why collapsed:

- It preserves **retrieval first**. Showing the expected line open by default
  would turn production practice into copying.
- It follows the existing disclosure contract instead of adding a new panel.
- Opening it plays the line once (a user gesture, so speech synthesis is
  allowed); the button replays it. The button is labelled and the text carries
  `lang="ko"`, so screen-reader and language-switch behaviour match the rest of
  the app.

**Reuse:** `.help-tip` for the shell, `.speak-btn` for audio, existing semantic
tokens (`--text-xl`, `--primary`, `--ink-500`, `--space-2`) for the inner text.
No new colors, no new focus handling, no JS dependency beyond the existing
speech fallback.

**Test:** `tests/test_scenes.py::test_scene_step_offers_natural_reply_audio`
asserts the disclosure, the canonical reply text, the `data-speak` value, and
the accessible label.

**Known limits:**

- Audio uses browser speech synthesis, consistent with the character line and
  the rest of the scene surface. It is a stopgap until scene audio is
  pre-generated and native-reviewed.
- Two steps have a slightly different canonical item and first accepted answer
  (`cafe-order` step 3, `pharmacy` step 2). The UI shows the canonical item, so
  the displayed line can be a superset of the matcher's first answer. If that
  divergence grows, add an explicit `reply` field to the scene data instead of
  reusing `target_item`.

## Recommended order of work

1. Correct `DESIGN.md` and add page families to `/design` (documentation truth).
2. Add one `ASSET_VERSION` and remove per-page literals.
3. Token sweep for `#5b6472`, `#3a5a8c`, and the grade palette.
4. Merge duplicate selector blocks; delete dead wrapper hooks.
5. Fix the live-region and `aria-current` nits.
6. Add a CI grep for new raw hex values outside `:root`.

## Verification for this pass

- `venv/bin/ruff check app config.py run.py tests` — clean.
- `venv/bin/python -m pytest` — **257 passed**.
- New scene test passes; the rendered step contains the reply text, audio hook,
  and accessible label.
- Contrast measured, not assumed: every sampled text/background pair is at or
  above WCAG AA for normal text.
