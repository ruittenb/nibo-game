# Nibo's Way Out

A complete platform game implemented **entirely in HTML and CSS** with
no JavaScript. All game logic, state management, animations, and
interactions are handled through CSS selectors and checkbox/radio button
state.

## Core Concept

The game uses **CSS sibling selectors** (`~`) to create conditional logic:
- Radio buttons for exclusive states (position, level)
- Checkboxes for boolean states (item pickups, unlocks)
- Labels trigger state changes when clicked
- CSS selectors show/hide/animate elements based on checked states

## State Management

### Position & Level (Radio Buttons)
```
Levels:  #level-0 (ground) through #level-4 (top)
Positions: #pos-1 through #pos-12 (pos 1-6 = stage 1, pos 7-12 = stage 2)
```

### Game State (Checkboxes)
| Checkbox | Purpose |
|----------|---------|
| `#key-pickup` | Player has key |
| `#toolbox-unlock` | Toolbox opened (needs key) |
| `#wrench-pickup` | Player has wrench |
| `#door-unlocked` | Door to stage 2 open (needs wrench) |
| `#axe-pickup` | Player has axe |
| `#tree-chopped` | Tree destroyed (needs axe) |
| `#escaped` | Victory triggered |
| `#valuable-LxPy-pickup` | Valuable (coin/gem) at level x, position y collected |
| `#debug-toggle` | Shows state checkboxes for debugging |

### CSS Selector Pattern
```css
/* Show element when conditions are met */
#level-0:checked ~ #pos-12:checked ~ #tree-chopped:checked ~ .game-world .arrow-escape {
    display: block;
}
```

## Coordinate System

All positioning uses CSS variables:
```css
--pos-width: 150px;           /* Horizontal distance between positions */
--platform-height: 110px;     /* Vertical distance between levels */
--ground-height: 35px;        /* Ground level height */
--platform-thickness: 30px;   /* Platform visual thickness */
--pos-offset: 55px;           /* Starting X offset */
--pickup-size: 28px;          /* Size of pick-uppable items and valuables */
```

**Player X position:** `calc(var(--pos-offset) + var(--pos-width) * (pos - 1))`
**Player Y position:** Based on level with platform calculations

## Item Chain (Win Condition)

```
Key (L4P1) → Toolbox (L2P6) → Wrench → Door (L0P6) → Stage 2
                                                      ↓
                              Axe (L4P12) → Tree (L0P12) → Escape!
```

## Navigation

**Horizontal arrows:** Between adjacent positions, shown based on current position
**Vertical arrows:** At ladder/vine locations for climbing
**Nav panel:** Fixed widget in corner with directional buttons

Arrow visibility controlled by selectors like:
```css
#pos-5:checked ~ .game-world .arrow-5-6 { display: block; }
```

## Hazards

- **Skull** at L1P6 - triggers death overlay
- **Bacteria** at L0P10 and L1P9 - triggers death overlay
- Death overlay: fades in with "YOU DIED / GAME OVER"

## Adding New Elements

### New Item
1. Add checkbox: `<input type="checkbox" id="item-name" class="item-checkbox" title="item">`
2. Add to CSS hiding rule (line ~509) and debug show rule (line ~554)
3. Add debug position: `#item-name { top: Npx; left: Npx; }`
4. Create label in game-world: `<label for="item-name" class="item-in-game">...</label>`
5. Add visibility/interaction selectors

### New Hazard
1. Add element with position class: `<svg class="skull skull-LxPy">...</svg>`
2. Add death trigger: `#level-x:checked ~ #pos-y:checked ~ .death-overlay { opacity: 1; }`

### New Arrow/Navigation
1. Add label: `<label for="pos-N" class="arrow arrow-right arrow-h arrow-X-Y"></label>`
2. Add position CSS: `.arrow-X-Y { left: calc(...); }`
3. Add visibility rule: `#pos-X:checked ~ .game-world .arrow-X-Y { display: block; }`
4. Add nav panel equivalent if needed

## Naming Conventions

- **Location format:** `LxPy` (Level x, Position y) - e.g., `L2P6`, `L0P12`
- **Arrows:** `arrow-X-Y` (from position X to Y)
- **Stage 1 prefix:** `-s1-` for stage 1 elements (e.g., `platform-s1-1`, `ladder-s1-L0P5`, `grate-s1-L1P1`)
- **Stage 2 prefix:** `-s2-` for stage 2 elements (e.g., `platform-s2-1`, `vine-s2-L0P8`, `branch-s2-L1P7`)
- **Checkboxes:** `id="thing-action"` (e.g., `key-pickup`, `door-unlocked`)

## Key Files Structure

Everything is in `index.html` (~2600 lines):
- CSS styles, animations, state selectors
- State inputs (radios, checkboxes)
- Nav panel, inventory, UI
- Game world (platforms, items, hazards, overlays)

## Debug Mode

Press the debug checkbox (top-left) to show all state checkboxes/radios for testing.
Each has a `title` attribute showing what it controls.

## Overlays

- **Death overlay:** `.death-overlay` - red text, triggered by hazard positions
- **Escape overlay:** `.escape-overlay` - green text, triggered by `#escaped:checked`
- Both use `transition: opacity 1s ease-in` for fade effect

## Animations

Key animations defined via `@keyframes`:
- `idle` - player breathing
- `coin-pulse` - item/coin availability glow
- `gem-pulse` - gem availability glow (aquamarine)
- `tree-pulse`, `door-pulse` - interactive object availability
- `deadly-roll` - hazard animation
- `gem-sparkle` - gem idle sparkle effect

## Stage Scrolling

At positions 7+, the game world translates left to show stage 2:
```css
#pos-7:checked ~ .game-world { transform: translateX(calc(var(--pos-width) * -6)); }
```

## Stage Subtitles

Below the title "NIBO'S WAY OUT", subtitles indicate the current stage:
- `.subtitle-s1` "The Factory" - shown on positions 1-6
- `.subtitle-s2` "The Jungle" - shown on positions 7-12
