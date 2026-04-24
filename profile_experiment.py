"""
cProfile demo for CS5381 AOA – Lecture 4, Slide 10
====================================================
Usage:
    python profile_experiment.py                   # profile matrix problem (default)
    python profile_experiment.py pacman            # profile pacman problem
    python profile_experiment.py matrix --save     # save .prof file for snakeviz

Three ways to profile shown here:
    1. cProfile.run()          – quick one-liner
    2. cProfile.Profile()      – programmatic start/stop
    3. python -m cProfile ...  – command-line (see bottom of this file)
"""

import cProfile
import pstats
import sys
import argparse
from pathlib import Path

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from src.utils.config import Config
from src.engine.runner import run_experiment

cfg = Config.load(str(_HERE / "config.yaml"))

# Use a very short run for profiling so it finishes quickly during the demo
# Override generation count to 2 to keep profiling time reasonable
_DEMO_GENERATIONS = 2


def _patch_cfg_for_demo(config):
    """Temporarily lower generation count so profiling completes fast."""
    config.raw["project"]["max_generations"] = _DEMO_GENERATIONS
    config.raw["project"]["population_size"] = 2
    return config


# --------------------------------------------------------------------------- #
# Method 1: cProfile.run()  (simplest – one liner)
# --------------------------------------------------------------------------- #
def demo_method1(problem: str):
    print("\n" + "="*60)
    print("METHOD 1: cProfile.run() — one-liner")
    print("="*60)

    patched = _patch_cfg_for_demo(Config.load(str(_HERE / "config.yaml")))

    # cProfile.run() compiles and profiles the given statement string
    cProfile.run(
        f"run_experiment(patched, problem='{problem}')",
        globals={"run_experiment": run_experiment, "patched": patched},
    )


# --------------------------------------------------------------------------- #
# Method 2: cProfile.Profile()  (programmatic start/stop, custom pstats output)
# --------------------------------------------------------------------------- #
def demo_method2(problem: str, save: bool = False):
    print("\n" + "="*60)
    print("METHOD 2: cProfile.Profile() — programmatic")
    print("="*60)

    patched = _patch_cfg_for_demo(Config.load(str(_HERE / "config.yaml")))

    profiler = cProfile.Profile()
    profiler.enable()

    # ---- code under profiling ----
    run_experiment(patched, problem=problem)
    # ---- end of profiled section ----

    profiler.disable()

    # pstats lets you sort and filter the results — print directly to stdout
    print("\n--- Top 20 functions by CUMULATIVE time (cumtime) ---")
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(20)

    print("\n--- Top 20 functions by TOTAL (self) time (tottime) ---")
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(20)

    if save:
        out_path = _HERE / f"outputs/profile_{problem}.prof"
        out_path.parent.mkdir(exist_ok=True)
        profiler.dump_stats(str(out_path))
        print(f"\n[cProfile] Stats saved to: {out_path}")
        print("  Visualise with:  pip install snakeviz && snakeviz", out_path)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cProfile demo for CS5381 AOA")
    parser.add_argument("problem", nargs="?", default="matrix",
                        choices=["matrix", "pacman", "pseudocode"],
                        help="Which problem to profile (default: matrix)")
    parser.add_argument("--method", type=int, default=2, choices=[1, 2],
                        help="Which cProfile method to demonstrate (default: 2)")
    parser.add_argument("--save", action="store_true",
                        help="Save .prof file for snakeviz visualisation")
    args = parser.parse_args()

    print(__doc__)
    print(f"Profiling: problem={args.problem}, method={args.method}, save={args.save}")
    print(f"(Generations capped at {_DEMO_GENERATIONS} for demo speed)\n")

    if args.method == 1:
        demo_method1(args.problem)
    else:
        demo_method2(args.problem, save=args.save)

    print("\n" + "="*60)
    print("COMMAND-LINE alternative (METHOD 3):")
    print(f"  python -m cProfile -s cumtime run_experiment.py")
    print(f"  python -m cProfile -o outputs/profile_{args.problem}.prof run_experiment.py")
    print("="*60)
