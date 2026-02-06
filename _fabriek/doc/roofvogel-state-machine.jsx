import { useState, useCallback, useRef, useEffect } from "react";

// === CONSTANTS ===
const LEVELS = [0, 1, 2, 3, 4];
const POSITIONS = [13, 14, 15, 16, 17, 18];
const VARIANTS = ["normaal", "ζ", "η"];
const VARIANT_COLORS = {
  normaal: "#22d3ee",
  "ζ": "#a78bfa",
  "η": "#f472b6",
};
const VARIANT_SHORT = { normaal: "N", "ζ": "ζ", "η": "η" };

const COLORS = {
  bg: "#0a0e1a",
  surface: "#111827",
  surfaceLight: "#1e293b",
  border: "#2d3a4f",
  borderLight: "#3b4c66",
  text: "#e2e8f0",
  textDim: "#8892a8",
  textMuted: "#5a6478",
  accent: "#f59e0b",
  accentDim: "#b45309",
  bird: "#ef4444",
  birdDim: "#991b1b",
  danger: "#ef4444",
  safe: "#10b981",
  transition: "#3b82f6",
  transLevel: "#22d3ee",
  transPos: "#f59e0b",
  transVar: "#e879f9",
  gridLine: "#1a2235",
};

function stateKey(s) {
  return `${s.variant}-${s.level}-${s.position}`;
}

function displayLabel(s) {
  return `L${s.level} P${s.position}`;
}

function fullLabel(s) {
  if (s.variant === "normaal") return `L${s.level} P${s.position}`;
  return `L${s.level} P${s.position} [${s.variant}]`;
}

function shortLabel(s) {
  const v = s.variant === "normaal" ? "" : s.variant;
  return `${v}L${s.level}P${s.position}`;
}

function transitionAxis(from, to) {
  if (from.level !== to.level) return "level";
  if (from.position !== to.position) return "position";
  if (from.variant !== to.variant) return "variant";
  return "none";
}

function transitionColor(axis) {
  if (axis === "level") return COLORS.transLevel;
  if (axis === "position") return COLORS.transPos;
  if (axis === "variant") return COLORS.transVar;
  return COLORS.transition;
}

function transitionIcon(axis) {
  if (axis === "level") return "↕";
  if (axis === "position") return "↔";
  if (axis === "variant") return "⟳";
  return "→";
}

const GRID_SNAP = { x: 110, y: 100, offsetX: 80, offsetY: 80 };

function snapToGrid(x, y) {
  const col = Math.round((x - GRID_SNAP.offsetX) / GRID_SNAP.x);
  const row = Math.round((y - GRID_SNAP.offsetY) / GRID_SNAP.y);
  return {
    x: GRID_SNAP.offsetX + col * GRID_SNAP.x,
    y: GRID_SNAP.offsetY + row * GRID_SNAP.y,
  };
}

const buildInitialStates = () => {
  const out = [];
  for (const l of LEVELS) {
    for (const p of POSITIONS) {
      out.push({
        id: `normaal-${l}-${p}`,
        level: l,
        position: p,
        variant: "normaal",
        birdLevel: null,
        birdPosition: null,
        birdMode: "flying",
      });
    }
  }
  return out;
};

