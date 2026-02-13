# Adding Items, Loot, and Checkboxes

## Adding New Checkboxes

Every new boolean state (item pickups, unlocks, etc.) needs a checkbox. There are two categories:

- **Class-based**: loot checkboxes use `class="loot-checkbox"`, which handles bulk hiding and debug visibility automatically
- **ID-based**: item and state checkboxes (e.g., `#key-pickup`, `#tree-chopped`) need individual IDs added to two CSS rules

### Checklist for ID-based checkboxes

1. **Add the checkbox input** in the HTML inputs section (before `.game-world`):
   ```html
   <input type="checkbox" id="my-checkbox" title="my-checkbox">
   ```

2. **Add the ID to the hidden inputs rule** — find the CSS rule that starts with `.position-radio, .level-radio, .loot-checkbox, #key-pickup, ...` and add the new ID:
   ```css
   .position-radio, .level-radio, .layer-radio, .loot-checkbox,
   #key-pickup, ..., #my-checkbox {
       display: none;
   ```
   If you skip this step, the checkbox will be visible in the top-left corner of the play area.

3. **Add to debug toggle visibility rule** — find the `#debug-toggle:checked ~ ...` rule and add:
   ```css
   #debug-toggle:checked ~ #my-checkbox,
   ```

4. **Add debug position** — add a rule with a unique left offset:
   ```css
   #my-checkbox { top: 50px; left: XXXpx; }
   ```

### Checklist for class-based checkboxes (loot)

Only step 1 is needed. Use `class="loot-checkbox"`:
```html
<input type="checkbox" id="loot-SX-LY-PZ-pickup" class="loot-checkbox" title="coin">
```
The class selector handles hiding, debug visibility, and debug positioning automatically.

---

## Adding New Items

Items are pickable objects that go into the inventory (key, wrench, axe, battery, id card, scuba gear, torch).

### Checklist

#### 1. CSS variable for item color
Add near the other item color variables:
```css
--myitem-color: #RRGGBB;
```

#### 2. Checkbox
Add an ID-based checkbox (see checklist above):
```html
<input type="checkbox" id="myitem-pickup" title="myitem">
```
Must appear before `.game-world` in DOM order for sibling selectors to work.

#### 3. In-game element
Add in `.game-world` at the item's stage location:
```html
<span class="myitem-hover-area"></span>
<label for="myitem-pickup" class="myitem-in-game"><svg><use href="#myitem"/></svg></label>
<span class="tooltip myitem-tooltip">My Item</span>
```

CSS for the in-game element:
- Position at world location using `bottom` and `left` with CSS variables
- `pointer-events: none` by default
- Hover area at `z-index: var(--z-item-hover)`, item itself at `z-index: var(--z-items)`

#### 4. Adjacency rules (pulse + enable click)
When the player is adjacent and the item is not yet picked up:

```css
/* Hide hover area when player is adjacent (so label click works) */
#level-Y:checked ~ #pos-X:checked ~ .game-world .myitem-hover-area {
    display: none;
}
/* Show tooltip on item hover when player is adjacent */
#level-Y:checked ~ #pos-X:checked ~ #myitem-pickup:not(:checked) ~ .game-world .myitem-in-game:hover ~ .myitem-tooltip {
    opacity: 1;
}
/* Enable clicking + pulse animation */
#level-Y:checked ~ #pos-X:checked ~ #myitem-pickup:not(:checked) ~ .game-world .myitem-in-game {
    pointer-events: auto;
    cursor: pointer;
    animation: myitem-pulse 1s ease-in-out infinite;
}
```

If the item is reachable from multiple locations (e.g., a real location and a phantom location), add comma-separated selectors for each.

#### 5. Fly-to-inventory rule
When `#myitem-pickup:checked`, transition `bottom`/`left` to inventory position, fade `opacity` to 0:
```css
#myitem-pickup:checked ~ .game-world .myitem-in-game {
    bottom: calc(/* inventory Y position */);
    left: calc(/* inventory X position */);
    opacity: 0;
    transition: bottom 0.6s ease-in, left 0.6s ease-in, opacity 0.3s ease-in 0.5s;
}
```
- Slot position uses `--inv-slot-width * (offset)` where offset accounts for other items already in inventory
- This rule must come **after** the base positioning rule (CSS cascade: later rules override)

#### 6. Inventory icon
Inside `.inv-panel`, add the inventory representation:
```html
<span class="inventory-myitem"><svg><use href="#myitem"/></svg><span class="tooltip">My Item</span></span>
```

CSS: `visibility: hidden` by default, `visible` with `transition-delay` when picked up:
```css
#myitem-pickup:checked ~ .inv-panel .inventory-myitem {
    visibility: visible;
    transition-delay: 0.6s;
}
```

#### 7. Pickup animation keyframes
Add a `@keyframes myitem-pulse` in the consolidated animations section:
```css
@keyframes myitem-pulse {
    0%, 100% { filter: drop-shadow(0 0 4px var(--myitem-color)); }
    50% { filter: drop-shadow(0 0 12px var(--myitem-color)) drop-shadow(0 0 20px var(--myitem-color)); }
}
```

#### 8. Hide hover area and tooltip when picked up
```css
#myitem-pickup:checked ~ .game-world .myitem-hover-area,
#myitem-pickup:checked ~ .game-world .myitem-tooltip {
    display: none;
}
```

---

## Adding New Loot

Loot are collectibles (coins, gems, seashells) that fly to a counter rather than the inventory.

### Checklist

#### 1. Checkbox
Add a class-based checkbox (see checklist above):
```html
<input type="checkbox" id="loot-SX-LY-PZ-pickup" class="loot-checkbox" title="coin">
```

#### 2. Container in `.game-world`
```html
<div class="container coin loot-SX-LY-PZ">
    <label for="loot-SX-LY-PZ-pickup" class="loot-in-game"><svg><use href="#coin"/></svg></label>
    <span class="loot-hover-area"></span>
    <span class="tooltip">Gold Coin</span>
</div>
```
- `.container` wrapper with loot type class and location class
- The location class (e.g., `loot-S1-L0-P3`) controls positioning via CSS
- Label wraps the icon SVG, targeting the pickup checkbox

#### 3. Location positioning CSS
```css
.loot-SX-LY-PZ {
    bottom: calc(/* level height */);
    left: calc(var(--pos-offset) + var(--pos-width) * (pos - 1) - var(--item-offset));
}
```
For S2/S3 (top row), add `var(--stage-height) +` to the bottom.

#### 4. Fly-to-counter rule
When checked, transition `bottom`/`left` to the valuable counter position:
```css
#loot-SX-LY-PZ-pickup:checked ~ .game-world .loot-SX-LY-PZ {
    bottom: calc(/* counter Y position */);
    left: calc(/* counter X position */);
    opacity: 0;
    transition: bottom 0.6s ease-in, left 0.6s ease-in, opacity 0.3s ease-in 0.5s;
}
```

#### 5. Counter variable
The `--valuable-count` CSS variable increments via `:checked` selectors counting picked-up loot. If the new loot increases the maximum collectible count beyond the current digit range, add new frames to `@keyframes digit-roll`.
