---
name: bird-positioning
description: >
  Translates bird positioning data into CSS rules for the S5 bird in this CSS-only game.
  Use this skill automatically whenever the user provides bird data (layer/level/position/mode
  lines), asks to update bird coordinates, or mentions the S5 bird tracking rules.
  Also triggers when asked about --bird-level, --bird-pos, --bird-attacking variables,
  or the bird mapping CSS section. Process data immediately when provided — do not wait
  to be asked. Apply :is() optimizations when multiple layers share the same output.
---

# Bird Positioning (S5)

> ⚠️ **Always edit `index.src.html`**, never `index.html`. Run `make minify` after changes.

The bird in S5 tracks the player's location. For every reachable combination of layer + level + position in S5, a CSS rule sets the bird's coordinates and mode via CSS variables on `.game-world`.

**Selector order** mirrors DOM input order — always `level → layer → position`:
```css
#level-X:checked ~ #layer-Y:checked ~ #pos-Z:checked ~ .game-world
```
Never reverse layer and level — `#layer ~ #level` won't match.

---

## Input Data Format

The user provides bird data as whitespace-separated columns:

```
<player coordinates>  <player visual>  <bird location>  <bird mode>
```

Multiple entries on one line are separated by `%`:
```
N L4P16  P16  L3P16  attacking  %  N L4P17  P17  L4P15  flying
```

### Field reference

| Field | Example | Used for |
|-------|---------|----------|
| Player coordinates | `ζ L4P13` | CSS selector — `#level-4:checked ~ #layer-ζ:checked ~ #pos-13:checked` |
| Player visual location | `P13` | Informational only — skip in CSS |
| Bird location | `L2P15` | `--bird-level: 2; --bird-pos: 15;` |
| Bird mode | `flying` / `attacking` | `attacking` → add `--bird-attacking: 1;` — `flying` → omit (0 is the default) |

### Layer → selector mapping

| Data | CSS selector |
|------|-------------|
| `N` | `#layer-N` |
| `ζ` | `#layer-ζ` |
| `η` | `#layer-η` |
| `θ` | `#layer-θ` |

---

## Translation to CSS

**Flying (default)** — omit `--bird-attacking`:
```css
#level-4:checked ~ #layer-ζ:checked ~ #pos-13:checked ~ .game-world {
    --bird-level: 2; --bird-pos: 15;
}
```

**Attacking** — add `--bird-attacking: 1`:
```css
#level-4:checked ~ #layer-N:checked ~ #pos-16:checked ~ .game-world {
    --bird-level: 3; --bird-pos: 16; --bird-attacking: 1;
}
```

> ⚠️ Do **not** write `--bird-attacking: 0` — it's the `.game-world` default and only needs to be set when attacking.

---

## `:is()` Optimization

When multiple layers at the same level+position produce identical bird output, combine them.

**All 4 layers identical:**
```css
#level-4:checked ~ :is(#layer-N, #layer-ζ, #layer-η, #layer-θ):checked ~ #pos-13:checked ~ .game-world {
    --bird-level: 4; --bird-pos: 14;
}
```

**Two pairs, each pair identical:**
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

---

## Location in `index.src.html`

Find the section:
```css
/* ---- Bird mapping rules: player location → bird position + state ---- */
```

Rules are grouped by level with per-position comments:
```css
/* ---- L0 ---- */
/* L0-P13: bird at L3-P15 */
#level-0:checked ~ ...

/* ---- L1 ---- */
/* L1-P13: bird at L0-P13 (placeholder) */
...
```

---

## Workflow When Data Is Provided

1. **Process immediately** — don't wait to batch or confirm
2. Parse all entries (split on `%` for multi-entry lines)
3. Translate to CSS rules
4. Apply `:is()` groupings where layers share identical output
5. Compare against existing rules — only update what changed
6. Re-evaluate `:is()` groupings for any affected positions
