# Nibo's Way Out

A platform game implemented **entirely in HTML and CSS** with no JavaScript.

## Core Mechanism

The game uses **CSS sibling selectors** (`~`) to create conditional logic:
- Radio buttons for exclusive states (position, level)
- Checkboxes for boolean states (item pickups, unlocks)
- Labels trigger state changes when clicked
- All inputs must appear **before** the elements they control in the DOM

```css
/* Example: Show escape arrow only when at correct position with tree chopped */
#level-0:checked ~ #pos-12:checked ~ #tree-chopped:checked ~ .game-world .arrow-escape {
    display: block;
}
```

## Document Structure

The HTML ordering is critical for sibling selectors to work:
1. CSS styles (including all state-based selectors)
2. State inputs (all radios and checkboxes)
3. UI elements (nav-widget, inventory, subtitles)
4. Game world (platforms, items, hazards, player, overlays)

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

## Stage Scrolling

The viewport shows one stage at a time. When crossing stage boundaries, the entire `.game-world` translates:
- Positions 1-6: no transform (stage 1 visible)
- Positions 7-12: `translateX(-6 * pos-width)` (stage 2 visible)
- Positions 13-18: `translateX(-12 * pos-width)` (stage 3 visible)

## Coordinate System

All positioning derives from CSS variables (`--pos-width`, `--platform-height`, etc.). Player and element positions are calculated as:
- X: `calc(var(--pos-offset) + var(--pos-width) * (pos - 1))`
- Y: Based on level with platform height calculations

## Naming Conventions

- **Location format:** `LxPy` (Level x, Position y)
- **Stage prefixes:** `-s1-`, `-s2-`, `-s3-` in class names
- **Vertical navigation:** "ladders" (stage 1), "vines" (stage 2) - same mechanic, different visuals
- **Vertical down:** "grates" (stage 1), "branches" (stage 2)

## Visual Styles per Stage

- **Stage 1:** Industrial/factory aesthetic - rusted metal platforms with rivets, wooden ladders
- **Stage 2:** Jungle aesthetic - organic green platforms, rock formation on left edge, vines for climbing
- **Stage 3:** Hangar aesthetic - bluish-grey metallic platforms, concrete floor, spine ladders (central pole with alternating rungs)

## Ladder Types

- **`.ladder`** - Base class with shared positioning properties
- **`.wooden-ladder`** - Traditional two-rail ladder with horizontal rungs (stage 1)
- **`.spine-ladder`** - Central metal pole with alternating rungs on each side (stage 3)

## Overlays

Overlays share a base `.overlay` class with common styling. Specific types:
- **`.title-screen-overlay`** - Shown on game start, hidden when `#title-screen-toggle` is checked
- **`.death-screen-overlay`** - Shown when player reaches hazard locations
- **`.escape-screen-overlay`** - Shown when `#escaped` checkbox is checked

## Conditional Animations

Items pulse/glow when the player can interact with them. This requires combining position checks with item state:
```css
#level-4:checked ~ #pos-1:checked ~ .game-world .key-in-game {
    animation: key-pulse 2s infinite;
}
```

## Winning Route

1. Pick up **key** (L4P1)
2. Use key on **toolbox** (L2P6) → unlocks toolbox, key consumed
3. Pick up **wrench** from toolbox
4. Use wrench on **door** (L0P6) → door opens, enter stage 2
5. Pick up **axe** (L4P12)
6. Use axe on **tree** (L0P12) → tree chopped, escape arrow appears
7. Click escape arrow → victory

## Phantom Positions

**Challenge:** One label can only apply to one input element. This makes is non-trivial
to make a player move horizontally and have them fall vertically as part of the same move:
it would require two radio buttons to change state.

**Solution: Phantom positions** - a state that differs from its visual location.

Example: `stage-3-pos-φ`
 - The player is at S3-L3-P5 and moves up
 - This moves them to S3-L3-Pφ. This counts as *horizontal* movement only.
 - This position is shown as if the player were at S3-L4-P5.
 - As soon as the player moves left or right, they are moved back to the physical location (L3-P4 or L3-P6)

Since all these transitions stay on L3, they only change the position radio - making them valid single-input operations.

## Debug Mode

The `#debug-toggle` checkbox reveals all state inputs for testing. Each input has a `title` attribute describing its purpose.
