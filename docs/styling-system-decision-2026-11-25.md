# Styling system decision — 25 November 2026

**Question:** should Kiku switch to an official component library, and if so,
which one?

## What the front end actually looks like

Measured from `app/static/css/style.css` and `app/templates`:

| Signal | Count |
|---|---|
| CSS lines | 3,530 |
| Top-level class rules | 499 |
| Unique hex values | 49 (34 outside `:root`, in 126 declarations) |
| Raw `px` values outside `:root` | 508 |
| Breakpoints | 7 (`900, 768, 700, 620, 600, 560, 480`) |
| Page-header patterns | 5 (`page-hero`, `page-head`, `learn-header`, `dash-head`, `review-top`) |
| Card families | 13 |
| Button families | 9 |
| Asset version values | 5 (`20261123`, `20261125`, `20261125b/c/m`) |
| Inline `style=` attributes | 0 (good) |

The inconsistency is not mainly color. It is that each page grew its own
header, card, button, and spacing model on top of a token layer that was only
partly adopted. There are three styling systems in the same file:

1. **Legacy raw CSS** (`px`, hex, one-off classes).
2. **The token layer** (`--primary`, `--space-*`, `--radius-*`).
3. **Page families** added later (`dash-*`, `review-*`, `teacher-*`, `fidel-*`,
   `scene-*`, `hangul-*`, `sound-*`, `pair-*`, `production-*`).

A component library would replace the primitives. It would **not** decide that
five headers should be one, or that 13 cards should be three. That work is the
component contract, and it has to happen either way.

## Options

### 1. Internal component layer — recommended

Keep Flask + Jinja + vanilla JS. Split the stylesheet and add Jinja macros so a
page composes components instead of inventing them.

- `tokens.css` — primitives, semantic colors, spacing, type, radius, motion.
- `base.css` — reset, typography, links, focus, `prefers-reduced-motion`.
- `components.css` — button, field, card, page header, empty state, chip, stat,
  stepper, help, nav, transcript.
- `pages.css` — layout overrides only; no colors, no new primitives.
- Jinja macros: `page_head`, `card`, `button`, `field`, `empty_state`, `stat`,
  `stepper`, `help`.
- One `ASSET_VERSION`; a Python check that fails on new raw hex/`px` outside
  `tokens.css` and on duplicate selectors.
- Standardize on **one** page-header macro and **three** card sizes
  (page card, list card, compact card).

Cost: incremental, page by page. Keeps the app’s identity and the no-build
deploy. This is the only option that directly removes the 5/13/9 duplication
without adding a second system.

### 2. Bootstrap 5.3, vendored, no build

The closest thing to an “official” library that fits server-rendered Jinja.

- Pros: mature, accessible components, grid, forms, nav, cards, modals; no Node.
- Cons: a visible identity reset; ~200 KB CSS + JS; custom review/teacher/fidel
  surfaces stay custom; during migration there are **two** systems, which is the
  exact problem today, only larger. You would still need the page-header/card
  decisions above.

### 3. Tailwind + daisyUI, with a build step

- Pros: strongest utility system and the best story if several contributors
  edit the UI daily.
- Cons: Node/Tailwind pipeline, a rewrite of ~3,500 CSS lines into Jinja class
  strings, and an explicit reversal of the project’s no-build decision. Not
  justified for a single-user local app yet.

### 4. Pico CSS

Tiny and semantic, but it has no real card/stepper/nav-dropdown component set.
It would not cover the learning surfaces; not enough.

**Material UI / shadcn / Chakra are React-only.** Adopting them means rewriting
the front end, not restyling it. Not on the table.

## Recommendation

Do **option 1 first**. If it still feels inconsistent after the component
contract exists, adopt **Bootstrap 5.3** as the primitive layer and keep the
Kiku components on top. Do not add Bootstrap or Tailwind on top of the current
stylesheet without removing the old page CSS.

## Migration plan (option 1)

1. **Inventory and guard:** split tokens/base/components/pages, one
   `ASSET_VERSION`, add the raw-hex/px and duplicate-selector checks.
2. **One page shell:** a `page_head` macro replacing `page-hero`, `learn-header`,
   `page-head`, and `dash-head`; one `card` macro family.
3. **Utility pages first:** Today, Look up, Dictionary, Teacher, Settings.
4. **Learning surfaces second:** Review, Scenes, Hangul/Fidel, Sound Gym —
   keep their custom widgets, but rebuild them from the primitives.
5. **Delete legacy rules** until `style.css` has zero hex outside `:root`, one
   breakpoint set, and no duplicate selectors.

## Phase 1a shipped (25 November 2026)

- One `ASSET_VERSION` in `app/__init__.py`; every template uses
  `?v={{ asset_version }}`. No hardcoded asset versions remain.
- Page-header typography unified across `page-head`, `page-hero`,
  `learn-header`, and `dash-head`: same h2 size, margins, eyebrow, and body
  color. (`review-top` is a utility bar, not a page header.)
- Token sweep: unique hex outside `:root` went from **34 to 14**; hex
  declarations outside `:root` from **126 to 19**. Added semantic
  `--warning-*` and `--info-*` tokens for the grade palette.
- Merged the duplicate `.nav-container` and `.link-button` blocks.
- Added `tests/test_style_contract.py`: budgets raw hex/px, forbids duplicate
  top-level selectors, and forbids hardcoded `?v=` values.

## Phase 1b — next

- Split `style.css` into `tokens.css`, `base.css`, `components.css`, and
  `pages.css`; keep one `<link>` per layer or a build-free concatenation.
- Add Jinja macros for `page_head`, `card`, `button`, `field`, and
  `empty_state`; migrate pages to them.
- Replace the five header class names with `page_head`.
- Reduce the 13 card families and 9 button families to a small set of
  primitives plus semantic variants.
- Cut the 508 raw `px` values and the seven breakpoints to the documented set.

The budget test is the ratchet: debt may go down in a commit, never up.
