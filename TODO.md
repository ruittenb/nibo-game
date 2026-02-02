
 - fix landing gear of ship

 - animated coin still below mask: plan 'flying-coins' (problem: stacking context in sibling)

 - central pick up icon in nav-panel?

 - I would like to re-order the game state checkboxes. Which ones need to be in a specific order?

    - Required order (earlier → later in DOM):
    1. level-* radios must come before pos-* radios (many rules use #level-X:checked ~ #pos-Y:checked)
    2. pos-* radios must come before item checkboxes (rules like #pos-15:checked ~ #idcard-pickup:checked)
    3. toolbox-unlocked must come before wrench-pickup (rule: #toolbox-unlocked:checked ~ #wrench-pickup:checked)
    4. idcard-pickup must come before bolt-fixed (rule: #idcard-pickup:checked ~ #bolt-fixed:checked)
    5. bolt-fixed must come before flight-controls-used (rule: #bolt-fixed:checked ~ #flight-controls-used:not(:checked))
    6. All checkboxes must come before .game-world and UI elements they control

    - Summary: You can reorder checkboxes freely as long as you maintain these dependencies:
      - level radios → pos radios → item/state checkboxes → .game-world
    - Within the item checkboxes, you need: toolbox-unlocked before wrench-pickup, and idcard-pickup before bolt-fixed
       before flight-controls-used.

 - add video

 - afslanken met geneste regels?

  ┌─────────┬──────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┐
  │ Z-Index │        Source        │                               Elements                                              │
  ├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ -1      │ -1                   │ Grate grid pattern (:after pseudo)                                                  │
  ┝━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┥
  │ 0       │ 0                    │ Stage backgrounds (spacecraft-bg, factory-bg, jungle-bg, caves-bg)                  │
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
  ├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 9999    │ 9999                 │ Debug inputs (when visible)                                                         │
  ├─────────┼──────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 10000   │ 10000                │ Debug panel, title-screen-toggle                                                    │
  └─────────┴──────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┘







