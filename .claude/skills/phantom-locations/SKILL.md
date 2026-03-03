---
name: phantom-locations
description: >
  Implementation guide for phantom locations, phantom positions, phantom levels,
  teleporters, and teleport flash animations in this CSS-only game.
  Use this skill automatically whenever the user asks to add a phantom position or level
  (pos-φ, level-ρ style), a new teleporter, a teleport flash effect, or exit arrows from
  a phantom location. Also triggers when dealing with Greek-letter radio IDs, visual
  position overrides, or any state where the player's logical coordinates differ from
  their visual appearance. Do not wait to be asked — load this skill proactively any time
  the task involves phantom coordinates, teleporter pairs, or arrival flash animations.
---

# Phantom Locations

> ⚠️ **Always edit `index.src.html`**, never `index.html`. Run `make minify` after changes.

A **phantom location** is a radio button state whose logical coordinates differ from where the player visually appears. This solves the core CSS-only constraint: one label click can only change **one** radio button. Phantoms let a single click appear to move the player diagonally.

## Two Variants

| Type | Logical axis | Visual override | Exits via |
|------|-------------|-----------------|-----------|
| **Phantom position** | `pos-X` stays on position axis | CSS overrides `left` + `bottom` of player | Arrows that change position only |
| **Phantom level** | `level-X` stays on level axis | CSS overrides `left` + `bottom` of player | Arrows that change level only |

**Naming convention:** Use Greek letters (`pos-φ`, `level-ρ`, `level-σ`, `level-τ`). The letter appears in the radio ID and in all arrow class names (e.g. `arrow-φ-left`).

## Existing Phantoms

| Name | Logical state | Visual location | Purpose |
|------|--------------|-----------------|---------|
| φ (phi) | L8-Pφ | S3-L9-P17 | Floating platform — up from L8-P17 |
| ρ (rho) | Lρ-P13 | S3-L6-P14 | Teleporter exit S5→S3 (N/θ) |
| σ (sigma) | Lσ-P14 | S3-L9-P15 | Teleporter exit S5→S3 (ζ/η) |
| τ (tau) | Lτ-P18 | S5-L4-P18 | Teleporter exit S3→S5 |

---

## Checklist: Phantom Position

### 1 — HTML: position radio
Add after the last `pos-*` radio (before `pos-φ`). `class="position-radio"` handles hiding and debug visibility automatically:
```html
<input type="radio" name="position" id="pos-X" class="position-radio" title="pos-X">
```

### 2 — CSS: `--pos` tooltip variable
Near the other `--pos` definitions (~line 355):
```css
#pos-X:checked ~ .game-world { --pos: "PX"; }
```

### 3 — CSS: Viewport horizontal scroll
Add to the correct scroll group:
- P1–P6: no translateX
- P7–P12: `--world-translateX: calc(var(--pos-width) * -6)`
- P13–P18, φ: `--world-translateX: calc(var(--pos-width) * -12)`

### 4 — CSS: Debug position
Unique `left` offset, stacked at `top: 10px` (~line 1449):
```css
#pos-X { top: 10px; left: XXXpx; }
```

### 5 — CSS: Player visual position
Overrides both `left` and `bottom` to place the player at the visual location (~line 2246):
```css
#level-Y:checked ~ #pos-X:checked ~ .game-world .player {
    left: calc(var(--pos-offset) + var(--pos-width) * (visual_pos - 1));
    bottom: calc(/* visual level height */);
}
```
For S2/S3 (top row), add `var(--stage-height) +` to `bottom`.

### 6 — CSS: Stage subtitle
Phantom IDs are **not** auto-included in subtitle rules. Add to the correct stage's `:is(...)` selector (~line 2737):
```css
:is(#level-5, ...):checked ~ :is(#pos-13, ..., #pos-X):checked ~ .subtitle-S3 {
    display: block;
}
```

### 7 — CSS: Landing transition (if player falls on exit)
If the exit arrow drops the player to a lower level, add a transition rule. **Always include both `left` and `bottom`** — omitting `left` causes jerky horizontal movement:
```css
#level-Y:checked ~ #pos-Z:checked ~ .game-world .player {
    transition: left 0.3s ease-out, bottom 0.3s ease-in;
}
```

