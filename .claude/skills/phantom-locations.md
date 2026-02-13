# Creating Phantom Locations

## Concept

A **phantom location** is a game state (radio button value) whose logical coordinates differ from where the player visually appears. This solves the fundamental CSS-only constraint: one label click can only change one radio button. Phantom locations let a single click appear to move the player both horizontally and vertically.

There are two variants:
- **Phantom position** — a special position radio (e.g., `pos-φ`) that displays at a different position+level than its logical value
- **Phantom level** — a special level radio (e.g., `level-ρ`) that displays at a different level+position than its logical value

Both follow the same pattern: the radio stays on its logical axis (position or level), while CSS overrides make the player render at a displaced visual location. Exit arrows then bring the player back to a real coordinate on that same axis.

## Existing Examples

| Name | Logical state | Visual location | Purpose |
|------|--------------|-----------------|---------|
| φ (phi) | L8-Pφ | S3-L9-P17 | Floating platform in S3 — entering via up-arrow at L8-P17 |
| κ (kappa) | L3-P18 | S5-L4-P18 | Teleporter exit from S3→S5 — level stays at L3, displays one level higher |
| ρ (rho) | Lρ-P13 | S3-L6-P14 | Teleporter exit from S5→S3 — position stays at P13, displays one position right |

## Naming Convention

Use Greek letters for phantom IDs. The letter appears in the radio ID (`pos-φ`, `level-ρ`) and in arrow class names (`arrow-φ-left`, `arrow-ρ-left`).

---

## Creating a Phantom Position

A phantom position adds a new position radio button. The player's level stays unchanged, but they appear at a different (position, level) visually.

### Checklist

#### 1. HTML: Add position radio button
After the last `pos-*` radio (currently before `pos-φ`), add:
```html
<input type="radio" name="position" id="pos-X" class="position-radio" title="pos-X">
```
Using `class="position-radio"` automatically handles:
- Hidden by the `.position-radio { display: none; }` bulk rule
- Shown in debug mode by `#debug-toggle:checked ~ .position-radio { display: block; }`

#### 2. CSS: --pos variable for tooltip
Near the other `--pos` definitions (~line 355):
```css
#pos-X:checked ~ .game-world { --pos: "PX"; }
```

#### 3. CSS: Viewport scroll
Add `#pos-X:checked ~ .game-world` to the correct horizontal scroll group:
- Positions 1-6: no translateX (left column)
- Positions 7-12: `--world-translateX: calc(var(--pos-width) * -6)` (middle column)
- Positions 13-18, φ: `--world-translateX: calc(var(--pos-width) * -12)` (right column)

#### 4. CSS: Debug position
Add a unique position in the debug grid. Positions use `top: 10px` with incrementing `left` values (~line 1449+):
```css
#pos-X { top: 10px; left: XXXpx; }
```

#### 5. CSS: Player visual position
Override both `left` and `bottom` to place the player at the visual location. Place this near the other phantom position rules (~line 2246):
```css
#level-Y:checked ~ #pos-X:checked ~ .game-world .player {
    left: calc(var(--pos-offset) + var(--pos-width) * (visual_pos - 1));
    bottom: calc(/* visual level height */);
}
```
- For S2/S3 (top row), add `var(--stage-height) +` to the bottom calculation
- The level selector scopes this to only apply when the phantom is active

#### 6. CSS: Stage subtitle
Subtitle display rules use `:is(...)` lists of level and position IDs (~line 2737). Phantom radios are **not** automatically included — you must add the phantom ID to the correct stage's subtitle rule. For example, to show "The Hangar" (S3) for a phantom position `pos-X`:
```css
/* Add #pos-X to the position list */
:is(#level-5, ...):checked ~ :is(#pos-13, ..., #pos-X):checked ~ .subtitle-S3 {
    display: block;
}
```

#### 7. CSS: Landing transition (optional)
If the exit arrow leads to a position where the player "falls" (visual level changes), add the landing position to the transition rule:
```css
#level-Y:checked ~ #pos-Z:checked ~ .game-world .player {
    transition: left 0.3s ease-out, bottom 0.3s ease-in;
}
```

#### 8. Add exit arrows — see [Adding Arrows from a Phantom Location](#adding-arrows-from-a-phantom-location) below

#### 9. Add entry mechanism
The entry point is a label that targets `pos-X`. This can be:
- A regular arrow label (`for="pos-X"`)
- A teleporter label (`for="pos-X"`)
The entry label appears at the location *before* the phantom, not at the phantom's visual location.

