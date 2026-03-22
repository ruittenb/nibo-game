---
name: prepare-for-publish
description: >
  Restores the game to its publishable state. Use this skill when the user asks
  to prepare for publish, release, or ship. During development, certain inputs
  are set to non-default states for testing (debug mode on, title screen skipped,
  player starting at a non-S1 position). This skill documents the exact changes
  needed to restore the publishable defaults.
---

# Prepare for Publish

> **File:** `index.src.html` — run `make minify` after changes.

During development, several inputs are toggled to non-default states for faster testing. Before publishing, restore these to their game-start defaults.

## Checklist

### 1. Debug toggle — unchecked

Find `id="debug-toggle"` and remove the `checked` attribute:

```html
<!-- Dev -->
<input type="checkbox" id="debug-toggle" accesskey="d" title="debug" checked>
<!-- Publish -->
<input type="checkbox" id="debug-toggle" accesskey="d" title="debug">
```

### 2. Title screen toggle — unchecked

Find `id="title-screen-toggle"` and remove the `checked` attribute. This ensures the title screen overlay is shown on game start:

```html
<!-- Dev -->
<input type="checkbox" id="title-screen-toggle" autofocus title="title screen" checked>
<!-- Publish -->
<input type="checkbox" id="title-screen-toggle" autofocus title="title screen">
```

### 3. Player start state

Ensure `checked` is on the correct radio button in each group. If a different radio in the group has `checked`, move it.

| Radio group | Expected `checked` |
|-------------|-------------------|
| `name="position"` | `id="pos-1"` |
| `name="level"` | `id="level-0"` |
| `name="layer"` | `id="layer-N"` |
| `name="lives"` | `id="lives-3"` |

### 4. Minify

```
make minify
```
