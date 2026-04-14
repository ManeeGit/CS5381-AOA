from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

_HERE = Path(__file__).parent          # Project/src/engine/
_PROJECT_ROOT = _HERE.parent.parent    # Project/

import pandas as pd
import matplotlib.pyplot as plt

from ..cache.cache import FitnessCache
from ..evaluators.matrix import MatrixConfig, MatrixEvaluator
from ..evaluators.pacman import PacmanConfig, PacmanEvaluator
from ..evaluators.wrappers import MatrixWrapper, PacmanWrapper
from ..llm.local import LocalLLM
from ..llm.ollama_client import OllamaLLM
from ..llm.remote import RemoteLLM
from .evolve import EvolutionConfig, Evolver


@dataclass
class RunResult:
    mode: str
    history: List
    best_code: str


def load_templates(path: str, pattern: str = "*.py") -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [f.read_text() for f in p.glob(pattern)]


def run_experiment(config, problem: str, llm_override=None) -> Dict[str, RunResult]:
    # Initialize LLM based on config provider setting (or use override from UI)
    if llm_override is not None:
        llm = llm_override
    else:
        provider = config.get("llm", "provider", default="ollama")
        model_name = config.get("llm", "model_name", default="qwen2.5-coder:1.5b")
        ollama_host = config.get("llm", "ollama_host", default="http://localhost:11434")

        if provider == "ollama":
            llm = OllamaLLM(model=model_name, host=ollama_host)
        elif provider == "local":
            llm = LocalLLM()
        else:
            api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
            llm = RemoteLLM(
                provider=provider,
                api_key=api_key,
                model=model_name
            )
    
    evo_cfg = EvolutionConfig(
        generations=config.get("project", "max_generations"),
        population_size=config.get("project", "population_size"),
        top_k=config.get("project", "top_k"),
        mutation_rate=config.get("project", "mutation_rate"),
    )

    _raw_cache_dir = config.get("project", "cache_dir")
    _cache_dir = str(_PROJECT_ROOT / _raw_cache_dir.lstrip("./")) if _raw_cache_dir.startswith(".") else _raw_cache_dir
    cache = FitnessCache(_cache_dir)

    if problem == "pacman":
        templates = load_templates(str(_PROJECT_ROOT / "data/templates"), pattern="pacman_*.py")
        # Human-in-the-loop: allow UI to override base code
        human_override = config.get("pacman", "_human_code_override", default=None)
        if human_override:
            base_code = human_override
        else:
            base_code = _load_base_code(
                config.get("pacman", "base_agent_path"),
                fallback=str(_PROJECT_ROOT / "data/templates/pacman_agent_template.py"),
            )
        evaluator = PacmanWrapper(
            PacmanEvaluator(
                PacmanConfig(
                    root_path=str(_PROJECT_ROOT / config.get("pacman", "root_path").lstrip("./")),
                    base_agent_path=config.get("pacman", "base_agent_path"),
                    command=config.get("pacman", "command"),
                    layout=config.get("pacman", "layout"),
                )
            ),
            agent_path=config.get("pacman", "base_agent_path"),
            agent_name="MyAgent",
        )
        prompt = "Improve the Pacman agent to maximize score and survival while minimizing steps."
    else:
        templates = load_templates(str(_PROJECT_ROOT / "data/templates"), pattern="matrix_*.py")
        # Human-in-the-loop: allow UI to override base code
        human_override = config.get("matrix", "_human_code_override", default=None)
        if human_override:
            base_code = human_override
        else:
            base_code = _load_base_code(
                str(_PROJECT_ROOT / "data/templates/matrix_base.py"),
                fallback=str(_PROJECT_ROOT / "data/templates/matrix_base.py"),
            )
        evaluator = MatrixWrapper(
            MatrixEvaluator(
                MatrixConfig(
                    size=config.get("matrix", "size"),
                    samples=config.get("matrix", "samples"),
                    max_ops=config.get("matrix", "max_ops"),
                )
            )
        )
        prompt = "Improve the 3x3 matrix multiplication to reduce ops while staying correct."

    evolver = Evolver(evo_cfg, llm, cache, templates, evaluator, prompt)

    results: Dict[str, RunResult] = {}
    for mode in ["no_evolution", "random_mutation", "llm_guided"]:
        history = evolver.run(base_code, mode=mode)
        best = history[-1].best
        results[mode] = RunResult(mode=mode, history=history, best_code=best.code)

    return results


def history_to_df(results: Dict[str, RunResult]) -> pd.DataFrame:
    rows = []
    for mode, res in results.items():
        for gen in res.history:
            best = gen.best
            rows.append(
                {
                    "mode": mode,
                    "generation": gen.generation,
                    "fitness": best.fitness,
                    **{f"metric_{k}": v for k, v in best.metrics.items()},
                }
            )
    return pd.DataFrame(rows)


def plot_results(df: pd.DataFrame, out_path: str) -> None:
    plt.figure(figsize=(8, 4))
    for mode in df["mode"].unique():
        subset = df[df["mode"] == mode]
        plt.plot(subset["generation"], subset["fitness"], label=mode)
    plt.title("Fitness across generations")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.legend()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path)


def _load_base_code(path: str, fallback: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text()
    return Path(fallback).read_text()