---

## Creating a Phantom Level

A phantom level adds a new level radio button. The player's position stays unchanged, but they appear at a different (position, level) visually.

### Checklist

#### 1. HTML: Add level radio button
After the last `level-*` radio, add:
```html
<input type="radio" name="level" id="level-X" class="level-radio" title="level-X">
```
Using `class="level-radio"` automatically handles hiding and debug visibility.

#### 2. CSS: --level variable for tooltip
Near the other `--level` definitions (~line 344):
```css
#level-X:checked ~ .game-world { --level: "LX"; }
```

#### 3. CSS: Viewport scroll (vertical)
Add `#level-X:checked ~ .game-world` to the correct vertical scroll group:
- Levels 0-4: no translateY (bottom row — S1/S4/S5)
- Levels 5-9: `--world-translateY: var(--stage-height)` (top row — S0/S2/S3)

#### 4. CSS: Debug position
Add below the existing level debug positions (~line 1448):
```css
#level-X { top: YYYpx; left: 30px; }
```
The level debug positions are stacked vertically at left 30px/40px alternating.

#### 5. CSS: Player visual position
Override both `left` and `bottom`:
```css
#level-X:checked ~ #pos-Y:checked ~ .game-world .player {
    left: calc(var(--pos-offset) + var(--pos-width) * (visual_pos - 1));
    bottom: calc(/* visual level height */);
}
```

#### 6. CSS: Stage subtitle
Subtitle display rules use `:is(...)` lists of level and position IDs (~line 2737). Phantom radios are **not** automatically included — you must add the phantom ID to the correct stage's subtitle rule. For example, to show "The Hangar" (S3) for a phantom level `level-X`:
```css
/* Add #level-X to the level list */
:is(#level-5, ..., #level-X):checked ~ :is(#pos-13, ...):checked ~ .subtitle-S3 {
    display: block;
}
```

#### 7. Add exit arrows — see [Adding Arrows from a Phantom Location](#adding-arrows-from-a-phantom-location) below

#### 8. Add entry mechanism
The entry point is a label that targets `level-X` (e.g., a teleporter `for="level-X"`).

---

## Adding Arrows from a Phantom Location

Arrows let the player leave the phantom location and return to real coordinates. Each exit arrow needs changes in three areas: positioning CSS, display rules, and HTML elements.

### In-game arrow

#### 1. CSS: Arrow positioning
Add near the other phantom arrow positions (~line 3074, section "Phantom position special arrows"):
```css
.arrow-X-left {
    left: calc(var(--pos-offset) + var(--pos-width) * N + 12px);
    bottom: calc(/* visual level height */ + 19px);
}
```

Positioning conventions:
- **Left arrows**: `left` uses `(visual_pos - 1) - 0.5` multiplier (halfway between current and left neighbor). Add `+ 12px`.
- **Right arrows**: `left` uses `(visual_pos - 1) + 0.5` multiplier. Add `+ 12px`.
- **Up arrows**: `left` uses `(visual_pos - 1)` multiplier. Add `+ 10px`. Bottom adds `+ 72.5px` above platform.
- **Down arrows**: not typically needed (phantom locations are usually "high" positions you leave horizontally or by going up).
- Bottom value: same formula as player bottom but with `+ 19px` instead of `- 2px`.
- For S2/S3 (top row), include `var(--stage-height) +` in the bottom.

#### 2. CSS: Arrow display rule
Add near the other phantom arrow display rules (~line 3315):
```css
/* For phantom positions (keyed on level + phantom pos): */
#level-Y:checked ~ #pos-X:checked ~ .game-world .arrow-X-left { display: block; }

/* For phantom levels (keyed on phantom level + pos): */
#level-X:checked ~ #pos-Y:checked ~ .game-world .arrow-X-left { display: block; }
```

#### 3. HTML: Arrow label in `.game-world`
Add near the other phantom arrow labels (~line 5651):
```html
<label for="real-target" class="arrow arrow-left arrow-X-left"></label>
```
The `for` attribute targets the **real** radio value the player moves to (e.g., `for="pos-16"` or `for="level-6"`). The arrow can only change the radio on the phantom's own axis (position arrows change position, level arrows change level).

### Nav-panel arrow

#### 4. CSS: Nav-panel display rule
Add near the other phantom nav rules (~line 3508):
```css
#level-Y:checked ~ #pos-X:checked ~ .nav-panel .nav-left[for="real-target"] { display: block; }
```

