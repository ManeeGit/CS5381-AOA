"""Final comprehensive test — all 3 problems, all 3 modes, validates chart data."""
import sys
sys.path.insert(0, ".")
from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df, plot_results

cfg = Config.load("config.yaml")
cfg.raw["project"]["max_generations"] = 5
cfg.raw["project"]["population_size"] = 6
cfg.raw["project"]["top_k"] = 2
cfg.raw["project"]["mutation_rate"] = 0.45

all_ok = True
for problem in ["matrix", "pseudocode", "pacman"]:
    print(f"\n=== {problem.upper()} ===")
    try:
        results = run_experiment(cfg, problem)
        df = history_to_df(results)

        # --- validate generation indexing ---
        gens = sorted(df["generation"].unique())
        assert gens[0] == 1, f"gen index should start at 1, got {gens[0]}"

        # --- validate no_evolution padding ---
        no_evo_gens = df[df["mode"] == "no_evolution"]["generation"].tolist()
        max_gen = int(df["generation"].max())
        assert len(no_evo_gens) == max_gen, (
            f"no_evolution should have {max_gen} rows, got {len(no_evo_gens)}"
        )

        # --- print per-mode result ---
        for mode, r in results.items():
            f0 = r.history[0].best.fitness
            fn = r.history[-1].best.fitness
            df_rows = len(df[df["mode"] == mode])
            print(f"  {mode}: gen1={f0:.4f} final={fn:.4f} delta={fn-f0:+.4f}  df_rows={df_rows}")

        plot_results(df, f"outputs/{problem}_fitness_final.png")
        print(f"  [PASS] gens={gens[0]}-{gens[-1]} | no_evo_rows={len(no_evo_gens)}/{max_gen}")
    except Exception as e:
        import traceback
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        all_ok = False

print()
print("=" * 40)
print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")
print("=" * 40)
