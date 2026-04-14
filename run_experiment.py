from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df, plot_results

cfg = Config.load("./config.yaml")

for problem in ["pacman", "matrix"]:
    results = run_experiment(cfg, problem=problem)
    df = history_to_df(results)
    plot_results(df, f"./outputs/{problem}_fitness.png")
    df.to_csv(f"./outputs/{problem}_fitness.csv", index=False)
    print(f"Saved outputs for {problem}.")