#### 5. HTML: Nav-panel label
If a nav label with the same `for` value and direction class doesn't already exist, add one in the appropriate nav-cell:
- Left arrows: in `.nav-cell-left` div
- Right arrows: in `.nav-cell-right` div
- Up arrows: in `.nav-cell-up` div
- Down arrows: in `.nav-cell-down` div

```html
<label for="real-target" class="nav-btn nav-left"></label>
```

**Important**: The display rule uses an attribute selector (e.g., `.nav-left[for="level-6"]`) to distinguish this label from others with the same `for` value but different directions.

### Hiding default arrows at the phantom location

If the phantom's logical coordinates would normally show standard arrows (e.g., generic horizontal arrows at that level), you may need to explicitly hide them:
```css
#level-Y:checked ~ #pos-X:checked ~ .game-world .arrow-PX-left { display: none; }
```

---

## Teleporter Positions

Teleporters move the player between distant locations. Since a label can only change one radio, teleporters change either the position or the level, but not both — which is why they often land on a phantom location.

### Teleporter pair structure

A teleporter consists of:
1. **Entry teleporter** — a clickable label at the origin, targeting either a position or level radio
2. **Exit teleporter** — a decorative (non-clickable) platform at the destination
3. **Phantom location** at the destination (if the visual arrival point differs from the logical one)
4. **Teleport flash animation** — a visual effect triggered by the arrival state
5. **Exit arrows** from the phantom location back to real coordinates

### Entry teleporter HTML
```html
<span class="teleporter-STAGE-hover-area"></span>
<label for="level-X" class="teleporter-STAGE">
    <svg><use href="#teleporter-platform"/></svg>
</label>
<span class="tooltip teleporter-STAGE-tooltip">Teleporter</span>
```
- The `for` attribute targets either a level radio or position radio (never both)
- `pointer-events: none` by default; enabled when player is adjacent
- Pulses when clickable

### Entry teleporter CSS
```css
.teleporter-STAGE {
    position: absolute;
    width: calc(var(--pickup-size) * 3);
    height: var(--pickup-size);
    bottom: calc(/* platform height */);
    left: calc(/* position */);
    z-index: var(--z-scenery);
    pointer-events: none;
    cursor: pointer;
    animation: teleporter-cycle-orange 1.5s linear infinite;
}
/* Enable when player is adjacent */
#level-Y:checked ~ #pos-Z:checked ~ .game-world .teleporter-STAGE {
    pointer-events: auto;
    animation: teleporter-pulse 1s ease-in-out infinite, teleporter-cycle-orange 1.5s linear infinite;
}
```

### Teleport flash animation

The flash has three elements inside `.teleport-flash-overlay` (a sibling of `.game-world`):
- `.teleport-flash-in` — white dot expanding from the origin point
- `.teleport-flash-out` — white screen with hole shrinking at the destination
- `.teleport-ring` — red ring shrinking at the destination

Each is triggered by the **arrival** state (the radio value after clicking the teleporter):

```css
/* Flash-in: origin position (where player was) */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-flash-in {
    left: calc(/* origin viewport-relative X */ + 20px);
    bottom: /* origin viewport-relative Y, often 0 for off-screen */;
    animation: teleport-dot-expand 0.4s ease-out forwards;
}
/* Flash-out: destination position (where player arrives) */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-flash-out {
    left: calc(/* dest viewport-relative X */ + 20px);
    bottom: calc(/* dest viewport-relative Y */ + 28px);
    animation: teleport-hole-expand 0.6s ease-in 0.4s forwards;
}
/* Ring: same position as flash-out */
#level-X:checked ~ #pos-Y:checked ~ .teleport-flash-overlay .teleport-ring {
    left: calc(/* dest viewport-relative X */ + 20px);
    bottom: calc(/* dest viewport-relative Y */ + 28px);
    animation: teleport-ring-shrink 0.6s ease-in 0.4s forwards;
}
```

**Position calculation for flash**: The flash overlay is a sibling of `.game-world`, so its coordinates are viewport-relative (not world-relative). Use `var(--pos-offset) + var(--pos-width) * (viewport_column)` where `viewport_column` is 0-5 within the visible stage area.

### Timing
- Flash-in runs for 0.4s (white screen covers everything)
- Flash-out starts at 0.4s delay, runs 0.6s (hole opens revealing destination)
- Ring runs simultaneously with flash-out (shrinking red ring at destination)
