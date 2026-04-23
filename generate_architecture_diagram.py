"""
Generate a visually-appealing architecture diagram for the Evolve system.
Output: outputs/architecture_diagram.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ── colour palette ───────────────────────────────────────────────────────────
C = {
    "bg":        "#0d1117",   # dark canvas
    "ui":        "#1f6feb",   # blue  – UI layer
    "engine":    "#388bfd",   # lighter blue – engine
    "llm":       "#8957e5",   # purple – LLM
    "eval":      "#3fb950",   # green – evaluators
    "cache":     "#d29922",   # amber – cache
    "data":      "#f0883e",   # orange – data/config
    "arrow":     "#8b949e",   # grey arrows
    "text":      "#e6edf3",   # light text
    "subtext":   "#8b949e",   # dim text
    "border_ui": "#388bfd",
    "border_llm":"#a371f7",
    "modes":     "#238636",   # dark green panel
}

fig, ax = plt.subplots(figsize=(20, 14))
fig.patch.set_facecolor(C["bg"])
ax.set_facecolor(C["bg"])
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def box(ax, x, y, w, h, color, label, sublabel="", radius=0.35,
        fontsize=11, subfontsize=8.5, alpha=0.18, border_alpha=0.85,
        label_color=None):
    """Draw a rounded box with a coloured border and optional sub-label."""
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.05,rounding_size={radius}",
        linewidth=1.8,
        edgecolor=color,
        facecolor=color,
        alpha=alpha,
        zorder=2,
    )
    # border
    border = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.05,rounding_size={radius}",
        linewidth=1.8,
        edgecolor=(*matplotlib.colors.to_rgb(color), border_alpha),
        facecolor="none",
        zorder=3,
    )
    ax.add_patch(patch)
    ax.add_patch(border)

    cy = y + h / 2
    if sublabel:
        ax.text(x + w / 2, cy + 0.13, label,
                ha="center", va="center",
                fontsize=fontsize, fontweight="bold",
                color=label_color or C["text"], zorder=4)
        ax.text(x + w / 2, cy - 0.22, sublabel,
                ha="center", va="center",
                fontsize=subfontsize, color=C["subtext"], zorder=4)
    else:
        ax.text(x + w / 2, cy, label,
                ha="center", va="center",
                fontsize=fontsize, fontweight="bold",
                color=label_color or C["text"], zorder=4)


def section_label(ax, x, y, text, color):
    ax.text(x, y, text, ha="left", va="bottom",
            fontsize=8, color=color, fontweight="bold",
            alpha=0.7, zorder=5)


def arrow(ax, x1, y1, x2, y2, label="", color=None, style="->", lw=1.5):
    color = color or C["arrow"]
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style,
            color=color,
            lw=lw,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=6,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, fontsize=7, color=color,
                ha="left", va="center", zorder=7)


def dashed_arrow(ax, x1, y1, x2, y2, label="", color=None):
    color = color or C["arrow"]
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            lw=1.2,
            linestyle="dashed",
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=6,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, fontsize=7, color=color,
                ha="left", va="center", zorder=7)


def section_bg(ax, x, y, w, h, color, title, radius=0.5):
    """Faint background panel for a layer."""
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.05,rounding_size={radius}",
        linewidth=1,
        edgecolor=(*matplotlib.colors.to_rgb(color), 0.35),
        facecolor=(*matplotlib.colors.to_rgb(color), 0.06),
        zorder=1,
    )
    ax.add_patch(patch)
    ax.text(x + 0.18, y + h - 0.02, title,
            ha="left", va="top",
            fontsize=7.5, color=color, fontweight="bold",
            alpha=0.6, zorder=2)


# ─────────────────────────────────────────────────────────────────────────────
# Title
# ─────────────────────────────────────────────────────────────────────────────
ax.text(10, 13.6, "Evolve — Evolutionary Algorithm Discovery System",
        ha="center", va="top", fontsize=18, fontweight="bold",
        color=C["text"], zorder=10)
ax.text(10, 13.2, "CS5381 · Analysis of Algorithms · Architecture Overview",
        ha="center", va="top", fontsize=10, color=C["subtext"], zorder=10)

# thin title separator
ax.plot([0.5, 19.5], [12.95, 12.95], color=C["arrow"], lw=0.6, alpha=0.4, zorder=1)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 – UI  (top)
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 0.4, 11.6, 19.2, 1.2, C["ui"], "  UI LAYER")
box(ax, 6.0, 11.75, 8.0, 0.85, C["ui"],
    "  Streamlit Web App  (app.py)",
    "Matrix tab  |  Pacman tab  |  Live fitness chart  |  Human code editor")

# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 – Orchestration
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 0.4, 9.85, 19.2, 1.55, C["engine"], "  ORCHESTRATION")
box(ax, 6.0, 10.0, 8.0, 1.2, C["engine"],
    "  Runner  (src/engine/runner.py)",
    "Loads config · Selects LLM · Wires Evaluator · Launches 3 evolution modes · Auto-saves CSV")

# arrow UI → Runner
arrow(ax, 10, 11.75, 10, 11.2, color=C["ui"], lw=1.8)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 – Evolution Engine
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 0.4, 7.2, 19.2, 2.5, C["engine"], "  EVOLUTION ENGINE  (3 modes run sequentially)")

# Mode badges
modes = [
    ("no_evolution", "Baseline (no change)", 2.2),
    ("random_mutation", "Random Mutation", 8.2),
    ("llm_guided", "LLM-Guided Evolution", 14.2),
]
mode_colors = ["#388bfd", "#f0883e", "#8957e5"]
for (name, desc, mx), mc in zip(modes, mode_colors):
    box(ax, mx, 8.6, 3.6, 0.9, mc, name, desc,
        fontsize=9.5, subfontsize=7.5)

# Evolver box
box(ax, 5.0, 7.4, 10.0, 1.0, C["engine"],
    "  Evolver  (src/engine/evolve.py)",
    "Adaptive mutation rate · ThreadPoolExecutor (parallel eval) · Elitism · Stagnation detection")

# arrow Runner → Evolver (×3 modes)
for mx in [4.0, 10.0, 16.0]:
    arrow(ax, mx, 10.0, mx, 9.5, color=C["engine"], lw=1.5)

arrow(ax, 10, 10.0, 10, 9.5, color=C["engine"], lw=1.8)

# mode → evolver
for mx in [4.0, 10.0, 16.0]:
    arrow(ax, mx, 8.6, 10.0, 8.4, color=C["arrow"], lw=1.0)

arrow(ax, 10, 8.6, 10, 8.4, color=C["arrow"], lw=1.4)

# Mutations box
box(ax, 1.0, 7.4, 3.5, 1.0, C["engine"],
    "Mutations",
    "perturb · swap · replace\ninsert · llm_meta",
    fontsize=9, subfontsize=7.5)

# Evolver ↔ Mutations
arrow(ax, 5.0, 7.9, 4.5, 7.9, color=C["arrow"], lw=1.2)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 – LLM  (left column)
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 0.4, 3.8, 5.8, 3.2, C["llm"], "  LLM LAYER")

box(ax, 0.6, 5.8, 5.4, 0.95, C["llm"],
    "LLMClient  (base.py)",
    "Abstract interface  ·  improve(prompt, code) → code")

box(ax, 0.6, 4.7, 1.6, 0.95, C["llm"],
    "OllamaLLM",
    "localhost\n:11434",
    fontsize=8.5, subfontsize=7)

box(ax, 2.3, 4.7, 1.6, 0.95, C["llm"],
    "RemoteLLM",
    "OpenAI\nGemini",
    fontsize=8.5, subfontsize=7)

box(ax, 4.0, 4.7, 1.6, 0.95, C["llm"],
    "LocalLLM",
    "Fallback\nmutate",
    fontsize=8.5, subfontsize=7)

# LLMClient → concrete
for lx in [1.4, 3.1, 4.8]:
    arrow(ax, 3.3, 5.8, lx, 5.65, color=C["llm"], lw=1.0)

# Evolver → LLM
arrow(ax, 5.0, 7.7, 3.3, 6.75, color=C["llm"], lw=1.4)
ax.text(3.5, 7.35, "improve()", fontsize=7.5, color=C["llm"], rotation=38, zorder=7)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 – Evaluators  (right column)
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 7.2, 3.8, 12.4, 3.2, C["eval"], "  EVALUATOR LAYER")

box(ax, 7.4, 5.8, 5.6, 0.95, C["eval"],
    "MatrixWrapper → MatrixEvaluator",
    "Fitness = 0.7×correctness + 0.3×ops_score  |  numpy matmul samples")

box(ax, 13.5, 5.8, 5.8, 0.95, C["eval"],
    "PacmanWrapper → PacmanEvaluator",
    "Fitness = 0.6×score + 0.3×survival − 0.1×steps  |  subprocess")

# Pacman sub-system
box(ax, 14.0, 4.7, 4.8, 0.95, C["eval"],
    "third_party/pacman/",
    "pacman.py · game.py · layout",
    fontsize=9, subfontsize=7.5)

arrow(ax, 16.4, 5.8, 16.4, 5.65, color=C["eval"], lw=1.2)

# Evolver → Evaluators
arrow(ax, 10, 7.4, 10.2, 6.75, color=C["eval"], lw=1.4)
ax.text(10.3, 7.1, "evaluate()", fontsize=7.5, color=C["eval"], rotation=-35, zorder=7)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 5 – Cache  (bottom centre)
# ─────────────────────────────────────────────────────────────────────────────
section_bg(ax, 5.5, 1.6, 9.0, 2.0, C["cache"], "  CACHE LAYER")

box(ax, 5.7, 1.8, 8.6, 1.6, C["cache"],
    "FitnessCache  (VectorCache)  ·  src/cache/vector_cache.py",
    "SHA-256 exact hit  →  TF-IDF cosine similarity  →  JSONL persistence\n"
    "Reuses previous fitness scores for near-duplicate candidates",
    fontsize=10, subfontsize=8)

# Evolver ↔ Cache
arrow(ax, 10, 7.4, 10, 3.4, color=C["cache"], lw=1.4)
ax.text(10.1, 5.35, "lookup /\nstore", fontsize=7, color=C["cache"], zorder=7)

# ─────────────────────────────────────────────────────────────────────────────
# Layer 6 – Data & Config  (bottom, flanking cache)
# ─────────────────────────────────────────────────────────────────────────────
# Config (left of cache)
section_bg(ax, 0.4, 1.6, 4.8, 2.0, C["data"], "  CONFIG")
box(ax, 0.6, 1.8, 4.4, 0.85, C["data"],
    "config.yaml → Config",
    "llm · project · matrix · pacman",
    fontsize=9, subfontsize=7.5)
box(ax, 0.6, 2.75, 4.4, 0.7, C["data"],
    "data/templates/",
    "matrix_base.py  |  pacman_agent_template.py",
    fontsize=8.5, subfontsize=7)

# Outputs (right of cache)
section_bg(ax, 14.8, 1.6, 4.8, 2.0, C["data"], "  OUTPUTS")
box(ax, 15.0, 1.8, 4.4, 0.85, C["data"],
    "outputs/ · student_data/",
    "CSV fitness logs  |  per-student analysis",
    fontsize=9, subfontsize=7.5)
box(ax, 15.0, 2.75, 4.4, 0.7, C["data"],
    "profile_experiment.py",
    "cProfile  |  pstats  |  snakeviz",
    fontsize=8.5, subfontsize=7)

# Runner → Config
dashed_arrow(ax, 6.0, 10.6, 2.8, 3.45, color=C["data"])
ax.text(3.2, 7.0, "load", fontsize=7, color=C["data"], rotation=72, zorder=7)

# Runner → Outputs
dashed_arrow(ax, 14.0, 10.6, 17.2, 3.45, color=C["data"])
ax.text(16.0, 7.1, "save CSV", fontsize=7, color=C["data"], rotation=-72, zorder=7)

# ─────────────────────────────────────────────────────────────────────────────
# Legend
# ─────────────────────────────────────────────────────────────────────────────
legend_items = [
    (C["ui"],     "UI / Frontend"),
    (C["engine"], "Evolution Engine"),
    (C["llm"],    "LLM Layer"),
    (C["eval"],   "Evaluators"),
    (C["cache"],  "Cache"),
    (C["data"],   "Data / Config / Output"),
]
lx, ly = 0.5, 1.3
for i, (color, label) in enumerate(legend_items):
    rect = mpatches.Patch(facecolor=color, edgecolor=color, alpha=0.7, label=label)
    ax.add_patch(mpatches.FancyBboxPatch(
        (lx + i * 3.1, ly - 0.18), 0.35, 0.28,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor=color, edgecolor=color, alpha=0.75, zorder=8))
    ax.text(lx + i * 3.1 + 0.5, ly - 0.04, label,
            fontsize=7.5, color=C["subtext"], va="center", zorder=9)

# thin bottom line
ax.plot([0.5, 19.5], [1.25, 1.25], color=C["arrow"], lw=0.6, alpha=0.4, zorder=1)
ax.text(19.5, 0.9, "CS5381-AOA · Evolve v1.0 · April 2026",
        ha="right", va="bottom", fontsize=7.5, color=C["subtext"], zorder=9)

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
from pathlib import Path
out = Path(__file__).parent / "outputs" / "architecture_diagram.png"
out.parent.mkdir(exist_ok=True)
plt.tight_layout(pad=0)
plt.savefig(str(out), dpi=180, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
plt.close()
print(f"Saved → {out}")
