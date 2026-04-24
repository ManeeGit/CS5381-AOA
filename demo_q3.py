"""
CS5381 AOA — Q3 Demo: Varying the Cost Function (mediumMaze)
=============================================================
Demonstrates the evolutionary code optimizer against the Berkeley UCS baseline:

    python pacman.py -l mediumMaze -p SearchAgent -a fn=ucs

Demo flow
---------
Phase 0  — UCS Baseline           (reference: SearchAgent fn=ucs on mediumMaze)
Phase 1  — No-Evolution Baseline   (random agent, no mutation, no LLM)
Phase 2  — Human Feedback          (human supplies a smarter greedy agent)
Phase 3  — 4 Generations LLM-Guided Evolution starting from the human agent
Phase 4  — cProfile  summary       (shows which functions consume the most time)

Usage
-----
    python demo_q3.py              # full demo with cProfile
    python demo_q3.py --skip-profile   # skip the profiling phase (faster)
"""
from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows so box-drawing chars print correctly
if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df, plot_results

# ── Terminal colours ──────────────────────────────────────────────────────────
RESET  = "\033[0m";  BOLD   = "\033[1m"
GREEN  = "\033[92m"; CYAN   = "\033[96m"
YELLOW = "\033[93m"; RED    = "\033[91m"
BLUE   = "\033[94m"; WHITE  = "\033[97m"

def banner(text: str, colour: str = CYAN) -> None:
    w = 66
    print(f"\n{colour}{BOLD}╔{'═'*w}╗")
    print(f"║  {text:<{w-2}}║")
    print(f"╚{'═'*w}╝{RESET}")

def section(text: str) -> None:
    print(f"\n{YELLOW}{BOLD}▶  {text}{RESET}")

def row(label: str, value: str, colour: str = WHITE) -> None:
    print(f"  {BOLD}{label:<30}{RESET}{colour}{value}{RESET}")

def ok(text: str)   -> None: print(f"  {GREEN}✔  {text}{RESET}")
def info(text: str) -> None: print(f"  {BLUE}ℹ  {text}{RESET}")
def warn(text: str) -> None: print(f"  {YELLOW}⚠  {text}{RESET}")


# ── Human-feedback agent (user pastes a smarter agent) ───────────────────────
# This simulates a professor or student providing a better base agent
# through the Streamlit UI's "Human Feedback" text area.
HUMAN_FEEDBACK_AGENT = """from game import Directions
import random

class MyAgent:
    \"\"\"Human-feedback Gen-1 agent: avoids ghosts and moves toward food.\"\"\"

    def getAction(self, state):
        legal = state.getLegalActions()
        if not legal:
            return Directions.STOP

        # 1. Win immediately if possible
        for action in legal:
            succ = state.generatePacmanSuccessor(action)
            if succ.isWin():
                return action

        # 2. Avoid losing moves
        safe = []
        for action in legal:
            succ = state.generatePacmanSuccessor(action)
            if not succ.isLose():
                safe.append(action)
        if not safe:
            return random.choice(legal)

        # 3. Prefer moves that increase score (eat food / capsules)
        best_score = float('-inf')
        best = []
        for action in safe:
            succ = state.generatePacmanSuccessor(action)
            s = succ.getScore() - state.getScore()
            if s > best_score:
                best_score = s
                best = [action]
            elif s == best_score:
                best.append(action)

        return random.choice(best)
"""

# ── UCS Baseline reference numbers (Berkeley mediumMaze fn=ucs) ──────────────
# Run: python pacman.py -l mediumMaze -p SearchAgent -a fn=ucs
UCS_SCORE        = 380   # typical score for UCS on mediumMaze
UCS_STEPS        = 68    # path length (optimal)
UCS_COST_TOTAL   = 68    # each step costs 1 by default (Q3 default)


# ── Config builder ────────────────────────────────────────────────────────────
def _make_cfg(generations: int = 4, pop_size: int = 6) -> Config:
    cfg = Config.load(str(_HERE / "config.yaml"))
    cfg.raw["project"]["max_generations"] = generations
    cfg.raw["project"]["population_size"] = pop_size
    cfg.raw["project"]["top_k"]           = 2
    cfg.raw["project"]["mutation_rate"]   = 0.45
    # Force mediumMaze (Q3 layout)
    cfg.raw["pacman"]["layout"] = "mediumMaze"
    return cfg


