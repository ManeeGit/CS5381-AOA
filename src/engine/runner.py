"""Experiment orchestrator for the Evolve evolutionary code-search framework.

This module is the single entry point for running a full experiment.  It:

1. Reads all settings from a ``Config`` object (populated from ``config.yaml``).
2. Instantiates the appropriate evaluator wrapper for the chosen problem
   (``pacman``, ``pseudocode``, or ``matrix``).
3. Instantiates the LLM backend (Ollama, local, or remote).
4. Runs three experimental *modes* in sequence via ``Evolver``:
   * ``no_evolution``    — baseline (no mutation or LLM).
   * ``random_mutation`` — mutation-only, no LLM.
   * ``llm_guided``      — mutation + LLM code improvements.
5. Auto-saves results to a timestamped ``.csv`` (and optionally ``.xlsx``).

The ``RunResult`` dataclass, ``history_to_df()``, and ``plot_results()``
helpers are consumed by the Streamlit UI (``app.py``) and by ``demo.py``.
"""
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
    """Results of a single evolutionary experiment run (one mode).

    Attributes
    ----------
    mode : str
        The evolution mode: ``"no_evolution"``, ``"random_mutation"``,
        or ``"llm_guided"``.
    history : list of GenerationResult
        One entry per generation, each containing the best candidate and
        the full evaluated population.
    best_code : str
        Python source code of the best candidate found across all generations.
    """
    mode: str
    history: List
    best_code: str


def load_templates(path: str, pattern: str = "*.py") -> List[str]:
    """Load all template algorithm files matching ``pattern`` from ``path``.

    Templates are used as donor bodies for the ``replace_function_body``
    mutation operator.  They should be valid Python files each containing
    one function that solves the target problem.

    Parameters
    ----------
    path : str
        Directory path to scan for template files.
    pattern : str
        Glob pattern to filter files, e.g. ``"matrix_*.py"``.
        Defaults to ``"*.py"`` (all Python files).

    Returns
    -------
    list of str
        File contents of all matched template files.  Returns an empty list
        if the directory does not exist.
    """
    p = Path(path)
    if not p.exists():
        return []
    return [f.read_text() for f in p.glob(pattern)]