export default function StateMachineEditor() {
  const [states, setStates] = useState(buildInitialStates);
  const [transitions, setTransitions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [activeTab, setActiveTab] = useState("graph");
  const [showCSS, setShowCSS] = useState(false);
  const [variantFilter, setVariantFilter] = useState("all");
  const [graphPos, setGraphPos] = useState({});
  const [dragging, setDragging] = useState(null);
  const [shiftDrag, setShiftDrag] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [hoveredId, setHoveredId] = useState(null);
  const svgRef = useRef(null);

  const selected = states.find((s) => s.id === selectedId);

  useEffect(() => {
    const newPos = {};
    const variantOffsetY = { normaal: 0, "ζ": 600, "η": 1200 };
    states.forEach((s) => {
      if (!newPos[s.id]) {
        const col = s.position - 13;
        const row = 4 - s.level;
        const oy = variantOffsetY[s.variant] || 0;
        newPos[s.id] = {
          x: 80 + col * 110,
          y: 80 + row * 100 + oy,
        };
      }
    });
    setGraphPos((prev) => {
      const merged = { ...prev };
      for (const k in newPos) {
        if (!merged[k]) merged[k] = newPos[k];
      }
      return merged;
    });
  }, [states]);

  const addVariantState = useCallback((level, position, variant) => {
    const id = `${variant}-${level}-${position}`;
    if (states.find((s) => s.id === id)) return;
    setStates((prev) => [
      ...prev,
      { id, level, position, variant, birdLevel: null, birdPosition: null, birdMode: "flying" },
    ]);
  }, [states]);

  const addFullVariant = useCallback((variant) => {
    const newStates = [];
    for (const l of LEVELS) {
      for (const p of POSITIONS) {
        const id = `${variant}-${l}-${p}`;
        if (!states.find((s) => s.id === id)) {
          newStates.push({ id, level: l, position: p, variant, birdLevel: null, birdPosition: null, birdMode: "flying" });
        }
      }
    }
    if (newStates.length > 0) setStates((prev) => [...prev, ...newStates]);
  }, [states]);

  const removeState = useCallback((id) => {
    const s = states.find((st) => st.id === id);
    if (s && s.variant === "normaal") return;
    setStates((prev) => prev.filter((st) => st.id !== id));
    setTransitions((prev) => prev.filter((t) => t.from !== id && t.to !== id));
    if (selectedId === id) setSelectedId(null);
  }, [selectedId, states]);

  const updateState = useCallback((id, updates) => {
    setStates((prev) => prev.map((s) => (s.id === id ? { ...s, ...updates } : s)));
  }, []);

  const addTransition = useCallback((fromId, toId, label) => {
    if (fromId === toId) return;
    if (transitions.find((t) => t.from === fromId && t.to === toId)) return;
    const from = states.find((s) => s.id === fromId);
    const to = states.find((s) => s.id === toId);
    if (!from || !to) return;
    const axis = transitionAxis(from, to);
    setTransitions((prev) => [
      ...prev,
      { id: `${fromId}→${toId}`, from: fromId, to: toId, label: label || transitionIcon(axis), axis },
    ]);
  }, [transitions, states]);

  const removeTransition = useCallback((id) => {
    setTransitions((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const getSvgPoint = useCallback((e) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const svg = svgRef.current;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
    return { x: svgP.x, y: svgP.y };
  }, []);

  const handleMouseMove = useCallback((e) => {
    const p = getSvgPoint(e);
    setMousePos(p);
    if (dragging) {
      setGraphPos((prev) => ({ ...prev, [dragging]: { x: p.x, y: p.y } }));
    }
  }, [dragging, getSvgPoint]);

  const handleNodeMouseDown = (e, id) => {
    e.stopPropagation();
    if (e.shiftKey) setShiftDrag(id);
    else setDragging(id);
  };

  const handleNodeMouseUp = (e, targetId) => {
    e.stopPropagation();
    if (shiftDrag && targetId && shiftDrag !== targetId) addTransition(shiftDrag, targetId);
    if (dragging) {
      // Snap to grid
      setGraphPos((prev) => {
        const pos = prev[dragging];
        if (!pos) return prev;
        return { ...prev, [dragging]: snapToGrid(pos.x, pos.y) };
      });
    }
    setShiftDrag(null);
    setDragging(null);
  };

  const handleSvgMouseUp = () => {
    if (dragging) {
      setGraphPos((prev) => {
        const pos = prev[dragging];
        if (!pos) return prev;
        return { ...prev, [dragging]: snapToGrid(pos.x, pos.y) };
      });
    }
    setShiftDrag(null);
    setDragging(null);
  };

  const filtered = states.filter((s) => {
    if (variantFilter === "all") return true;
    return s.variant === variantFilter;
  });

  const generateCSS = () => {
    const birdStates = states.filter((s) => s.birdLevel !== null && s.birdPosition !== null);
    let css = `/* ══════════════════════════════════════════════════════\n`;
    css += `   ROOFVOGEL NPC — GEGENEREERDE CSS\n`;
    css += `   Drie-assen model: Level × Positie × Variant\n`;
    css += `   States met vogel: ${birdStates.length} / ${states.length}\n`;
    css += `   Transitions: ${transitions.length}\n`;
    css += `   ══════════════════════════════════════════════════════ */\n\n`;
    css += `/* --- Radiogroepen (verborgen) --- */\n`;
    css += `input[name="level"],\ninput[name="position"],\ninput[name="variant"] { display: none; }\n\n`;
    css += `/* --- Vogel basis --- */\n.bird { display: none; position: absolute; }\n\n`;
    css += `/* --- Vogel positionering per state --- */\n`;

    birdStates.forEach((s) => {
      const levelId = `level-${s.level}`;
      const posId = `pos-${s.position}`;
      const varId = `var-${s.variant}`;
      const gridCol = s.birdPosition - 12;
      const gridRow = 5 - s.birdLevel;
      css += `/* ${fullLabel(s)} → vogel op L${s.birdLevel} P${s.birdPosition} ${s.birdMode === "grabbing" ? "⚠ GEVAAR" : ""} */\n`;
      css += `#${levelId}:checked ~ #${posId}:checked ~ #${varId}:checked ~ .game-board .bird {\n`;
      css += `  display: block;\n  grid-column: ${gridCol};\n  grid-row: ${gridRow};\n`;
      if (s.birdMode === "grabbing") css += `  animation: bird-grab 0.3s ease-in-out;\n`;
      css += `}\n\n`;
    });

    const varTransitions = transitions.filter((t) => t.axis === "variant");
    if (varTransitions.length > 0) {
      css += `/* --- Variant-wisselende navigatielabels --- */\n`;
      varTransitions.forEach((t) => {
        const from = states.find((s) => s.id === t.from);
        const to = states.find((s) => s.id === t.to);
        if (!from || !to) return;
        css += `/* ${shortLabel(from)} ⟳ ${shortLabel(to)} — onzichtbaar voor speler */\n`;
        css += `/* Label verandert variant-radio van "${from.variant}" naar "${to.variant}" */\n\n`;
      });
    }

    css += `@keyframes bird-grab {\n  0% { transform: scale(1); }\n  50% { transform: scale(1.3) translateY(10px); }\n  100% { transform: scale(1); }\n}\n`;
    return css;
  };

  return (
    <div style={{
      background: COLORS.bg, color: COLORS.text, height: "100vh",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace",
      fontSize: 13, display: "flex", flexDirection: "column", overflow: "hidden",
    }}>
      {/* HEADER */}
      <div style={{
        padding: "12px 20px", borderBottom: `1px solid ${COLORS.border}`,
        display: "flex", alignItems: "center", gap: 14, background: COLORS.surface, flexShrink: 0,
      }}>
        <div style={{ fontSize: 22 }}>🦅</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 14, letterSpacing: "0.06em" }}>ROOFVOGEL STATE MACHINE</div>
          <div style={{ color: COLORS.textDim, fontSize: 10, marginTop: 2, display: "flex", gap: 12 }}>
            <span>{states.length} states</span><span>·</span>
            <span>{transitions.length} transitions</span><span>·</span>
            <span style={{ color: VARIANT_COLORS["ζ"] }}>{states.filter((s) => s.variant === "ζ").length} ζ</span>
            <span style={{ color: VARIANT_COLORS["η"] }}>{states.filter((s) => s.variant === "η").length} η</span>
          </div>
        </div>
        {VARIANTS.filter((v) => v !== "normaal").map((v) => {
          const count = states.filter((s) => s.variant === v).length;
          return (
            <button key={v} onClick={() => addFullVariant(v)}
              title={`Voeg alle ${v}-varianten toe (30 states)`}
              style={{
                padding: "5px 12px", background: count > 0 ? "transparent" : VARIANT_COLORS[v] + "22",
                color: VARIANT_COLORS[v], border: `1px solid ${VARIANT_COLORS[v]}55`,
                borderRadius: 4, cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600,
                opacity: count >= 30 ? 0.4 : 1,
              }}>
              {count >= 30 ? `${v} ✓` : `+ ${v} laag`}
            </button>
          );
        })}
        <button onClick={() => setShowCSS(true)} style={{
          padding: "5px 14px", background: "transparent", color: COLORS.accent,
          border: `1px solid ${COLORS.accent}`, borderRadius: 4, cursor: "pointer",
          fontFamily: "inherit", fontSize: 11, fontWeight: 600,
        }}>
          ⟨/⟩ CSS
        </button>
      </div>

      {/* CSS MODAL */}
      {showCSS && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 1000,
          display: "flex", alignItems: "center", justifyContent: "center", padding: 32,
        }} onClick={() => setShowCSS(false)}>
          <div style={{
            background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 8,
            width: "100%", maxWidth: 800, maxHeight: "85vh", overflow: "auto", padding: 20,
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontWeight: 700, fontSize: 13, color: COLORS.accent }}>GEGENEREERDE CSS</span>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => navigator.clipboard?.writeText(generateCSS())} style={{
                  padding: "4px 10px", background: COLORS.accentDim, color: COLORS.text,
                  border: "none", borderRadius: 3, cursor: "pointer", fontFamily: "inherit", fontSize: 10,
                }}>📋 Kopieer</button>
                <button onClick={() => setShowCSS(false)} style={{
                  padding: "4px 10px", background: COLORS.surfaceLight, color: COLORS.textDim,
                  border: "none", borderRadius: 3, cursor: "pointer", fontFamily: "inherit", fontSize: 10,
                }}>✕</button>
              </div>
            </div>
            <pre style={{
              background: COLORS.bg, padding: 16, borderRadius: 4, overflow: "auto",
              fontSize: 11, lineHeight: 1.7, color: COLORS.textDim, border: `1px solid ${COLORS.border}`,
            }}>{generateCSS()}</pre>
          </div>
        </div>
      )}

      {/* TABS */}
      <div style={{
        display: "flex", borderBottom: `1px solid ${COLORS.border}`,
        background: COLORS.surface, flexShrink: 0,
      }}>
        {[
          { id: "graph", label: "◉ GRAPH" },
          { id: "table", label: "▤ TABEL" },
          { id: "preview", label: "▶ PREVIEW" },
        ].map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: "9px 22px",
            background: activeTab === tab.id ? COLORS.bg : "transparent",
            color: activeTab === tab.id ? COLORS.accent : COLORS.textDim,
            border: "none",
            borderBottom: activeTab === tab.id ? `2px solid ${COLORS.accent}` : "2px solid transparent",
            cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600, letterSpacing: "0.05em",
          }}>{tab.label}</button>
        ))}
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 4, paddingRight: 16 }}>
          <span style={{ color: COLORS.textMuted, fontSize: 9, marginRight: 4 }}>FILTER:</span>
          {["all", ...VARIANTS].map((v) => (
            <button key={v} onClick={() => setVariantFilter(v)} style={{
              padding: "3px 8px",
              background: variantFilter === v ? (v === "all" ? COLORS.borderLight : VARIANT_COLORS[v] + "33") : "transparent",
              color: v === "all" ? COLORS.textDim : VARIANT_COLORS[v] || COLORS.textDim,
              border: `1px solid ${variantFilter === v ? (v === "all" ? COLORS.borderLight : VARIANT_COLORS[v] + "66") : "transparent"}`,
              borderRadius: 3, cursor: "pointer", fontFamily: "inherit", fontSize: 10,
            }}>{v === "all" ? "Alle" : v === "normaal" ? "N" : v}</button>
          ))}
        </div>
      </div>

      {/* MAIN */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>

          {/* GRAPH TAB */}
          {activeTab === "graph" && (() => {
            // Compute SVG height from node positions
            const allY = filtered.map((s) => graphPos[s.id]?.y).filter(Boolean);
            const maxY = allY.length > 0 ? Math.max(...allY) + 80 : 600;
            const svgHeight = Math.max(maxY, 600);
            return (
            <div style={{ height: "100%", position: "relative", overflow: "hidden" }}>
              <div style={{
                position: "absolute", top: 10, left: 10, zIndex: 10,
                background: COLORS.surface + "ee", padding: "5px 10px",
                borderRadius: 5, border: `1px solid ${COLORS.border}`,
                color: COLORS.textMuted, fontSize: 9, lineHeight: 1.6,
              }}>
                Sleep = verplaats (snapt naar grid) · Shift+sleep = transitie · Klik = selecteer<br />
                <span style={{ color: COLORS.transLevel }}>●</span> level{" "}
                <span style={{ color: COLORS.transPos }}>●</span> positie{" "}
                <span style={{ color: COLORS.transVar }}>●</span> variant
              </div>

              <div style={{ height: "100%", overflow: "auto" }}>
              <svg ref={svgRef} style={{ width: "100%", minHeight: svgHeight, display: "block", background: COLORS.bg }}
                onMouseMove={handleMouseMove} onMouseUp={handleSvgMouseUp}
                onMouseLeave={() => { setDragging(null); setShiftDrag(null); }}>
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke={COLORS.gridLine} strokeWidth="0.5" />
                  </pattern>
                  {["level", "position", "variant"].map((axis) => (
                    <marker key={axis} id={`arrow-${axis}`} markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill={transitionColor(axis)} opacity="0.8" />
                    </marker>
                  ))}
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />

                {/* Variant group boxes */}
                {VARIANTS.map((v) => {
                  const vStates = filtered.filter((s) => s.variant === v);
                  if (vStates.length === 0) return null;
                  const positions = vStates.map((s) => graphPos[s.id]).filter(Boolean);
                  if (positions.length === 0) return null;
                  const minX = Math.min(...positions.map((p) => p.x)) - 40;
                  const minY = Math.min(...positions.map((p) => p.y)) - 40;
                  const maxX = Math.max(...positions.map((p) => p.x)) + 40;
                  const maxY = Math.max(...positions.map((p) => p.y)) + 40;
                  return (
                    <g key={`group-${v}`}>
                      <rect x={minX} y={minY} width={maxX - minX} height={maxY - minY} rx={8}
                        fill={VARIANT_COLORS[v] + "08"} stroke={VARIANT_COLORS[v] + "20"}
                        strokeWidth={1} strokeDasharray="6 4" />
                      <text x={minX + 8} y={minY + 14} fill={VARIANT_COLORS[v]}
                        fontSize={10} fontFamily="inherit" fontWeight={700} opacity={0.5}>
                        {v === "normaal" ? "NORMAAL" : `VARIANT ${v.toUpperCase()}`}
                      </text>
                    </g>
                  );
                })}

                {/* Transitions */}
                {transitions.map((t) => {
                  const fp = graphPos[t.from];
                  const tp = graphPos[t.to];
                  const fromS = filtered.find((s) => s.id === t.from);
                  const toS = filtered.find((s) => s.id === t.to);
                  if (!fp || !tp || !fromS || !toS) return null;
                  const dx = tp.x - fp.x; const dy = tp.y - fp.y;
                  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                  const nx = dx / dist; const ny = dy / dist;
                  const r = 26;
                  const sx = fp.x + nx * r; const sy = fp.y + ny * r;
                  const ex = tp.x - nx * r; const ey = tp.y - ny * r;
                  const cx = (sx + ex) / 2 - ny * 18; const cy = (sy + ey) / 2 + nx * 18;
                  const col = transitionColor(t.axis);
                  return (
                    <g key={t.id} style={{ cursor: "pointer" }} onClick={() => removeTransition(t.id)}>
                      <path d={`M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}`}
                        fill="none" stroke={col} strokeWidth={t.axis === "variant" ? 2.5 : 1.5}
                        opacity={0.6} strokeDasharray={t.axis === "variant" ? "6 3" : "none"}
                        markerEnd={`url(#arrow-${t.axis})`} />
                      <text x={cx} y={cy - 5} textAnchor="middle" fill={col}
                        fontSize={9} fontFamily="inherit" fontWeight={600} opacity={0.8}>
                        {t.axis === "variant" ? "⟳" : t.label}
                      </text>
                    </g>
                  );
                })}

                {/* Shift-drag line */}
                {shiftDrag && graphPos[shiftDrag] && (
                  <line x1={graphPos[shiftDrag].x} y1={graphPos[shiftDrag].y}
                    x2={mousePos.x} y2={mousePos.y}
                    stroke={COLORS.accent} strokeWidth={2} strokeDasharray="4 4" opacity={0.6} />
                )}

                {/* State nodes */}
                {filtered.map((state) => {
                  const pos = graphPos[state.id];
                  if (!pos) return null;
                  const isSel = selectedId === state.id;
                  const isHov = hoveredId === state.id;
                  const hasBird = state.birdLevel !== null && state.birdPosition !== null;
                  const vColor = VARIANT_COLORS[state.variant];
                  const r = isSel ? 26 : 23;
                  return (
                    <g key={state.id} style={{ cursor: dragging ? "grabbing" : "grab" }}
                      onMouseDown={(e) => handleNodeMouseDown(e, state.id)}
                      onMouseUp={(e) => handleNodeMouseUp(e, state.id)}
                      onClick={(e) => { e.stopPropagation(); if (!dragging) setSelectedId(state.id); }}
                      onMouseEnter={() => setHoveredId(state.id)}
                      onMouseLeave={() => setHoveredId(null)}>
                      {(isSel || isHov) && <circle cx={pos.x} cy={pos.y} r={r + 8} fill={vColor} opacity={0.1} />}
                      {hasBird && (
                        <circle cx={pos.x} cy={pos.y} r={r + 3} fill="none"
                          stroke={state.birdMode === "grabbing" ? COLORS.danger : COLORS.bird}
                          strokeWidth={2} strokeDasharray={state.birdMode === "grabbing" ? "none" : "3 2"} opacity={0.7} />
                      )}
                      <circle cx={pos.x} cy={pos.y} r={r} fill={COLORS.surface}
                        stroke={isSel ? COLORS.accent : vColor} strokeWidth={isSel ? 2.5 : 1.5} />
                      {state.variant !== "normaal" && (
                        <circle cx={pos.x} cy={pos.y} r={r - 4} fill="none"
                          stroke={vColor} strokeWidth={0.5} strokeDasharray="2 2" opacity={0.4} />
                      )}
                      <text x={pos.x} y={pos.y - 4} textAnchor="middle" fill={vColor}
                        fontSize={9} fontFamily="inherit" fontWeight={700}>
                        L{state.level}P{state.position}
                      </text>
                      <text x={pos.x} y={pos.y + 8} textAnchor="middle" fill={vColor}
                        fontSize={8} fontFamily="inherit" opacity={0.6}>
                        {VARIANT_SHORT[state.variant]}
                      </text>
                      {hasBird && <text x={pos.x + r - 4} y={pos.y - r + 6} fontSize={11} textAnchor="middle">🦅</text>}
                    </g>
                  );
                })}
              </svg>
              </div>
            </div>
            );
          })()}

          {/* TABLE TAB */}
          {activeTab === "table" && (
            <div style={{ height: "100%", overflow: "auto", padding: 16 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ color: COLORS.textDim, fontSize: 10, fontWeight: 600 }}>INDIVIDUELE VARIANT STATE:</span>
                {VARIANTS.filter((v) => v !== "normaal").map((v) => (
                  <button key={v} onClick={() => {
                    const input = prompt(`Level (0-4) en Positie (13-18) voor ${v}-variant, bijv. "2 15":`);
                    if (input) {
                      const [l, p] = input.split(/[\s,]+/).map(Number);
                      if (LEVELS.includes(l) && POSITIONS.includes(p)) addVariantState(l, p, v);
                      else alert("Ongeldig! Level 0-4, Positie 13-18");
                    }
                  }} style={{
                    padding: "3px 10px", background: VARIANT_COLORS[v] + "22",
                    color: VARIANT_COLORS[v], border: `1px solid ${VARIANT_COLORS[v]}44`,
                    borderRadius: 3, cursor: "pointer", fontFamily: "inherit", fontSize: 10,
                  }}>+ {v} state</button>
                ))}
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                    {["State", "Variant", "Speler ziet", "🦅 Level", "🦅 Pos", "🦅 Mode", ""].map((h, i) => (
                      <th key={i} style={{
                        padding: "7px 10px", textAlign: "left", color: COLORS.textDim,
                        fontWeight: 600, fontSize: 9, letterSpacing: "0.08em", textTransform: "uppercase",
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((state) => {
                    const vCol = VARIANT_COLORS[state.variant];
                    return (
                      <tr key={state.id} onClick={() => setSelectedId(state.id)} style={{
                        borderBottom: `1px solid ${COLORS.border}`,
                        background: selectedId === state.id ? COLORS.surfaceLight : "transparent", cursor: "pointer",
                      }}>
                        <td style={{ padding: "5px 10px", fontWeight: 600, color: vCol }}>{shortLabel(state)}</td>
                        <td style={{ padding: "5px 10px" }}>
                          <span style={{
                            display: "inline-block", padding: "1px 6px", borderRadius: 3,
                            background: vCol + "22", color: vCol, fontSize: 10,
                          }}>{state.variant}</span>
                        </td>
                        <td style={{ padding: "5px 10px", color: COLORS.textDim }}>{displayLabel(state)}</td>
                        <td style={{ padding: "5px 10px" }}>
                          <select value={state.birdLevel ?? ""}
                            onChange={(e) => updateState(state.id, { birdLevel: e.target.value === "" ? null : +e.target.value })}
                            style={{
                              background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`,
                              padding: "2px 5px", borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                            }}>
                            <option value="">–</option>
                            {LEVELS.map((l) => <option key={l} value={l}>L{l}</option>)}
                          </select>
                        </td>
                        <td style={{ padding: "5px 10px" }}>
                          <select value={state.birdPosition ?? ""}
                            onChange={(e) => updateState(state.id, { birdPosition: e.target.value === "" ? null : +e.target.value })}
                            style={{
                              background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`,
                              padding: "2px 5px", borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                            }}>
                            <option value="">–</option>
                            {POSITIONS.map((p) => <option key={p} value={p}>P{p}</option>)}
                          </select>
                        </td>
                        <td style={{ padding: "5px 10px" }}>
                          <select value={state.birdMode}
                            onChange={(e) => updateState(state.id, { birdMode: e.target.value })}
                            style={{
                              background: COLORS.bg,
                              color: state.birdMode === "grabbing" ? COLORS.danger : COLORS.text,
                              border: `1px solid ${state.birdMode === "grabbing" ? COLORS.danger : COLORS.border}`,
                              padding: "2px 5px", borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                            }}>
                            <option value="flying">🦅 Vliegend</option>
                            <option value="attacking">💨 Aanvallend</option>
                            <option value="grabbing">☠️ Grijpend</option>
                          </select>
                        </td>
                        <td style={{ padding: "5px 10px" }}>
                          {state.variant !== "normaal" && (
                            <button onClick={(e) => { e.stopPropagation(); removeState(state.id); }} style={{
                              background: "transparent", color: COLORS.textMuted, border: "none",
                              cursor: "pointer", fontFamily: "inherit", fontSize: 10,
                            }}>✕</button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Transitions table */}
              <div style={{ marginTop: 28 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <span style={{ fontWeight: 700, fontSize: 11, color: COLORS.transition, letterSpacing: "0.05em" }}>TRANSITIONS</span>
                  <button onClick={() => {
                    const from = prompt("Van state (bijv. L2P15 of ζL2P15):");
                    const to = prompt("Naar state (bijv. L2P16 of ηL2P15):");
                    if (from && to) {
                      const norm = (x) => x.toLowerCase().replace(/\s/g, "");
                      const fs = states.find((s) => norm(shortLabel(s)) === norm(from));
                      const ts = states.find((s) => norm(shortLabel(s)) === norm(to));
                      if (fs && ts) addTransition(fs.id, ts.id);
                      else alert("State niet gevonden! Formaat: L2P15 of ζL2P15");
                    }
                  }} style={{
                    padding: "4px 12px", background: COLORS.transition, color: "#fff",
                    border: "none", borderRadius: 3, cursor: "pointer", fontFamily: "inherit", fontSize: 10, fontWeight: 600,
                  }}>+ TRANSITION</button>
                </div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr style={{ borderBottom: `2px solid ${COLORS.border}` }}>
                      {["Van", "", "Naar", "As", "Speler ziet", "🦅 effect", ""].map((h, i) => (
                        <th key={i} style={{
                          padding: "7px 10px", textAlign: "left", color: COLORS.textDim, fontWeight: 600, fontSize: 9,
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {transitions.map((t) => {
                      const from = states.find((s) => s.id === t.from);
                      const to = states.find((s) => s.id === t.to);
                      if (!from || !to) return null;
                      const col = transitionColor(t.axis);
                      const birdChanged = (from.birdLevel !== to.birdLevel) || (from.birdPosition !== to.birdPosition);
                      return (
                        <tr key={t.id} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                          <td style={{ padding: "5px 10px", color: VARIANT_COLORS[from.variant], fontWeight: 600 }}>{shortLabel(from)}</td>
                          <td style={{ padding: "5px 10px", color: col, fontWeight: 700 }}>{transitionIcon(t.axis)}</td>
                          <td style={{ padding: "5px 10px", color: VARIANT_COLORS[to.variant], fontWeight: 600 }}>{shortLabel(to)}</td>
                          <td style={{ padding: "5px 10px" }}>
                            <span style={{
                              padding: "1px 6px", borderRadius: 3, background: col + "22", color: col, fontSize: 9, fontWeight: 600,
                            }}>{t.axis}</span>
                          </td>
                          <td style={{ padding: "5px 10px", color: COLORS.textDim }}>
                            {displayLabel(from)} → {displayLabel(to)}
                            {t.axis === "variant" && (
                              <span style={{ color: COLORS.transVar, marginLeft: 6, fontSize: 9 }}>(onzichtbaar!)</span>
                            )}
                          </td>
                          <td style={{ padding: "5px 10px" }}>
                            {birdChanged ? (
                              <span style={{ color: COLORS.bird, fontSize: 10 }}>
                                L{from.birdLevel ?? "?"}P{from.birdPosition ?? "?"} → L{to.birdLevel ?? "?"}P{to.birdPosition ?? "?"}
                              </span>
                            ) : <span style={{ color: COLORS.textMuted }}>–</span>}
                          </td>
                          <td style={{ padding: "5px 10px" }}>
                            <button onClick={() => removeTransition(t.id)} style={{
                              background: "transparent", color: COLORS.textMuted, border: "none",
                              cursor: "pointer", fontFamily: "inherit", fontSize: 10,
                            }}>✕</button>
                          </td>
                        </tr>
                      );
                    })}
                    {transitions.length === 0 && (
                      <tr><td colSpan={7} style={{ padding: 20, color: COLORS.textMuted, textAlign: "center" }}>
                        Nog geen transitions. Voeg ze toe hierboven of shift+sleep in de graph.
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* PREVIEW TAB */}
          {activeTab === "preview" && (() => {
            // Precompute: for each grid cell, which states place a bird here?
            const birdMap = {};
            states.forEach((s) => {
              if (s.birdLevel !== null && s.birdPosition !== null) {
                const key = `${s.birdLevel}-${s.birdPosition}`;
                if (!birdMap[key]) birdMap[key] = [];
                birdMap[key].push(s);
              }
            });

            // Precompute: for each grid cell, which states have the player here?
            const playerMap = {};
            states.forEach((s) => {
              const key = `${s.level}-${s.position}`;
              if (!playerMap[key]) playerMap[key] = [];
              playerMap[key].push(s);
            });

            return (
            <div style={{
              height: "100%", display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", gap: 20, padding: 24,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{ color: COLORS.textDim, fontSize: 11, fontWeight: 600, letterSpacing: "0.08em" }}>
                  STAGE PREVIEW
                </div>
                {selected && (
                  <span style={{
                    color: VARIANT_COLORS[selected.variant], fontSize: 11,
                    padding: "2px 10px", background: VARIANT_COLORS[selected.variant] + "18",
                    borderRadius: 4, border: `1px solid ${VARIANT_COLORS[selected.variant]}44`,
                  }}>
                    {fullLabel(selected)}
                  </span>
                )}
              </div>

              <div style={{
                display: "grid", gridTemplateColumns: `40px repeat(6, 80px)`,
                gridTemplateRows: `repeat(5, 64px) 24px`,
                gap: 2, background: COLORS.border, padding: 2, borderRadius: 6,
              }}>
                {/* Level labels */}
                {Array.from({ length: 5 }).map((_, row) => {
                  const level = 4 - row;
                  return (
                    <div key={`ll-${level}`} style={{
                      gridColumn: 1, gridRow: row + 1,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: COLORS.textMuted, fontSize: 10, fontWeight: 600, background: COLORS.surface,
                    }}>L{level}</div>
                  );
                })}
                {/* Position labels */}
                {POSITIONS.map((p, col) => (
                  <div key={`pl-${p}`} style={{
                    gridColumn: col + 2, gridRow: 6,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: COLORS.textMuted, fontSize: 10, fontWeight: 600, background: COLORS.surface,
                  }}>P{p}</div>
                ))}

                {/* Grid cells */}
                {Array.from({ length: 5 }).map((_, row) =>
                  Array.from({ length: 6 }).map((_, col) => {
                    const level = 4 - row;
                    const pos = col + 13;
                    const cellKey = `${level}-${pos}`;

                    // Birds at this cell from ANY state
                    const birdsHere = birdMap[cellKey] || [];
                    // Group by variant
                    const birdsByVariant = {};
                    birdsHere.forEach((s) => {
                      if (!birdsByVariant[s.variant]) birdsByVariant[s.variant] = [];
                      birdsByVariant[s.variant].push(s);
                    });
                    const birdVariants = Object.keys(birdsByVariant);

                    // Is the selected state's player here?
                    const isPlayer = selected && selected.level === level && selected.position === pos;
                    // Is the selected state's bird here?
                    const isActiveBird = selected && selected.birdLevel === level && selected.birdPosition === pos;
                    const isDanger = isActiveBird && selected.birdMode === "grabbing";
                    const isSameSquare = isPlayer && isActiveBird;

                    // Any grabbing birds here?
                    const hasGrabbingBird = birdsHere.some((s) => s.birdMode === "grabbing");

                    // Player variants at this cell
                    const playersHere = playerMap[cellKey] || [];
                    const playerVariantCount = new Set(playersHere.map((s) => s.variant)).size;

                    return (
                      <div key={`${row}-${col}`} style={{
                        gridColumn: col + 2, gridRow: row + 1,
                        background: isDanger ? `${COLORS.danger}30`
                          : isSameSquare ? `${COLORS.danger}20`
                          : isActiveBird ? `${COLORS.bird}18`
                          : isPlayer ? `${VARIANT_COLORS[selected.variant]}18`
                          : birdsHere.length > 0 ? `${COLORS.bird}08`
                          : COLORS.bg,
                        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                        gap: 2,
                        border: isPlayer ? `2px solid ${VARIANT_COLORS[selected.variant]}`
                          : isActiveBird ? `2px solid ${COLORS.bird}`
                          : hasGrabbingBird ? `1px solid ${COLORS.danger}66`
                          : birdsHere.length > 0 ? `1px solid ${COLORS.bird}33`
                          : `1px solid ${COLORS.border}`,
                        borderRadius: 3, position: "relative",
                        cursor: birdsHere.length > 0 ? "pointer" : "default",
                      }}>
                        {/* Active player + bird */}
                        <div style={{ display: "flex", gap: 2, fontSize: 14, lineHeight: 1 }}>
                          {isPlayer && <span>🧍</span>}
                          {isActiveBird && <span>{isDanger ? "🦅☠️" : "🦅"}</span>}
                        </div>

                        {/* Bird variant dots — always visible */}
                        {birdVariants.length > 0 && (
                          <div style={{
                            display: "flex", gap: 2, flexWrap: "wrap", justifyContent: "center",
                            maxWidth: 70,
                          }}>
                            {birdVariants.map((v) => {
                              const count = birdsByVariant[v].length;
                              const hasGrab = birdsByVariant[v].some((s) => s.birdMode === "grabbing");
                              const hasAttack = birdsByVariant[v].some((s) => s.birdMode === "attacking");
                              const isActiveVariant = selected && selected.variant === v
                                && selected.birdLevel === level && selected.birdPosition === pos;
                              return (
                                <div key={v} title={`${count}× ${v} vogel${count > 1 ? "s" : ""} hier${hasGrab ? " (GEVAAR!)" : ""}`}
                                  style={{
                                    display: "flex", alignItems: "center", gap: 2,
                                    padding: "1px 4px", borderRadius: 3,
                                    background: isActiveVariant ? VARIANT_COLORS[v] + "44" : VARIANT_COLORS[v] + "18",
                                    border: isActiveVariant ? `1px solid ${VARIANT_COLORS[v]}` : `1px solid ${VARIANT_COLORS[v]}33`,
                                  }}>
                                  <span style={{ fontSize: 8 }}>
                                    {hasGrab ? "☠️" : hasAttack ? "💨" : "🦅"}
                                  </span>
                                  <span style={{
                                    fontSize: 7, color: VARIANT_COLORS[v], fontWeight: 700,
                                  }}>
                                    {VARIANT_SHORT[v]}{count > 1 ? `×${count}` : ""}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {/* Player variant indicator */}
                        {playerVariantCount > 1 && (
                          <div style={{
                            position: "absolute", top: 1, right: 3,
                            fontSize: 7, color: COLORS.transVar, fontWeight: 700,
                          }}>🧍×{playerVariantCount}</div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* Legend */}
              <div style={{
                display: "flex", gap: 16, alignItems: "center",
                color: COLORS.textMuted, fontSize: 9,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{
                    display: "inline-block", width: 10, height: 10, borderRadius: 2,
                    background: VARIANT_COLORS["normaal"] + "33",
                    border: `1px solid ${VARIANT_COLORS["normaal"]}55`,
                  }} />
                  <span>N = normaal</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{
                    display: "inline-block", width: 10, height: 10, borderRadius: 2,
                    background: VARIANT_COLORS["ζ"] + "33",
                    border: `1px solid ${VARIANT_COLORS["ζ"]}55`,
                  }} />
                  <span>ζ = variant ζ</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{
                    display: "inline-block", width: 10, height: 10, borderRadius: 2,
                    background: VARIANT_COLORS["η"] + "33",
                    border: `1px solid ${VARIANT_COLORS["η"]}55`,
                  }} />
                  <span>η = variant η</span>
                </div>
                <span>·</span>
                <span>🦅 = vliegend</span>
                <span>💨 = aanvallend</span>
                <span>☠️ = grijpend</span>
              </div>

              <div style={{ color: COLORS.textMuted, fontSize: 10, textAlign: "center", maxWidth: 500, lineHeight: 1.7 }}>
                Elke cel toont alle vogels die daar kunnen verschijnen, per variant.
                Selecteer een state voor speler 🧍 + actieve vogel markering.
                {selected && selected.variant !== "normaal" && (
                  <span style={{ color: VARIANT_COLORS[selected.variant], display: "block", marginTop: 6 }}>
                    ⟳ Variant <strong>{selected.variant}</strong> — onzichtbaar voor speler
                  </span>
                )}
              </div>
            </div>
            );
          })()}
        </div>

        {/* INSPECTOR */}
        <div style={{
          width: 260, borderLeft: `1px solid ${COLORS.border}`,
          background: COLORS.surface, overflow: "auto", padding: 14, flexShrink: 0,
        }}>
          <div style={{ color: COLORS.textDim, fontSize: 9, fontWeight: 700, letterSpacing: "0.1em", marginBottom: 14 }}>
            INSPECTOR
          </div>

          {selected ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{
                background: COLORS.bg, padding: 10, borderRadius: 6,
                border: `1px solid ${VARIANT_COLORS[selected.variant]}44`,
              }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: VARIANT_COLORS[selected.variant] }}>
                  {shortLabel(selected)}
                </div>
                <div style={{ color: COLORS.textDim, fontSize: 10, marginTop: 3 }}>
                  Speler ziet: <strong>{displayLabel(selected)}</strong>
                </div>
                <div style={{
                  display: "inline-block", marginTop: 4, padding: "1px 8px", borderRadius: 3,
                  background: VARIANT_COLORS[selected.variant] + "22",
                  color: VARIANT_COLORS[selected.variant], fontSize: 10,
                }}>variant: {selected.variant}</div>
              </div>

              <div style={{ display: "flex", gap: 6 }}>
                {[
                  { label: "LEVEL", value: selected.level, color: COLORS.transLevel },
                  { label: "POSITIE", value: selected.position, color: COLORS.transPos },
                  { label: "VARIANT", value: VARIANT_SHORT[selected.variant], color: COLORS.transVar },
                ].map((a) => (
                  <div key={a.label} style={{
                    flex: 1, background: a.color + "15", padding: "6px 8px",
                    borderRadius: 4, textAlign: "center",
                  }}>
                    <div style={{ fontSize: 8, color: a.color, fontWeight: 600 }}>{a.label}</div>
                    <div style={{ fontSize: 14, color: a.color, fontWeight: 700 }}>{a.value}</div>
                  </div>
                ))}
              </div>

              <div>
                <div style={{ fontSize: 9, color: COLORS.bird, fontWeight: 600, marginBottom: 5, letterSpacing: "0.05em" }}>
                  🦅 ROOFVOGEL
                </div>
                <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
                  <select value={selected.birdLevel ?? ""}
                    onChange={(e) => updateState(selectedId, { birdLevel: e.target.value === "" ? null : +e.target.value })}
                    style={{
                      flex: 1, background: COLORS.bg, color: COLORS.text,
                      border: `1px solid ${COLORS.border}`, padding: "4px 6px",
                      borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                    }}>
                    <option value="">– Level –</option>
                    {LEVELS.map((l) => <option key={l} value={l}>L{l}</option>)}
                  </select>
                  <select value={selected.birdPosition ?? ""}
                    onChange={(e) => updateState(selectedId, { birdPosition: e.target.value === "" ? null : +e.target.value })}
                    style={{
                      flex: 1, background: COLORS.bg, color: COLORS.text,
                      border: `1px solid ${COLORS.border}`, padding: "4px 6px",
                      borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                    }}>
                    <option value="">– Positie –</option>
                    {POSITIONS.map((p) => <option key={p} value={p}>P{p}</option>)}
                  </select>
                </div>
                <select value={selected.birdMode}
                  onChange={(e) => updateState(selectedId, { birdMode: e.target.value })}
                  style={{
                    width: "100%", background: COLORS.bg,
                    color: selected.birdMode === "grabbing" ? COLORS.danger : COLORS.text,
                    border: `1px solid ${selected.birdMode === "grabbing" ? COLORS.danger : COLORS.border}`,
                    padding: "4px 6px", borderRadius: 3, fontFamily: "inherit", fontSize: 10,
                  }}>
                  <option value="flying">🦅 Vliegend</option>
                  <option value="attacking">💨 Aanvallend</option>
                  <option value="grabbing">☠️ Grijpend (GEVAAR)</option>
                </select>
              </div>

              <div>
                <div style={{ fontSize: 9, color: COLORS.transition, fontWeight: 600, marginBottom: 5, letterSpacing: "0.05em" }}>
                  TRANSITIONS
                </div>
                {transitions
                  .filter((t) => t.from === selectedId || t.to === selectedId)
                  .map((t) => {
                    const other = states.find((s) => s.id === (t.from === selectedId ? t.to : t.from));
                    const isOut = t.from === selectedId;
                    const col = transitionColor(t.axis);
                    return (
                      <div key={t.id} style={{
                        display: "flex", alignItems: "center", gap: 5,
                        padding: "4px 7px", background: COLORS.bg, borderRadius: 3, marginBottom: 3,
                        fontSize: 10, borderLeft: `3px solid ${col}`,
                      }}>
                        <span style={{ color: col, fontWeight: 700, width: 14 }}>
                          {isOut ? transitionIcon(t.axis) : "◀"}
                        </span>
                        <span style={{ color: other ? VARIANT_COLORS[other.variant] : COLORS.textDim, fontWeight: 600 }}>
                          {other ? shortLabel(other) : "?"}
                        </span>
                        <span style={{
                          fontSize: 8, color: col, padding: "0 4px", background: col + "18",
                          borderRadius: 2, marginLeft: 2,
                        }}>{t.axis}</span>
                        <span style={{ flex: 1 }} />
                        <button onClick={() => removeTransition(t.id)} style={{
                          background: "transparent", color: COLORS.textMuted, border: "none",
                          cursor: "pointer", fontFamily: "inherit", fontSize: 9,
                        }}>✕</button>
                      </div>
                    );
                  })}
                {transitions.filter((t) => t.from === selectedId || t.to === selectedId).length === 0 && (
                  <div style={{ color: COLORS.textMuted, fontSize: 10, lineHeight: 1.5 }}>
                    Geen transitions.<br />Shift+sleep in graph.
                  </div>
                )}
              </div>

              <div>
                <div style={{ fontSize: 9, color: COLORS.textDim, fontWeight: 600, marginBottom: 5, letterSpacing: "0.05em" }}>
                  ZELFDE POSITIE, ANDERE VARIANT
                </div>
                {states
                  .filter((s) => s.level === selected.level && s.position === selected.position && s.id !== selected.id)
                  .map((s) => (
                    <div key={s.id} onClick={() => setSelectedId(s.id)} style={{
                      display: "flex", alignItems: "center", gap: 6,
                      padding: "4px 7px", background: COLORS.bg, borderRadius: 3,
                      marginBottom: 3, cursor: "pointer", fontSize: 10,
                      borderLeft: `3px solid ${VARIANT_COLORS[s.variant]}`,
                    }}>
                      <span style={{ color: VARIANT_COLORS[s.variant], fontWeight: 600 }}>{shortLabel(s)}</span>
                      {s.birdLevel !== null && (
                        <span style={{ fontSize: 9 }}>🦅 L{s.birdLevel}P{s.birdPosition}</span>
                      )}
                    </div>
                  ))}
                {states.filter((s) => s.level === selected.level && s.position === selected.position && s.id !== selected.id).length === 0 && (
                  <div style={{ color: COLORS.textMuted, fontSize: 10 }}>Geen andere varianten hier.</div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ color: COLORS.textMuted, fontSize: 11, textAlign: "center", marginTop: 40, lineHeight: 1.6 }}>
              Selecteer een state<br />om te inspecteren.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
