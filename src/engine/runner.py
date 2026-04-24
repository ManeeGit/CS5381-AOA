from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

_HERE = Path(__file__).parent          # Project/src/engine/
_PROJECT_ROOT = _HERE.parent.parent    # Project/

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..cache.cache import FitnessCache
from ..evaluators.matrix import MatrixConfig, MatrixEvaluator
from ..evaluators.pacman import PacmanConfig, PacmanEvaluator
from ..evaluators.pseudocode import PseudocodeConfig, PseudocodeEvaluator
from ..evaluators.wrappers import MatrixWrapper, PacmanWrapper, PseudocodeWrapper
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


def run_experiment(config, problem: str, llm_override=None, on_generation=None) -> Dict[str, RunResult]:
    # Apply reproducibility seed from config
    import random as _random
    _seed = config.get("project", "seed", default=42)
    _random.seed(_seed)
    np.random.seed(_seed)

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
        # Always reset the base agent file to the clean template before each run.
        # This prevents evolved (or corrupted) code from previous runs from becoming
        # the baseline, which would cause a flat fitness chart with no visible improvement.
        _template_path = _PROJECT_ROOT / "data/templates/pacman_agent_template.py"
        _agent_path_str = config.get("pacman", "base_agent_path")
        _agent_path = Path(_agent_path_str) if Path(_agent_path_str).is_absolute() else _PROJECT_ROOT / _agent_path_str.lstrip("./")
        import shutil as _shutil
        _shutil.copy2(str(_template_path), str(_agent_path))

        # Human-in-the-loop: allow UI to override base code
        human_override = config.get("pacman", "_human_code_override", default=None)
        if human_override:
            base_code = human_override
        else:
            base_code = _template_path.read_text()
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
    elif problem == "pseudocode":
        templates = load_templates(str(_PROJECT_ROOT / "data/templates"), pattern="pseudocode_*.py")
        # Human-in-the-loop: allow UI to override base code
        human_override = config.get("pseudocode", "_human_code_override", default=None)
        if human_override:
            base_code = human_override
        else:
            base_code = _load_base_code(
                str(_PROJECT_ROOT / "data/templates/pseudocode_base.py"),
                fallback=str(_PROJECT_ROOT / "data/templates/pseudocode_base.py"),
            )
        # Configurable fitness weights from config (set by UI sliders)
        pc_cfg = PseudocodeConfig(
            w_correctness=float(config.get("pseudocode", "w_correctness", default=0.4)),
            w_runtime=float(config.get("pseudocode", "w_runtime", default=0.2)),
            w_length=float(config.get("pseudocode", "w_length", default=0.2)),
            w_readability=float(config.get("pseudocode", "w_readability", default=0.2)),
            samples=int(config.get("pseudocode", "samples", default=10)),
        )
        evaluator = PseudocodeWrapper(PseudocodeEvaluator(pc_cfg))
        prompt = (
            "Improve the sorting algorithm to be more correct, faster, shorter, and more readable. "
            "The function must be named 'sort' and accept a list, returning a sorted list."
        )
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
    experiment_start = time.time()
    for mode in ["no_evolution", "random_mutation", "llm_guided"]:
        history = evolver.run(base_code, mode=mode, on_generation=on_generation)
        best = history[-1].best
        results[mode] = RunResult(mode=mode, history=history, best_code=best.code)

    total_time = time.time() - experiment_start
    print(f"\n[Runner] All modes complete | Total experiment time: {total_time:.2f}s")

    # --- Auto-save results CSV to disk (required by grading criteria) ---
    _auto_save_results(results, problem, total_time)

    return results


def _auto_save_results(results: Dict[str, RunResult], problem: str, total_time: float) -> None:
    """Automatically save experiment results to a timestamped CSV file."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _PROJECT_ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{problem}_results_{timestamp}.csv"

    df = history_to_df(results)
    df["total_experiment_time_s"] = total_time
    df.to_csv(out_path, index=False)
    print(f"[Runner] Results auto-saved to: {out_path}")

    # Also save as Excel (grading requirement: Excel or .csv)
    try:
        xlsx_path = out_dir / f"{problem}_results_{timestamp}.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")
        print(f"[Runner] Results also saved to: {xlsx_path}")
    except Exception:
        pass  # openpyxl not installed; CSV is sufficient


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
    import ast as _ast

    def _try_load(p: str) -> str | None:
        try:
            code = Path(p).read_text()
            _ast.parse(code)   # validate — raises SyntaxError if corrupt
            return code
        except Exception:
            return None

    code = _try_load(path)
    if code is not None:
        return code
    # Primary path is missing or corrupt — use fallback
    code = _try_load(fallback)
    if code is not None:
        return code
    # Both corrupt — return a minimal safe agent
    return "from game import Directions\nimport random\n\nclass MyAgent:\n    def getAction(self, state):\n        legal = state.getLegalActions()\n        return random.choice(legal) if legal else Directions.STOP\n"