# ── Phase helpers ─────────────────────────────────────────────────────────────

def phase_ucs_baseline() -> None:
    banner("PHASE 0 — UCS Baseline (Berkeley SearchAgent)", BLUE)
    info("Reference command:")
    print(f"\n  {CYAN}python pacman.py -l mediumMaze -p SearchAgent -a fn=ucs{RESET}\n")
    row("Algorithm:",      "Uniform Cost Search (fn=ucs)")
    row("Layout:",         "mediumMaze")
    row("Score:",          f"{UCS_SCORE}  pts")
    row("Steps (cost):",   f"{UCS_STEPS}  moves")
    row("Total path cost:", f"{UCS_COST_TOTAL}  (1 per step, Q3 default cost fn)")
    print()
    info("This is the reference we are competing against.")


def phase_no_evolution(cfg: Config) -> dict:
    banner("PHASE 1 — No-Evolution Baseline (random agent)", BLUE)
    info("Running no_evolution mode only — no mutation, no LLM.")
    t0 = time.time()
    results = run_experiment(cfg, "pacman")
    elapsed = time.time() - t0

    r   = results["no_evolution"]
    fit = r.history[-1].best.fitness
    m   = r.history[-1].best.metrics

    section(f"Result  ({elapsed:.1f}s)")
    row("Fitness:",  f"{fit:.4f}")
    row("Score:",    f"{m.get('score', 0):.1f}  pts")
    row("Steps:",    f"{m.get('steps', 0):.0f}")
    row("Survival:", f"{m.get('survival', 0):.1f}  s")

    delta_score = m.get('score', 0) - UCS_SCORE
    colour = GREEN if delta_score >= 0 else RED
    row("vs UCS score:", f"{colour}{delta_score:+.1f} pts{RESET}")
    return results


def phase_human_feedback_evolution(cfg: Config) -> dict:
    banner("PHASE 2+3 — Human Feedback + 4-Generation LLM Evolution", BLUE)
    info("Simulating human expert pasting a smarter agent in the UI…")
    print(f"\n{CYAN}  [Human provides: food-chasing, ghost-avoiding greedy agent]{RESET}\n")

    # Inject the human agent as the base code for evolution
    cfg.raw["pacman"]["_human_code_override"] = HUMAN_FEEDBACK_AGENT

    t0 = time.time()
    results = run_experiment(cfg, "pacman")
    elapsed = time.time() - t0

    section(f"Generation-by-Generation Results  ({elapsed:.1f}s)")
    print(f"\n  {'Mode':<20} {'Gen':>4}  {'Fitness':>9}  {'Score':>7}  {'Steps':>6}  {'Surv':>6}  {'Δ fitness':>9}")
    print(f"  {'─'*20} {'─'*4}  {'─'*9}  {'─'*7}  {'─'*6}  {'─'*6}  {'─'*9}")

    summary = {}
    for mode_name in ["no_evolution", "random_mutation", "llm_guided"]:
        r = results[mode_name]
        prev_fit = None
        for gen_result in r.history:
            b   = gen_result.best
            m   = b.metrics
            gen = gen_result.generation + 1
            delta = "" if prev_fit is None else f"{b.fitness - prev_fit:+.4f}"
            colour = GREEN if (prev_fit is not None and b.fitness > prev_fit) else RESET
            print(f"  {mode_name:<20} {gen:>4}  {b.fitness:>9.4f}  "
                  f"{m.get('score',0):>7.1f}  {m.get('steps',0):>6.0f}  "
                  f"{m.get('survival',0):>6.1f}  {colour}{delta:>9}{RESET}")
            prev_fit = b.fitness
        summary[mode_name] = r.history[-1].best

    return results, summary


