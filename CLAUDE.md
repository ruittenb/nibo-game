# Nibo's Way Out

A platform game implemented **entirely in HTML and CSS** with no JavaScript.

This file is intended to help Claude Code get up-to-speed about the applied
mechanics in this html/css file.

## Core Mechanism

The game uses **CSS sibling selectors** (`~`) to create conditional logic:
- Radio buttons for exclusive states (position, level)
- Checkboxes for boolean states (item pickups, unlocks)
- Labels trigger state changes when clicked
- All inputs must appear **before** the elements they control in the DOM

```css
/* Example: Show escape arrow only when at correct position with tree chopped (S2 uses level-5 for L0) */
#level-5:checked ~ #pos-12:checked ~ #tree-chopped:checked ~ .game-world .arrow-S2-P6-S3-P1 {
    display: block;
}
```

## Document Structure

The HTML ordering is critical for sibling selectors to work:
1. CSS styles (including all state-based selectors)
2. `#title-screen-toggle` checkbox (outside `.game-container`)
3. `.game-container` containing:
   - State inputs (level radios, position radios, item checkboxes)
   - UI elements (nav-widget, inventory, subtitles)
   - `.game-world` (platforms, items, hazards, player)
   - Overlays (title, death, escape - siblings of `.game-world`)

## Navigation: Two Systems

**In-game arrows** (inside `.game-world`):
- Positioned absolutely within the scrolling game world
- Scroll with the stage when viewport shifts
- Click target is the arrow itself

**Nav-panel arrows** (inside `.nav-panel`):
- Fixed position in corner of screen
- Always visible regardless of scroll position
- Provides consistent navigation UI

Both systems use the same radio buttons (`#pos-N`, `#level-N`) as targets, so clicking either updates the same state.

## Inventory Flying Animation

When items are picked up, they animate to the inventory box:
1. The in-game item's `bottom` and `left` properties transition to inventory position
2. `opacity` fades to 0 with a delay (so it disappears after arriving)
3. The inventory icon uses `visibility: hidden/visible` with transition delay to appear after the flight completes
4. Items use `display: none` when consumed (e.g., key after toolbox unlock)

The flight destination is calculated using CSS variables to match the inventory box position.

## Stage Layout and Coordinates

The game world is a 3x2 grid of stages:

|            | pos 1-6      | pos 7-12    | pos 13-18   |
|------------|--------------|-------------|-------------|
| levels 5-9 | S0           | S2 (jungle) | S3 (hangar) |
| levels 0-4 | S1 (factory) | S4 (caves)  | S5          |

**Terminology:** A **position** is the horizontal coordinate (`pos-*` radio), a **level** is the vertical coordinate (`level-*` radio), a **layer** is the S5 maze dimension (`layer-*` radio), and a **location** is a place in the game world (the combination of position + level + layer). Two locations can look the same visually but differ by layer or by being phantom.

**Radio button IDs** are pure coordinates with no stage semantics:
- `pos-1` through `pos-18` for horizontal position
- `pos-φ` (phi) - a phantom position (see Phantom Locations)
- `level-0` through `level-9` for vertical level (5-9 display at same heights as 0-4)
- `level-ρ` (rho) - a phantom level (see Phantom Locations)

Stage is derived from the combination of position and level as shown in the table above.

**Position calculations** (using CSS variables):
- X: `calc(var(--pos-offset) + var(--pos-width) * (pos - 1))`
- Y: Based on level with `--level-height` calculations

**Stage transitions:**
- S1 → S4: Door at P6 changes position only (6→7)
- S4 → S2: Climb up at P7 changes level only (4→5)
- S2 → S3: Exit at P12 changes position only (12→13)

## Stage Scrolling

The game world is twice the viewport height, with S1/S4 at the bottom and S2/S3 at the top. The viewport scrolls via CSS `translate` property using CSS variables:

```css
.game-world {
    top: calc(var(--stage-height) * -1);  /* Initial offset to show bottom row */
    translate: var(--world-translateX, 0) var(--world-translateY, 0);
}

/* Levels 5-9 scroll up to show top row (S0/S2/S3) */
#level-5:checked ~ .game-world,
#level-6:checked ~ .game-world, /* etc */ {
    --world-translateY: var(--stage-height);
}

/* Positions 7-12 scroll left */
#pos-7:checked ~ .game-world, /* etc */ {
    --world-translateX: calc(var(--pos-width) * -6);
}
```

This approach uses **independent CSS variable rules** for X and Y translation, avoiding the combinatorial explosion of level×position selectors.

## World Positioning

S2/S3 elements are positioned one `--stage-height` above S1/S4 elements in the game world:

```css
/* S1 element */
.platform-S1-L2-P3 {
    bottom: calc(var(--level-height) * 2);
}

/* S2 element at same visual height */
.platform-S2-L2-P3 {
    bottom: calc(var(--stage-height) + var(--level-height) * 2);
}
```