def run_experiment(config, problem: str, llm_override=None, on_generation=None) -> Dict[str, RunResult]:
    """Run a full three-mode evolutionary experiment and return the results.

    Orchestrates the entire experiment lifecycle:

    1. Sets a reproducibility seed from ``config.project.seed``.
    2. Initialises the LLM backend (or uses ``llm_override`` from the UI).
    3. Builds the appropriate evaluator wrapper for ``problem``.
    4. Loads the base code and template pool for the problem.
    5. Runs ``Evolver.run()`` three times (one per mode) in sequence.
    6. Calls ``_auto_save_results`` to persist a timestamped CSV.

    Parameters
    ----------
    config : Config
        Parsed YAML configuration object (``src.utils.config.Config``).
    problem : str
        Problem identifier: ``"pacman"``, ``"pseudocode"``, or ``"matrix"``.
    llm_override : LLMClient, optional
        If provided, skip reading the LLM provider from config and use this
        client directly.  Used by the Streamlit UI to pass a pre-configured
        backend.
    on_generation : callable, optional
        Callback ``fn(mode, generation_result)`` called after each generation.
        Used by the Streamlit UI to update the live progress chart.

    Returns
    -------
    dict mapping str to RunResult
        Keys are the three mode names; values are ``RunResult`` objects
        containing the full generation history and best code.
    """
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
            _BUBBLE_SORT_FALLBACK = (
                "def sort(arr):\n"
                "    # Bubble sort baseline\n"
                "    n = len(arr)\n"
                "    result = arr[:]\n"
                "    for i in range(n):\n"
                "        for j in range(0, n - i - 1):\n"
                "            if result[j] > result[j + 1]:\n"
                "                result[j], result[j + 1] = result[j + 1], result[j]\n"
                "    return result\n"
            )
            base_code = _load_base_code(
                str(_PROJECT_ROOT / "data/templates/pseudocode_base.py"),
                fallback=str(_PROJECT_ROOT / "data/templates/pseudocode_base.py"),
                inline_fallback=_BUBBLE_SORT_FALLBACK,
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
            _MATMUL_FALLBACK = (
                "def matmul3(a, b):\n"
                "    res = [[0, 0, 0] for _ in range(3)]\n"
                "    for i in range(3):\n"
                "        for j in range(3):\n"
                "            s = 0\n"
                "            for k in range(3):\n"
                "                s += a[i][k] * b[k][j]\n"
                "            res[i][j] = s\n"
                "    return res\n"
            )
            base_code = _load_base_code(
                str(_PROJECT_ROOT / "data/templates/matrix_base.py"),
                fallback=str(_PROJECT_ROOT / "data/templates/matrix_base.py"),
                inline_fallback=_MATMUL_FALLBACK,
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
    """Persist experiment results to a timestamped CSV (and Excel if possible).

    Creates ``outputs/<problem>_results_<timestamp>.csv`` under the project
    root, appending a ``total_experiment_time_s`` column.  Attempts to also
    write an ``.xlsx`` file (requires ``openpyxl``); silently skips Excel if
    the package is not installed.

    Parameters
    ----------
    results : dict
        The return value of ``run_experiment`` — maps mode name to
        ``RunResult``.
    problem : str
        Problem identifier used in the output filename.
    total_time : float
        Wall-clock seconds for the entire experiment run.
    """
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
    """Convert experiment results to a tidy long-format DataFrame.

    Each row represents one generation of one mode.  The ``no_evolution``
    mode typically stops after generation 1 (it never improves), so the
    function pads it with repeated rows out to ``max_gen`` so charts show
    a flat reference line rather than a single point.

    Parameters
    ----------
    results : dict
        Return value of ``run_experiment``.

    Returns
    -------
    pd.DataFrame
        Columns: ``mode``, ``generation``, ``fitness``, one ``metric_*``
        column per evaluator dimension, and (after ``_auto_save_results``)
        ``total_experiment_time_s``.
    """
    rows = []
    for mode, res in results.items():
        for gen in res.history:
            best = gen.best
            rows.append(
                {
                    "mode": mode,
                    "generation": gen.generation + 1,   # 1-indexed for display
                    "fitness": best.fitness,
                    **{f"metric_{k}": v for k, v in best.metrics.items()},
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # no_evolution breaks after gen 1 (performance optimisation in evolve.py).
    # Pad it as a flat reference line across all generations so the chart is
    # readable — same fitness repeated, clearly showing no improvement.
    max_gen = int(df["generation"].max())
    no_evo_rows = df[df["mode"] == "no_evolution"]
    if not no_evo_rows.empty and max_gen > int(no_evo_rows["generation"].max()):
        template = no_evo_rows.iloc[-1].to_dict()
        extra = [
            {**template, "generation": g}
            for g in range(int(no_evo_rows["generation"].max()) + 1, max_gen + 1)
        ]
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)

    return df.sort_values(["mode", "generation"]).reset_index(drop=True)


def plot_results(df: pd.DataFrame, out_path: str) -> None:
    """Save a fitness-over-generations line chart to ``out_path``.

    Plots one line per evolution mode.  The ``no_evolution`` baseline is
    rendered as a dashed line extended across all generations so it is
    visually distinct from the mutation and LLM-guided curves.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``history_to_df()`` — must have ``generation``, ``fitness``,
        and ``mode`` columns.
    out_path : str
        Absolute or relative path where the PNG chart should be saved.
        Parent directories are created automatically.
    """
    plt.figure(figsize=(8, 4))
    # Ensure no_evolution appears as a flat reference line across all gens
    max_gen = int(df["generation"].max()) if not df.empty else 1
    for mode in df["mode"].unique():
        subset = df[df["mode"] == mode].sort_values("generation")
        if mode == "no_evolution" and len(subset) == 1:
            # Extend to full x-range as a flat dashed reference
            gen_vals = [1, max_gen]
            fit_vals = [subset.iloc[0]["fitness"]] * 2
            plt.plot(gen_vals, fit_vals, label=mode, linestyle="--", linewidth=1.5)
        else:
            plt.plot(subset["generation"], subset["fitness"], label=mode)
    plt.title("Fitness across generations")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.legend()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path)


def _load_base_code(path: str, fallback: str, inline_fallback: str | None = None) -> str:
    """Load the base algorithm code from ``path`` with multiple fallback levels.

    Validates the file contents with ``ast.parse`` so a corrupt or partially
    written file is treated the same as a missing one.  Falls back in order:

    1. ``path`` (primary file).
    2. ``fallback`` (secondary file, if different from ``path``).
    3. ``inline_fallback`` (hard-coded string passed by the caller).
    4. Minimal valid Pacman agent (last-resort catch-all).

    Parameters
    ----------
    path : str
        Primary file path to read.
    fallback : str
        Secondary file path tried if ``path`` is missing or invalid.
    inline_fallback : str, optional
        Hard-coded algorithm string used when both files are unavailable.

    Returns
    -------
    str
        Syntactically valid Python source code ready to seed the population.
    """
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
    if fallback != path:
        code = _try_load(fallback)
        if code is not None:
            return code
    # Both corrupt — use caller-supplied inline default if provided
    if inline_fallback is not None:
        return inline_fallback
    # Last resort: minimal safe Pacman agent (only correct for pacman problem)
    return "from game import Directions\nimport random\n\nclass MyAgent:\n    def getAction(self, state):\n        legal = state.getLegalActions()\n        return random.choice(legal) if legal else Directions.STOP\n"
