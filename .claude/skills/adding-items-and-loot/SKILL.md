---
name: adding-items-and-loot
description: >
  Step-by-step checklists for adding items, loot, and checkboxes to this CSS-only game.
  Use this skill automatically whenever the user asks to add a new item (key, wrench, axe,
  etc.), a new loot collectible (coin, gem, seashell), or a new boolean checkbox state
  (pickups, unlocks, triggers). Also triggers when the user asks about inventory icons,
  fly-to-inventory animations, pulse animations, loot counters, or adjacency click rules.
  Do not wait to be asked — load this skill proactively any time the task involves game
  world pickups, collectible state, or checkbox-driven CSS visibility in this project.
---

# Adding Items, Loot, and Checkboxes

> ⚠️ **Always edit `index.src.html`**, never `index.html`. Run `make minify` after changes to regenerate the minified output.

This project uses **pure CSS state** (checkboxes + sibling selectors) for all game logic.
Every boolean state is a hidden `<input type="checkbox">`. Follow the checklists below exactly — skipping steps causes visual glitches (visible checkboxes, broken animations, wrong z-index).

---

## Checkbox Types — Pick One First

| Type | Class | When to use |
|------|-------|-------------|
| **Class-based** | `class="loot-checkbox"` | Loot pickups only — hiding, debug visibility, and debug positioning are all automatic |
| **ID-based** | unique `id="..."` | Everything else: items, unlocks, triggers, state flags |

---

## Checklist: ID-Based Checkbox

Use for items and any non-loot state (e.g. `#key-pickup`, `#tree-chopped`).

**1. Add the HTML input** (before `.game-world` in DOM order — required for sibling selectors):
```html
<input type="checkbox" id="my-checkbox" title="my-checkbox">
```

**2. Add ID to the hidden inputs CSS rule** (find the rule starting with `.position-radio, .level-radio, .loot-checkbox, #key-pickup, ...`):
```css
.position-radio, .level-radio, .layer-radio, .loot-checkbox,
#key-pickup, ..., #my-checkbox {
    display: none;
}
```
⚠️ Skip this and the checkbox will appear as a visible element in the top-left of the play area.

**3. Add to debug toggle visibility rule** (find `#debug-toggle:checked ~ ...`):
```css
#debug-toggle:checked ~ #my-checkbox,
```