This physical separation means S2 elements are naturally hidden when viewing S1/S4 (they're above the viewport), eliminating the need for visibility hacks.

## Naming Conventions

- **Location format:** `LxPy` (Level x, Position y) - levels in class names refer to visual height (0-4), not logical level
- **Stage prefixes:** `-S1-`, `-S2-`, `-S3-`, `-S4-` in class names
- **Vertical navigation:** "ladders" (S1), "vines" (S2), "spine-ladder" (S3)
- **Vertical down:** "grates" (S1), "branches" (S2)
- **Item/valuable naming:** Use stage prefix for readability but absolute position numbers that match radio IDs (e.g., `.valuable-S3-L5-P18` uses `pos-18`)

## Visual Styles per Stage

- **Stage 1 (The Factory):** Industrial/factory aesthetic - rusted metal platforms with rivets, wooden ladders
- **Stage 4 (The Caves):** Caves with maze of stalactites and stalagmites
- **Stage 2 (The Jungle):** Jungle aesthetic - organic green platforms, rock formation on left edge, vines for climbing
- **Stage 3 (The Hangar):** Hangar aesthetic - bluish-grey metallic platforms, concrete floor, spine ladders (central pole with alternating rungs)

## Ladder Types

- **`.ladder`** - Base class with shared positioning properties
- **`.wooden-ladder`** - Traditional two-rail ladder with horizontal rungs (stage 1)
- **`.spine-ladder`** - Central metal pole with alternating rungs on each side (stage 3)

## Overlays

Overlays are positioned **outside** `.game-world` but inside `.game-container`. This is important because:
- The `translate` property on `.game-world` creates a stacking context
- Elements inside a stacking context can't z-index above elements outside it
- By placing overlays as siblings of `.game-world`, they can properly layer

Overlay types:
- **`.title-screen-overlay`** - Shown on game start, hidden when `#title-screen-toggle` is checked
- **`.death-screen-overlay`** - Shown when player reaches hazard locations
- **`.escape-screen-overlay`** - Shown when `#escaped` checkbox is checked

**Title screen special case:** The player appears *in front of* the title screen overlay. This works because S1 (positions 1-6) uses `translate: none` instead of CSS variable-based translation, avoiding the stacking context issue for the starting stage.

```css
/* S1 uses translate: none to avoid stacking context on title screen */
#pos-1:checked ~ .game-world,
#pos-2:checked ~ .game-world,
/* ... */
#pos-6:checked ~ .game-world {
    translate: none;
}
```

**Important limitation:** To make the player appear above an overlay, you might think to give `.game-world` a higher z-index than the overlay. **Don't do this** - it would place the *entire* game world (platforms, items, hazards) above the overlay, defeating its purpose. The `translate: none` approach for S1 is specifically designed to avoid this problem by eliminating the stacking context entirely.

## Item Animations

Each pickupable item has two animation states:

| Item    | Pickup animation (in-game)  | Hovering animation (at target) |
|---------|----------------------------|-------------------------------|
| Key     | `key-pulse`                | `key-hovering-pulse`          |
| Wrench  | `wrench-pulse`             | `wrench-rotate`               |
| Axe     | `axe-pulse`                | `axe-chop`                    |
| Battery | `battery-pulse`            | `battery-hovering-pulse`      |
| ID Card | `idcard-pulse`             | `idcard-hovering-pulse`       |

- **Pickup animations**: Drop-shadow glow only, used when player is adjacent to the item
- **Hovering animations**: Scale + drop-shadow (or rotation for wrench/axe), used when item floats above its target (e.g., key above toolbox)

All `@keyframes` animations are consolidated in one section of the CSS for maintainability.

Items pulse/glow when the player can interact with them. This requires combining position checks with item state:
```css
/* Key is in S1 at level-4, so this selector is unchanged */
#level-4:checked ~ #pos-1:checked ~ .game-world .key-in-game {
    animation: key-pulse 1s ease-in-out infinite;
}
/* But S2/S3 items use levels 5-9, e.g., axe at S2-L9-P12: */
#level-9:checked ~ #pos-12:checked ~ .game-world .axe-in-game {
    animation: axe-pulse 1s ease-in-out infinite;
}
```

## Winning Route

1. Pick up **key** (S1-L4-P1)
2. Use key on **toolbox** (S1-L2-P6) → unlocks toolbox, key consumed
3. Pick up **wrench** from toolbox
4. Use wrench on **door** (S1-L0-P6) → door opens
5. Enter S4 through door (S4-L0-P7)
6. Climb up to S2 (S2-L5-P7)
7. Pick up **axe** (S2-L9-P12)
8. Use axe on **tree** (S2-L5-P12) → tree chopped
9. Enter S3 → navigate to escape → victory

## Phantom Locations

A phantom location is a radio button state whose logical coordinates differ from where the player visually appears. This works around the CSS constraint that one label can only change one radio button. For implementation details, see `.claude/skills/phantom-locations.md`.

Current phantom locations:

| Name | Logical state | Visual location | Purpose |
|------|--------------|-----------------|---------|
| φ (phi) | L8-Pφ | S3-L9-P17 | Floating platform — up from L8-P17, exits left/right back to L8 |
| κ (kappa) | L3-P18 | S5-L4-P18 | Teleporter exit S3→S5 — level stays L3, displays at L4 |
| ρ (rho) | Lρ-P13 | S3-L6-P14 | Teleporter exit S5→S3 — position stays P13, displays at P14 |

## Layers (S5 L0-L3)

S5 (The Sunken City) at levels 0-3 uses a **layer system** to create maze-like navigation within the same visual space. Four layer radio buttons (`layer-N`, `layer-ζ`, `layer-η`, `layer-θ`) control which horizontal arrows are available.

### Nomenclature
Layer-qualified coordinates use the **Y** prefix: `YN`, `Yζ`, `Yη`, `Yθ`. Full format: `Yθ-L2-P14`. The player tooltip on S5 shows this format (e.g., "Nibo (Yθ-L2-P15)").

### Layer cycle
Horizontal movement at "layer-boundary" gaps (P13↔P14, P15↔P16, P17↔P18) cycles through layers: **N → ζ → θ → η → N**. Movement at "position-boundary" gaps (P14↔P15, P16↔P17) either moves normally (on N/θ) or jumps 3 positions (on ζ/η).

### Visual position swaps
- **N/θ**: visual position = logical position (P13→vis13, P14→vis14, ...)
- **ζ/η**: positions are swapped in pairs (P13↔P14, P15↔P16, P17↔P18)

CSS override rules swap the player and vertical arrow `left` values when ζ/η is active at L0-L3.

### Scoping
Layer-aware CSS rules are scoped to `:is(#level-0, #level-1, #level-2, #level-3)` + S5 positions. The layer state has no visual effect outside S5 L0-L3.

### Arrow elements
- **8 layer-change labels** in `.game-world` (one per target-layer × direction), dynamically positioned via CSS
- **4 position-jump labels** in `.game-world` for the 3-position jumps on ζ/η
- **8 layer-change labels** in `.nav-panel` (mirroring in-game arrows)
- Existing position-change nav labels are reused for position-jumps on ζ/η

### Transition spec
The full transition table is in `_fabriek/doc/transitions.txt` (304 transitions).

## Debug Mode

The `#debug-toggle` checkbox reveals all game state inputs for testing. Each input has a `title` attribute describing its purpose.

## Adding New Checkboxes, Items, and Loot

For implementation checklists on adding checkboxes, items, and loot, see `.claude/skills/adding-items-and-loot.md`.

Key distinction between the two checkbox types:
- **Class-based** (`class="loot-checkbox"`): hiding and debug visibility handled automatically by class selectors
- **ID-based** (item/state checkboxes): must be individually added to the hidden inputs rule and debug toggle rule

## Z-Index Layers

┌─────────┬──────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┐
│ Z-Index │        Source        │                               Elements                                              │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ -1      │ -1                   │ Grate grid pattern (:after pseudo)                                                  │
┝━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┥
│ 0       │ 0                    │ Stage backgrounds (factory, caves, jungle, spacecraft)                              │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 50      │ --z-walls            │ Rock and warning walls                                                              │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 100     │ --z-item-hover       │ Tooltip hover areas for pickable items (key, wrench, axe, battery, idcard, torch)   │
│ 100     │ --z-loot-hover       │ Tooltip hover areas loot (coins, gems)                                              │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 200     │ --z-climbables       │ Ladders and vines                                                                   │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 300     │ --z-hazards          │ Poison, disease                                                                     │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 400     │ --z-scenery          │ Toolbox, door-container, tree-container, barrels                                    │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 500     │ --z-floating-item    │ Key-at-toolbox, wrench-at-door, axe-at-tree, battery-at-bolt, idcard-at-controls    │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 550     │ --z-underwater       │ Underwater filter overlay (S5 lower levels)                                         │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 600     │ --z-arrows           │ In-game navigation arrows                                                           │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 700     │ --z-darkness         │ Darkness mask (caves)                                                               │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 800     │ --z-items            │ Pickable items (key, wrench, axe, battery, idcard, torch)                           │
│ 800     │ --z-loot             │ Loot (coins, gems) and containers                                                   │
┝━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┥
│ 900     │ --z-ui               │ UI elements (inv-panel, counter-panel, nav-panel, title, subtitle)                  │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 1000    │ --z-title-overlay    │ Title screen overlay                                                                │
┝━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┥
│ 1100    │ --z-player           │ Player                                                                              │
┝━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┥
│ 1500    │ --z-tooltip          │ Tooltips                                                                            │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 2000    │ --z-endgame-overlay  │ Death and escape overlays                                                           │
│ 2000    │ --z-flash-overlay    │ Teleport flash screen overlay                                                       │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 9000    │ --z-state-controls   │ Game state inputs (when visible via debug toggle)                                   │
├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
│ 10000   │ --z-rotate-prompt    │ Rotate-prompt                                                                       │
└─────────┴──────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┘


This layering ensures:
- Player appears in front of the title screen on game start
- Player is hidden behind death/escape overlays when triggered

