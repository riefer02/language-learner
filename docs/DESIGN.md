# Design System

Current as of 23 November 2026. This is how Kiku’s UI is built and how to extend
it without making the interface harder to understand.

## Framework decision

Kiku is **Flask + Jinja + vanilla JavaScript + plain CSS**. There is no React,
no Vue, no Tailwind, no bundler, and no Node build step.

Why:

- The app is server-rendered and form-driven. A client framework would add state
  duplication and a build pipeline without removing real complexity.
- One CSS file is easy to audit, cache-bust, and test in a browser. It keeps the
  deploy to “Python + static files.”
- The hard problems here are information architecture, accessibility, and clear
  copy — not utility-class generation.

**Tailwind was considered and rejected for now.** It would require a Node
toolchain and a rewrite of ~2,700 lines of CSS into template class strings. It
does not fix navigation, language context, or page purpose by itself. Revisit
Tailwind only if several contributors are editing the UI daily and utility
classes become a shared convention. Until then, tokens + documented components
are the professional layer.

## Token layers

Tokens live at the top of `app/static/css/style.css`.

1. **Primitive** — raw palette values: `--blue-500`, `--ink-700`,
   `--orange-600`, `--green-100`, etc. These should appear only in `:root`.
2. **Semantic** — what a component should use: `--primary`, `--primary-soft`,
   `--accent`, `--surface`, `--surface-muted`, `--border`, `--ink-600`,
   `--success`, `--danger`, `--focus`.
3. **Scales** — `--space-1…8` (4px base), `--radius-sm/md/lg/pill`,
   `--shadow-sm/md/lg`, `--text-xs…3xl`, `--leading-tight/body`,
   `--transition-fast/base`, `--content-max/narrow`.

Rules:

- New components use semantic tokens and scales, not raw hex or arbitrary px.
- Legacy rules are migrated opportunistically. Do not add new hard-coded color
  values; prefer a token. `tests/test_style_contract.py` budgets the remaining
  raw hex/px and duplicate selectors, so debt can shrink but not grow.
- Status color is never the only signal. Pair it with text or an icon.
- The focus ring is `var(--focus)` at 3px with a 3px offset.

Current debt: the stylesheet still contains 47 unique hex values and ~222
top-level classes from the pre-token era. They are being retired component by
component, not in one risky rewrite.

## Information architecture

The home route is **Today**, not the translation utility. `/` redirects to the
learner’s language, and `/<lang>/` redirects to `/<lang>/learn`.

Navigation is grouped so the learner does not have to parse eight equal links:

| Group | Contents |
|---|---|
| **Learn** | Today, Review, Progress, Hangul/Fidel |
| **Practice** | Teacher, Scenes, Sound Gym (Korean only) |
| **Words** | Look up, Dictionary, My terms |
| **Settings** | Language, goal, timezone, reminders |

- The current language is a persistent select in the header. Changing it lands
  on Today in that language.
- The header also carries **Look up**, the free-association search. It submits
  `?q=…` to the Look up page, which searches/translates and plays the audio.
- Script courses sit under **Learn**, not **Practice**; lessons carry a
  clickable course stepper.
- “My terms” is the saved-term library. “Dictionary” searches and saves deck
  terms. **Resources** remains a deeper browse view linked from the dictionary,
  not a top-level destination.
- Korean-only surfaces (Teacher, Scenes, Sound Gym) are hidden for Amharic
  rather than shown and then rejected; Fidel replaces Hangul under Learn.

## Components

Live reference: **`/design`** (not linked from the learner nav).

| Class | Use |
|---|---|
| `.page-hero` | Page title, one-sentence purpose, language badge |
| `.language-badge` | Current target language |
| `.surface-card` | Generic white panel |
| `.teacher-panel` | Interactive panel (teacher, dictionary sections) |
| `.tutorial-card` | First-run guidance; `data-dismissible` + `[data-dismiss]` |
| `.help-tip` | Native `<details>` explanation; never a hover-only tooltip |
| `.empty-state` | What is missing, why, and the next action |
| `.chip-row` / `.chip` | Suggested searches, compact links |
| `.btn`, `.btn-primary`, `.btn-large`, `.link-button` | Actions |
| `.learn-meta` | Secondary text |
| `.term-list` / `.term-card` | Saved terms |
| `.fidel-glyph`, `.fidel-progress-bar` | Fidel trainer |
| `.scene-reply` (with `.help-tip`) | Collapsed natural reply + audio on a scene step |
| `.content-flag` (with `.help-tip`) | Quiet correction form; flat until opened |
| `.review-gradebar` | Sticky grading bar with the four buttons and keyboard hint |
| `.nav-lookup` | Global header Look up field; submits `?q=` to the Look up page |
| `.course-stepper` | Clickable lesson nodes; current node is `aria-current="step"` |
| `.dash-hero` / `.dash-stats` / `.dash-card` | Today dashboard: primary action, compact stats, continue/terms |
| `.page-head` / `.page-help` | Page title + one-time instructions behind a `?` control |

## Page composition

```html
<div class="page-hero">
  <span class="language-badge">Korean</span>
  <h2>What this page does.</h2>
  <p>One sentence about the learner’s outcome.</p>
</div>

<section class="surface-card" aria-labelledby="section-heading">
  <h3 id="section-heading">Section</h3>
  ...
</section>
```

- `base.html` owns the single `<h1>` (brand) and `<main>`.
- Page titles are `<h2>`; sections are `<h3>`.
- Page headers share one type/margin scale. `page-head` is the tool-page header
  and owns the `?` help control; `page-hero`, `learn-header`, and `dash-head`
  are legacy names on the same scale until Phase 1b migrates them.
- Tool pages put the interface first. Instructions live behind a `?`
  disclosure; the first visit opens it once (`localStorage`), then it stays
  closed. Escape or an outside click closes it.
- Use `<label>` for every control. Icon-only controls need `aria-label`.
- Use `aria-current="page"` on the active nav item.
- Test at 390px; the nav collapses at 900px.

## Accessibility contract

- Skip link to `#main-content` on every page.
- Visible focus ring on links, buttons, inputs, selects, summaries.
- Native `<details>`/`<summary>` for disclosures and help.
- `aria-expanded`/`aria-controls` on the mobile nav toggle.
- Live regions: teacher status and transcript, fidel feedback, form errors.
- `prefers-reduced-motion` disables transitions and smooth scrolling.
- No horizontal overflow at 390px.
- Every page: one `h1`, one `main`, no duplicate IDs, no unlabelled controls,
  no unnamed buttons/links, no images without `alt`.

## Changing the UI

1. Prefer an existing class before adding a new one.
2. If a new token is genuinely needed, add it to `:root` with a semantic name.
3. Add the component to `/design` with a short usage note.
4. Check desktop and 390px mobile, keyboard focus, and console errors.
5. Bump `ASSET_VERSION` in `app/__init__.py`; every template shares one
   `?v=` query string. Never hardcode a version in a page.
6. Update this file and `AGENTS.md` if a convention changed.

**Latest audits:** [`design-audit-2026-11-25.md`](design-audit-2026-11-25.md) ·
[`navigation-audit-2026-11-25.md`](navigation-audit-2026-11-25.md).