**4. Add debug position** (unique `left` offset so it doesn't overlap other debug checkboxes):
```css
#my-checkbox { top: 50px; left: XXXpx; }
```

---

## Checklist: Class-Based Checkbox (Loot Only)

Only one step needed:
```html
<input type="checkbox" id="loot-SX-LY-PZ-pickup" class="loot-checkbox" title="coin">
```
The `loot-checkbox` class handles hiding, debug visibility, and debug positioning automatically.

---

## Checklist: New Item

Items are pickable objects that go into the inventory (key, wrench, axe, battery, id card, scuba gear, torch). Complete all 8 steps.

### 1 — CSS color variable
```css
--myitem-color: #RRGGBB;
```

### 2 — Checkbox
ID-based (see checklist above). Must be before `.game-world` in DOM:
```html
<input type="checkbox" id="myitem-pickup" title="myitem">
```

### 3 — In-game element
Inside `.game-world` at the item's stage location:
```html
<span class="myitem-hover-area"></span>
<label for="myitem-pickup" class="myitem-in-game"><svg><use href="#myitem"/></svg></label>
<span class="tooltip myitem-tooltip">My Item</span>
```
CSS positioning rules:
- Position using `bottom` and `left` with CSS variables
- `pointer-events: none` by default
- Hover area: `z-index: var(--z-item-hover)` (100) — item itself: `z-index: var(--z-items)` (800)

### 4 — Adjacency rules (pulse + enable click)
These fire when the player is adjacent **and** the item is not yet picked up:
```css
/* Hide hover area so the label click works */
#level-Y:checked ~ #pos-X:checked ~ .game-world .myitem-hover-area {
    display: none;
}
/* Show tooltip on hover */
#level-Y:checked ~ #pos-X:checked ~ #myitem-pickup:not(:checked) ~ .game-world .myitem-in-game:hover ~ .myitem-tooltip {
    opacity: 1;
}
/* Enable clicking + pulse */
#level-Y:checked ~ #pos-X:checked ~ #myitem-pickup:not(:checked) ~ .game-world .myitem-in-game {
    pointer-events: auto;
    cursor: pointer;
    animation: myitem-pulse 1s ease-in-out infinite;
}
```
If the item is reachable from multiple locations (real + phantom), add comma-separated selectors for each location.

### 5 — Fly-to-inventory rule
Must come **after** the base positioning rule (CSS cascade — later rules win):
```css
#myitem-pickup:checked ~ .game-world .myitem-in-game {
    bottom: calc(/* inventory Y position */);
    left: calc(/* inventory X position */);
    opacity: 0;
    transition: bottom 0.6s ease-in, left 0.6s ease-in, opacity 0.3s ease-in 0.5s;
}
```
Slot `left` uses `--inv-slot-width * (offset)` — offset accounts for items already in inventory to the left.

### 6 — Inventory icon
Inside `.inv-panel`:
```html
<span class="inventory-myitem"><svg><use href="#myitem"/></svg><span class="tooltip">My Item</span></span>
```
CSS — hidden until picked up, then revealed after the fly animation completes:
```css
/* default */
.inventory-myitem { visibility: hidden; }

/* after pickup */
#myitem-pickup:checked ~ .inv-panel .inventory-myitem {
    visibility: visible;
    transition-delay: 0.6s;
}
```

### 7 — Pulse keyframes
Add to the consolidated animations section:
```css
@keyframes myitem-pulse {
    0%, 100% { filter: drop-shadow(0 0 4px var(--myitem-color)); }
    50%       { filter: drop-shadow(0 0 12px var(--myitem-color)) drop-shadow(0 0 20px var(--myitem-color)); }
}
```

### 8 — Hide hover area and tooltip when picked up
```css
#myitem-pickup:checked ~ .game-world .myitem-hover-area,
#myitem-pickup:checked ~ .game-world .myitem-tooltip {
    display: none;
}
```

---

## Checklist: New Loot

Loot are collectibles (coins, gems, seashells) that fly to a counter, not the inventory.

### 1 — Checkbox
Class-based (see checklist above):
```html
<input type="checkbox" id="loot-SX-LY-PZ-pickup" class="loot-checkbox" title="coin">
```

### 2 — Container in `.game-world`
```html
<div class="container coin loot-SX-LY-PZ">
    <label for="loot-SX-LY-PZ-pickup" class="loot-in-game"><svg><use href="#coin"/></svg></label>
    <span class="loot-hover-area"></span>
    <span class="tooltip">Gold Coin</span>
</div>
```
- `.container` wrapper with loot-type class and location class
- The location class (e.g. `loot-S1-L0-P3`) controls positioning via CSS
- z-index: `--z-loot-hover` (100) for `.loot-hover-area`, `--z-loot` (800) for the container

### 3 — Location positioning CSS
```css
.loot-SX-LY-PZ {
    bottom: calc(/* level height */);
    left: calc(var(--pos-offset) + var(--pos-width) * (pos - 1) - var(--item-offset));
}
```
For S2/S3 (top row), add `var(--stage-height) +` to the `bottom` value.

### 4 — Fly-to-counter rule
```css
#loot-SX-LY-PZ-pickup:checked ~ .game-world .loot-SX-LY-PZ {
    bottom: calc(/* counter Y position */);
    left: calc(/* counter X position */);
    opacity: 0;
    transition: bottom 0.6s ease-in, left 0.6s ease-in, opacity 0.3s ease-in 0.5s;
}
```

### 5 — Counter variable
`--valuable-count` increments via `:checked` selectors counting picked-up loot. If the new loot increases the maximum collectible count beyond the current digit range, add new frames to `@keyframes digit-roll`.