def phase_final_comparison(no_evo_results: dict, evo_summary: dict) -> None:
    banner("PHASE 4 — Final Comparison: UCS vs Evolved Agent", BLUE)

    no_evo_best = no_evo_results["no_evolution"].history[-1].best
    llm_best    = evo_summary.get("llm_guided")

    print(f"\n  {'Agent':<30} {'Fitness':>9}  {'Score':>7}  {'Steps':>6}  {'Survival':>8}")
    print(f"  {'─'*30} {'─'*9}  {'─'*7}  {'─'*6}  {'─'*8}")

    # UCS reference row
    print(f"  {'UCS baseline (SearchAgent)':<30} {'—':>9}  {UCS_SCORE:>7}  {UCS_STEPS:>6}  {'—':>8}")

    # No-evolution row
    m0 = no_evo_best.metrics
    print(f"  {'Our baseline (no_evolution)':<30} {no_evo_best.fitness:>9.4f}  "
          f"{m0.get('score',0):>7.1f}  {m0.get('steps',0):>6.0f}  "
          f"{m0.get('survival',0):>8.1f}")

    # Best evolved row
    if llm_best:
        ml = llm_best.metrics
        score_delta   = ml.get('score', 0) - UCS_SCORE
        steps_delta   = ml.get('steps', 0) - UCS_STEPS
        colour_score  = GREEN if score_delta >= 0 else RED
        colour_steps  = GREEN if steps_delta <= 0 else RED
        print(f"  {f'LLM-guided Gen-4 (human base)':<30} {BOLD}{llm_best.fitness:>9.4f}{RESET}  "
              f"{colour_score}{ml.get('score',0):>7.1f}{RESET}  "
              f"{colour_steps}{ml.get('steps',0):>6.0f}{RESET}  "
              f"{ml.get('survival',0):>8.1f}")
        print()
        row("Score vs UCS:", f"{colour_score}{score_delta:+.1f} pts{RESET}")
        row("Steps vs UCS:", f"{colour_steps}{steps_delta:+.0f}{RESET}")

    print()
    ok("Evolution complete — 4 generations demonstrated.")
    ok("Human feedback injected at Phase 2 (greedy food-chasing agent).")
    ok("Best result shown above vs Berkeley UCS reference.")


def phase_cprofile(cfg: Config) -> None:
    banner("PHASE 5 — cProfile Performance Analysis", BLUE)
    info("Profiling 2-generation run (matrix problem, fast reference)…")
    info("Full command:  python -m cProfile -s cumtime demo_q3.py")
    print()

    # Fast config for profiling (2 gens, 2 pop)
    pcfg = _make_cfg(generations=2, pop_size=2)

    pr = cProfile.Profile()
    pr.enable()
    run_experiment(pcfg, "matrix")
    pr.disable()

    # Print top-15 by cumulative time
    buf = io.StringIO()
    ps  = pstats.Stats(pr, stream=buf).sort_stats("cumulative")
    ps.print_stats(15)
    output = buf.getvalue()

    # Highlight our own module lines
    section("Top-15 functions by cumulative time (matrix/2gen/pop=2)")
    for line in output.splitlines():
        if any(k in line for k in ("evolve", "runner", "evaluator", "matrix", "mutation", "cache")):
            print(f"  {CYAN}{line}{RESET}")
        else:
            print(f"  {line}")

    print()
    info("To profile the full Pacman run:  python -m cProfile -s cumtime demo_q3.py --skip-profile")
    info("To explore interactively:        pip install snakeviz && snakeviz profile.prof")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="CS5381 Q3 Demo")
    parser.add_argument("--skip-profile", action="store_true",
                        help="Skip the cProfile phase (faster demo)")
    parser.add_argument("--generations", type=int, default=4,
                        help="Number of evolution generations (default: 4)")
    args = parser.parse_args()

    banner("CS5381 AOA — Q3: Varying the Cost Function Demo", CYAN)
    info(f"Layout:         mediumMaze")
    info(f"Generations:    {args.generations}")
    info(f"Human feedback: YES (greedy food-chasing agent)")
    info(f"LLM backend:    Ollama (qwen2.5-coder:7b)")

    # Phase 0: Show UCS baseline for reference
    phase_ucs_baseline()

    cfg_base = _make_cfg(generations=args.generations)
    cfg_evo  = _make_cfg(generations=args.generations)

    # Phase 1: No-evolution baseline
    no_evo_results = phase_no_evolution(cfg_base)

    # Phase 2+3: Human feedback + 4-gen LLM evolution
    evo_results, evo_summary = phase_human_feedback_evolution(cfg_evo)

    # Phase 4: Final comparison table
    phase_final_comparison(no_evo_results, evo_summary)

    # Phase 5: cProfile (optional)
    if not args.skip_profile:
        phase_cprofile(_make_cfg(generations=2, pop_size=2))

    banner("Demo Complete", GREEN)
    ok("Run the full interactive UI:  python demo.py --ui-only")
    ok("Profile the full run:         python -m cProfile -s cumtime run_experiment.py")


if __name__ == "__main__":
    main()
