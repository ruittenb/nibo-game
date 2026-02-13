# Bird Positioning (S5)

## Overview

The bird in S5 tracks the player's location. For every combination of layer, level, and position the player can be at in S5, there is a CSS rule that sets the bird's coordinates and mode.

## Data Format

The user provides bird data as lines with these columns (separated by whitespace):

```
player coordinates;  player visual location;  bird location;  bird mode
```

Example entry:
```
ζ L4P13    P13    L2P15    flying
```

Multiple entries per line are separated by `%`:
```
N L4P16    P16    L3P16    attacking    %    N L4P17    P17    L4P15    flying    %    N L4P18    P18    L4P16    flying
```

### Fields

| Field | Description | Used for |
|-------|-------------|----------|
| Player coordinates | `<layer> L<level>P<pos>` | CSS selector: `#level-X:checked ~ #layer-Y:checked ~ #pos-Z:checked` |
| Player visual location | `P<n>` | Not used in CSS (informational only — shows where player appears visually) |
| Bird location | `L<bird-level>P<bird-pos>` | CSS variables: `--bird-level` and `--bird-pos` |
| Bird mode | `flying` or `attacking` | If `attacking`: add `--bird-attacking: 1;` — if `flying`: omit (0 is the default) |

### Layers

- `N` → `#layer-N`
- `ζ` → `#layer-ζ`
- `η` → `#layer-η`
- `θ` → `#layer-θ`

## Translation to CSS

Each entry becomes a CSS rule:

```css
#level-4:checked ~ #layer-ζ:checked ~ #pos-13:checked ~ .game-world {
    --bird-level: 2; --bird-pos: 15;
}
```

For attacking mode, add `--bird-attacking: 1`:

```css
#level-4:checked ~ #layer-N:checked ~ #pos-16:checked ~ .game-world {
    --bird-level: 3; --bird-pos: 16; --bird-attacking: 1;
}
```

**Important**: Do NOT set `--bird-attacking: 0` — it's the default from `.game-world` variables and only needs to be overridden when attacking.

## Optimization with `:is()`

When multiple layers at the same level+position produce the **same** bird output, combine them using `:is()`:

**All 4 layers identical:**
```css
#level-4:checked ~ :is(#layer-N, #layer-ζ, #layer-η, #layer-θ):checked ~ #pos-13:checked ~ .game-world {
    --bird-level: 4; --bird-pos: 14;
}
```

**Pairs identical:**
```css
#level-4:checked ~ :is(#layer-N, #layer-θ):checked ~ #pos-18:checked ~ .game-world { --bird-level: 4; --bird-pos: 16; }
#level-4:checked ~ :is(#layer-ζ, #layer-η):checked ~ #pos-18:checked ~ .game-world { --bird-level: 4; --bird-pos: 15; }
```

**All different — separate rules:**
```css
#level-3:checked ~ #layer-N:checked ~ #pos-13:checked ~ .game-world { --bird-level: 4; --bird-pos: 14; }
#level-3:checked ~ #layer-ζ:checked ~ #pos-13:checked ~ .game-world { --bird-level: 3; --bird-pos: 13; }
#level-3:checked ~ #layer-η:checked ~ #pos-13:checked ~ .game-world { --bird-level: 4; --bird-pos: 14; --bird-attacking: 1; }
#level-3:checked ~ #layer-θ:checked ~ #pos-13:checked ~ .game-world { --bird-level: 4; --bird-pos: 13; }
```

## Organization in index.html

The rules are located in the section starting with:
```css
/* ---- Bird mapping rules: player location → bird position + state ---- */
```

They are grouped by level with section comments and per-position comments:

```css
/* ---- L0 ---- */
/* L0-P13: bird at L3-P15 */
#level-0:checked ~ ...

/* ---- L1 ---- */
/* L1-P13: bird at L0-P13 (placeholder) */
...
```

When data is provided, **process it immediately** — update the CSS rules right away, don't wait to batch. Compare with existing rules and only change what's different. When a layer's values change, re-evaluate `:is()` groupings for the affected positions.

## Selector order

The DOM order of radio inputs is: level → layer → position. CSS sibling selectors must follow the same order:

```css
#level-X:checked ~ #layer-Y:checked ~ #pos-Z:checked ~ .game-world
```

Never reverse layer and level — `#layer ~ #level` won't match.