### 8 — Exit arrows
See [Exit Arrows](#exit-arrows) below.

### 9 — Entry mechanism
A label (`for="pos-X"`) at the location *before* the phantom — can be a regular arrow or teleporter label.

---

## Checklist: Phantom Level

### 1 — HTML: level radio
`class="level-radio"` handles hiding and debug visibility automatically:
```html
<input type="radio" name="level" id="level-X" class="level-radio" title="level-X">
```

### 2 — CSS: `--level` tooltip variable
Near the other `--level` definitions (~line 344):
```css
#level-X:checked ~ .game-world { --level: "LX"; }
```

### 3 — CSS: Viewport vertical scroll
- Levels 0–4: no translateY (bottom row — S1/S4/S5)
- Levels 5–9: `--world-translateY: var(--stage-height)` (top row — S0/S2/S3)

### 4 — CSS: Debug position
Stacked vertically at `left: 30px` (alternating 30/40px) (~line 1448):
```css
#level-X { top: YYYpx; left: 30px; }
```

### 5 — CSS: Player visual position
```css
#level-X:checked ~ #pos-Y:checked ~ .game-world .player {
    left: calc(var(--pos-offset) + var(--pos-width) * (visual_pos - 1));
    bottom: calc(/* visual level height */);
}
```

### 6 — CSS: Stage subtitle
Same as phantom position — add the phantom ID to the correct stage's `:is(...)` selector (~line 2737).

### 7 — CSS: Bird visibility (S5 phantoms only)
If this phantom level is in S5, add its ID to the bird visibility rule:
```css
:is(#level-0, ..., #level-X):checked ~ ... { /* bird display: block */ }
```
Easy to forget — the bird rule is separate from the bird positioning rules.

### 8 — Exit arrows
See [Exit Arrows](#exit-arrows) below.

### 9 — Entry mechanism
A label (`for="level-X"`) at the origin location (e.g. a teleporter).

---

## Exit Arrows

Every phantom needs exit arrows. Each arrow requires changes in three places: positioning CSS, display rule, and HTML element. Plus a nav-panel counterpart.

### In-game arrow

**1 — CSS: Arrow positioning** (~line 3074, "Phantom position special arrows"):
```css
.arrow-X-left {
    left: calc(var(--pos-offset) + var(--pos-width) * N + 12px);
    bottom: calc(/* visual level height */ + 19px);
}
```

Positioning conventions:
- **Left**: `N = (visual_pos - 1) - 0.5` — halfway between current and left neighbor
- **Right**: `N = (visual_pos - 1) + 0.5`
- **Up**: `N = (visual_pos - 1)`, bottom adds `+ 72.5px` above platform (use `+ 10px` on left)
- Bottom formula: same as player bottom but `+ 19px` instead of `- 2px`
- S2/S3: include `var(--stage-height) +` in bottom

**2 — CSS: Arrow display rule** (~line 3315):
```css
/* Phantom position — keyed on level + phantom pos */
#level-Y:checked ~ #pos-X:checked ~ .game-world .arrow-X-left { display: block; }

/* Phantom level — keyed on phantom level + pos */
#level-X:checked ~ #pos-Y:checked ~ .game-world .arrow-X-left { display: block; }
```

**3 — HTML: Arrow label in `.game-world`** (~line 5651):
```html
<label for="real-target" class="arrow arrow-left arrow-X-left"></label>
```
`for` targets the **real** radio value the player moves to. An arrow can only change the radio on the phantom's own axis (position arrows → position radio, level arrows → level radio).

### Nav-panel arrow

**4 — CSS: Nav-panel display rule** (~line 3508):
```css
#level-Y:checked ~ #pos-X:checked ~ .nav-panel .nav-left[for="real-target"] { display: block; }
```
The `[for="..."]` attribute selector distinguishes this label from others sharing the same `for` value.

**5 — HTML: Nav-panel label** (in the correct `.nav-cell-*` div — left/right/up/down):
```html
<label for="real-target" class="nav-btn nav-left"></label>
```
Only add if a label with this `for` value and direction doesn't already exist.

### Hiding default arrows at the phantom

If the phantom's logical coordinates would normally show standard arrows, explicitly hide them:
```css
#level-Y:checked ~ #pos-X:checked ~ .game-world .arrow-PX-left { display: none; }
```

---

## Checklist: Teleporter Pair

A teleporter moves the player between distant locations. Because a label can only change one radio, the destination is usually a phantom location.

**Structure:** entry label → (changes one radio) → phantom arrival state → exit arrows back to real coords.

### Entry teleporter

**HTML** (at origin location in `.game-world`):
```html
<span class="teleporter-STAGE-hover-area"></span>
<label for="level-X" class="teleporter-STAGE">
    <svg><use href="#teleporter-platform"/></svg>
</label>
<span class="tooltip teleporter-STAGE-tooltip">Teleporter</span>
```
`for` targets either a level **or** position radio — never both.

**CSS:**
```css
.teleporter-STAGE {
    position: absolute;
    width: calc(var(--pickup-size) * 3);
    height: var(--pickup-size);
    bottom: calc(/* platform height */);
    left: calc(/* position */);
    z-index: var(--z-scenery);  /* 400 */
    pointer-events: none;
    cursor: pointer;
    animation: teleporter-cycle-orange 1.5s linear infinite;
}
/* Enable + pulse when player is adjacent */
#level-Y:checked ~ #pos-Z:checked ~ .game-world .teleporter-STAGE {
    pointer-events: auto;
    animation: teleporter-pulse 1s ease-in-out infinite, teleporter-cycle-orange 1.5s linear infinite;
}
```

### Teleport flash animation

Three elements inside `.teleport-flash-overlay` (a sibling of `.game-world`), all triggered by the **arrival** state:

```css
/* Flash-in: expands from origin (where player was) */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-flash-in {
    left: calc(/* origin viewport-relative X */ + 20px);
    bottom: /* origin viewport-relative Y, often 0 for off-screen */;
    animation: teleport-dot-expand 0.4s ease-out forwards;
}
/* Flash-out: hole opens at destination */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-flash-out {
    left: calc(/* dest viewport-relative X */ + 20px);
    bottom: calc(/* dest viewport-relative Y */ + 28px);
    animation: teleport-hole-expand 0.6s ease-in 0.4s forwards;
}
/* Ring: shrinks at destination simultaneously with flash-out */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-ring {
    left: calc(/* dest viewport-relative X */ + 20px);
    bottom: calc(/* dest viewport-relative Y */ + 28px);
    animation: teleport-ring-shrink 0.6s ease-in 0.4s forwards;
}
```

**Coordinate note:** `.teleport-flash-overlay` is a sibling of `.game-world`, so coordinates are **viewport-relative**, not world-relative. Use `var(--pos-offset) + var(--pos-width) * (viewport_column)` where `viewport_column` is 0–5 within the visible stage area.

**Timing:**
- 0.0s – 0.4s: flash-in (white dot expands, covers screen)
- 0.4s – 1.0s: flash-out (hole opens revealing destination) + ring shrinks simultaneously
