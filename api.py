from fastapi import FastAPI
from pydantic import BaseModel

from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df

app = FastAPI(title="Evolve API")


class RunRequest(BaseModel):
    problem: str = "pacman"
    generations: int | None = None
    population: int | None = None
    top_k: int | None = None
    mutation_rate: float | None = None


@app.post("/run")
def run(req: RunRequest):
    cfg = Config.load("./config.yaml")
    if req.generations is not None:
        cfg.raw["project"]["max_generations"] = req.generations
    if req.population is not None:
        cfg.raw["project"]["population_size"] = req.population
    if req.top_k is not None:
        cfg.raw["project"]["top_k"] = req.top_k
    if req.mutation_rate is not None:
        cfg.raw["project"]["mutation_rate"] = req.mutation_rate

    results = run_experiment(cfg, problem=req.problem)
    df = history_to_df(results)
    return {
        "rows": df.to_dict(orient="records"),
        "best": {
            mode: res.history[-1].best.fitness for mode, res in results.items()
        },
    }
