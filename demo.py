"""
CS5381 – Evolve: Evolutionary Code Optimizer
=============================================
Professor Demo Script — runs all 3 problems then opens the live UI.

Usage:
    python demo.py              # run experiments + open Streamlit UI
    python demo.py --no-ui      # run experiments only (no browser)
    python demo.py --ui-only    # skip experiments, open UI directly
"""

import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

# ── Colour helpers (work on Windows PowerShell + Linux/macOS) ────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"

def banner(text, colour=CYAN):
    width = 62
    bar = "═" * width
    print(f"\n{colour}{BOLD}╔{bar}╗")
    print(f"║  {text:<{width - 2}}║")
    print(f"╚{bar}╝{RESET}")

def section(text):
    print(f"\n{YELLOW}{BOLD}▶  {text}{RESET}")

def ok(text):
    print(f"  {GREEN}✔  {text}{RESET}")

def info(text):
    print(f"  {BLUE}ℹ  {text}{RESET}")

def warn(text):
    print(f"  {YELLOW}⚠  {text}{RESET}")


# ── Experiment runner ────────────────────────────────────────────────────────
def run_experiments():
    from src.utils.config import Config
    from src.engine.runner import run_experiment, history_to_df, plot_results

    cfg = Config.load(str(_HERE / "config.yaml"))
    cfg.raw["project"]["max_generations"]  = 5
    cfg.raw["project"]["population_size"]  = 6
    cfg.raw["project"]["top_k"]            = 2
    cfg.raw["project"]["mutation_rate"]    = 0.45

    problems = ["matrix", "pseudocode", "pacman"]
    summary  = {}

    for problem in problems:
        banner(f"Problem: {problem.upper()}", BLUE)
        t0 = time.time()

        results = run_experiment(cfg, problem)

        df = history_to_df(results)
        plot_results(df, str(_HERE / f"outputs/{problem}_fitness_demo.png"))

        elapsed = time.time() - t0
        section(f"Results  ({elapsed:.1f}s)")

        rows = []
        for mode, r in results.items():
            f0 = r.history[0].best.fitness
            fn = r.history[-1].best.fitness
            delta_pct = ((fn - f0) / max(abs(f0), 1e-6)) * 100
            symbol = "▲" if delta_pct > 0 else ("▼" if delta_pct < 0 else "─")
            rows.append((mode, f0, fn, delta_pct, symbol))

        col_w = max(len(m) for m, *_ in rows) + 2
        print(f"  {'Mode':<{col_w}} {'Gen-1':>8}  {'Final':>8}  {'Δ':>8}")
        print(f"  {'─'*col_w} {'─'*8}  {'─'*8}  {'─'*8}")
        for mode, f0, fn, dp, sym in rows:
            colour = GREEN if dp > 0 else (YELLOW if dp == 0 else RED)
            print(f"  {mode:<{col_w}} {f0:>8.4f}  {fn:>8.4f}  "
                  f"{colour}{sym}{dp:>+6.1f}%{RESET}")

        summary[problem] = rows

    return summary


# ── Streamlit launcher ───────────────────────────────────────────────────────
def launch_ui():
    section("Launching Streamlit UI")
    url = "http://localhost:8501"

    streamlit_exe = _HERE.parent / ".venv" / "Scripts" / "streamlit.exe"
    if not streamlit_exe.exists():
        streamlit_exe = "streamlit"  # fall back to PATH

    # Launch as a background process so this script keeps running
    proc = subprocess.Popen(
        [str(streamlit_exe), "run", str(_HERE / "app.py"),
         "--server.port", "8501",
         "--server.headless", "false"],
        cwd=str(_HERE),
    )

    info(f"Streamlit PID: {proc.pid}")
    info(f"Waiting 3 seconds for server to start…")
    time.sleep(3)

    webbrowser.open(url)
    ok(f"Browser opened → {url}")
    info("Press Ctrl+C to stop the server when done.")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print(f"\n{YELLOW}Streamlit stopped.{RESET}")


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    # Enable ANSI colours on Windows
    import os
    os.system("")   # triggers VT100 mode in Windows console

    parser = argparse.ArgumentParser(description="CS5381 Evolve — professor demo")
    parser.add_argument("--no-ui",    action="store_true", help="Skip Streamlit UI")
    parser.add_argument("--ui-only",  action="store_true", help="Skip experiments, open UI only")
    args = parser.parse_args()

    banner("CS5381 AOA  —  Evolve: Evolutionary Code Optimizer", CYAN)
    banner("Group 2  |  AlphaEvolve-Inspired  |  3 Problems  |  3 Modes", CYAN)

    if not args.ui_only:
        section("Running experiments on all 3 problems…")
        t_start = time.time()
        summary = run_experiments()
        total = time.time() - t_start

        banner("Final Summary", GREEN)
        print(f"  {'Problem':<12} {'Mode':<20} {'Final Fitness':>14}  {'Δ vs Baseline':>15}")
        print(f"  {'─'*12} {'─'*20} {'─'*14}  {'─'*15}")
        for problem, rows in summary.items():
            base_fitness = rows[0][2]   # no_evolution final fitness
            for mode, f0, fn, dp, sym in rows:
                vs_base = ((fn - base_fitness) / max(abs(base_fitness), 1e-6)) * 100
                colour  = GREEN if vs_base > 0 else RESET
                print(f"  {problem:<12} {mode:<20} {fn:>14.4f}  "
                      f"{colour}{sym}{vs_base:>+8.1f}%{RESET}")

        ok(f"All experiments complete in {total:.1f}s")
        ok("CSV + PNG results saved to outputs/")

    if not args.no_ui:
        launch_ui()
    else:
        info("UI skipped (--no-ui). Run  streamlit run app.py  to open the dashboard.")


if __name__ == "__main__":
    main()
