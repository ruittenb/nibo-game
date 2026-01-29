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

**Nav-widget arrows** (inside `.nav-widget`):
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

**Radio button IDs** are pure coordinates with no stage semantics:
- `pos-1` through `pos-18` for horizontal position
- `pos-φ` (phi) - a phantom position for special movement (see Phantom Positions)
- `level-0` through `level-9` for vertical level (5-9 display at same heights as 0-4)

Stage is derived from the combination of position and level as shown in the table above.

**Position calculations** (using CSS variables):
- X: `calc(var(--pos-offset) + var(--pos-width) * (pos - 1))`
- Y: Based on level with `--platform-height` calculations

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
    bottom: calc(var(--platform-height) * 2);
}

/* S2 element at same visual height */
.platform-S2-L2-P3 {
    bottom: calc(var(--stage-height) + var(--platform-height) * 2);
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

## Z-Index Layers

Z-index layers (defined as CSS variables):
- `--z-items: 15` - Items, hazards
- `--z-door: 20` - Door (above hazards for tooltip)
- `--z-ui: 300` - UI elements (title, inventory, counter)
- `--z-tooltip: 500` - Tooltips
- `--z-overlay: 1000` - Death and escape overlays

## Conditional Animations

Items pulse/glow when the player can interact with them. This requires combining position checks with item state:
```css
/* Key is in S1 at level-4, so this selector is unchanged */
#level-4:checked ~ #pos-1:checked ~ .game-world .key-in-game {
    animation: key-pulse 2s infinite;
}
/* But S2/S3 items use levels 5-9, e.g., axe at S2-L9-P12: */
#level-9:checked ~ #pos-12:checked ~ .game-world .axe-in-game {
    animation: axe-pulse 2s infinite;
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

## Phantom Positions

**Challenge:** One label can only apply to one input element. This makes it non-trivial
to make a player move horizontally and have them fall vertically as part of the same move:
it would require two radio buttons to change state.

**Solution: Phantom positions** - a state that differs from its visual location.

Example: `pos-φ` (in S3)
 - The player is at S3-L8-P17 and moves up
 - This moves them to S3-L8-Pφ. This counts as *horizontal* movement only.
 - This position is shown as if the player were at S3-L9-P17 (visually at L4 height).
 - As soon as the player moves left or right, they are moved back to the physical location (L8-P16 or L8-P18)

Since all these transitions stay on L8, they only change the position radio - making them valid single-input operations.

## Debug Mode

The `#debug-toggle` checkbox reveals all state inputs for testing. Each input has a `title` attribute describing its purpose.

## Adding New Checkboxes

When adding a new checkbox (for item pickups, unlocks, etc.), **three things** must be updated:

1. **Add the checkbox input** in the HTML inputs section (before `.game-world`)
2. **Add the class to the hidden inputs rule** - find the CSS rule that starts with `.position-radio, .level-radio, .key-checkbox, ...` and add your new class (e.g., `.my-new-checkbox`)
3. **Add to debug visibility rule** - find the `#debug-toggle:checked ~ .game-container ...` rule and add your class
4. **Add debug position** - add a rule like `#my-checkbox { top: 50px; left: XXXpx; }` with a unique left offset

If you skip step 2, the checkbox will be visible in the top-left corner of the play area instead of hidden.

## Adding New Items and Valuables

### Items (key, wrench, axe)

1. **CSS variable** for the item color (e.g., `--wrench-color`)
2. **Checkbox** in inputs section: `<input type="checkbox" id="item-pickup">`
   - Must appear before `.game-world` in DOM order for sibling selectors to work
3. **In-game element** (`.item-in-game`):
   - Position at world location using `bottom` and `left` with CSS variables
   - `display: none` / `pointer-events: none` by default
   - Enable + pulse animation when player is adjacent and item not picked up
   - Label targets the pickup checkbox
4. **Fly-to-inventory rule**: when `#item-pickup:checked`, transition `bottom`/`left` to inventory position, fade `opacity` to 0
   - Slot position uses `--inv-slot-width * (offset)` where offset accounts for other items already in inventory
   - This rule must come after the base positioning rule (CSS cascade: later rules override)
5. **Inventory icon** (`.inventory-item` inside `.inventory`): `visibility: hidden` by default, `visible` with transition-delay when picked up

### Valuables (coins, gems)

1. **Checkbox** for pickup state: `<input type="checkbox" id="valuable-SX-LY-PZ-pickup">`
2. **Container** in `.game-world`:
   - `.container` wrapper with location class (e.g., `.valuable-S1-L0-P3`)
   - `.hover-area` span for tooltip hover detection
   - `.tooltip` span with item name
   - Label wrapping the icon, targeting the pickup checkbox
3. **Fly-to-counter rule**: when checked, transition `bottom`/`left` to valuable counter position
4. **Digit strip**: if max collectible count increases beyond current digits, add new frames to `@keyframes digit-roll`
5. **Counter variable**: `--valuable-count` increments via `:checked` selectors counting picked-up valuables
