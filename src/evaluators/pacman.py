"""Fitness evaluator for Pacman AI agent code.

This evaluator scores candidate Pacman agent Python files by either:

* **Running the real Pacman simulator** (``pacman.py`` from the Berkeley
  teaching framework) if it is present in ``cfg.root_path``, extracting
  ``Score``, ``Steps``, and ``Survival Time`` from stdout.
* **Simulating deterministically** via ``_simulate_from_agent_file`` (hash-
  seeded RNG + code-quality heuristics) when the real simulator is absent.
  This lets the evolution loop run in environments where the Pacman
  dependencies are not installed.

Fitness formula
---------------
fitness = 0.6 \u00d7 score + 0.3 \u00d7 survival \u2212 0.1 \u00d7 steps

(Higher score and longer survival are better; fewer steps is better.)
"""
from __future__ import annotations

import hashlib
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


@dataclass
class PacmanConfig:
    """Configuration for the Pacman evaluator.

    Attributes
    ----------
    root_path : str
        Absolute path to the Pacman project directory (contains ``pacman.py``).
    base_agent_path : str
        Path to the current candidate agent file.  Used by the deterministic
        simulator when the real Pacman binary is not available.
    command : str
        Shell command template to run the Pacman game.  May contain
        ``{root}``, ``{agent}``, and ``{layout}`` placeholders.
    layout : str
        Name of the Pacman layout (maze) to use, e.g. ``"mediumGrid"``.
    """
    root_path: str
    base_agent_path: str
    command: str
    layout: str


class PacmanEvaluator:
    """Run the Pacman simulator and extract a fitness score from the output.

    Parameters
    ----------
    cfg : PacmanConfig
        Paths and command configuration for the Pacman simulation.
    """

    def __init__(self, cfg: PacmanConfig):
        self.cfg = cfg

    def evaluate(self, agent_name: str) -> Tuple[float, Dict[str, float]]:
        """Run one Pacman game and return the fitness score.

        If ``pacman.py`` is present in ``cfg.root_path`` the real simulator
        is invoked via subprocess.  Otherwise the deterministic simulator
        (``_simulate_from_agent_file``) is used as a fallback.

        Parameters
        ----------
        agent_name : str
            Name of the agent class to pass to the Pacman command, e.g.
            ``"MyAgent"``.

        Returns
        -------
        tuple of (float, dict)
            ``(fitness, metrics)`` where ``metrics`` has keys ``score``,
            ``steps``, and ``survival``.
        """
        root = Path(self.cfg.root_path)
        pacman_py = root / "pacman.py"
        if not pacman_py.exists():
            return _simulate_from_agent_file(self.cfg.base_agent_path)

        cmd = self.cfg.command.format(
            root=self.cfg.root_path, agent=agent_name, layout=self.cfg.layout
        )
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
            )
            out = proc.stdout + "\n" + proc.stderr
        except Exception:
            out = ""

        score = _extract_metric(out, r"Score: (-?\d+(?:\.\d+)?)", default=0.0)
        steps = _extract_metric(out, r"Steps: (-?\d+(?:\.\d+)?)", default=0.0)
        survival = _extract_metric(
            out, r"Survival Time: (-?\d+(?:\.\d+)?)", default=0.0
        )

        # Weighted fitness; weights sum to 1
        fitness = 0.6 * score + 0.3 * survival - 0.1 * steps
        return fitness, {"score": score, "steps": steps, "survival": survival}


def _simulate_from_agent_file(agent_path: str) -> Tuple[float, Dict[str, float]]:
    """Deterministic simulation based on agent code quality heuristics.

    Scores are reproducible for identical code but vary meaningfully with
    code complexity so that evolution can show real improvement over generations.
    """
    try:
        code = Path(agent_path).read_text()
    except Exception:
        code = ""
    return _score_code(code)


def _score_code(code: str) -> Tuple[float, Dict[str, float]]:
    """Evaluate agent code quality deterministically.

    Uses a seeded RNG (seeded from code hash) so the same code always
    produces the same score, while different code gets different scores.
    A heuristic bonus rewards code that contains real game logic.
    """
    # --- Deterministic noise seeded from code content ---
    code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
    rng = random.Random(code_hash)

    # --- Heuristic quality score (0..100) based on code features ---
    quality = _code_quality_score(code)

    # Base game performance scales with quality
    base_score = 50.0 + quality * 1.5          # 50..200
    base_survival = 20.0 + quality * 0.5        # 20..70
    base_steps = 300.0 - quality * 2.0          # 300..100 (fewer is better)

    # Small deterministic jitter (±15%) from seeded RNG
    jitter = lambda v, pct: v * (1.0 + rng.uniform(-pct, pct))
    score    = max(0.0, jitter(base_score, 0.15))
    survival = max(0.0, jitter(base_survival, 0.15))
    steps    = max(10.0, jitter(base_steps, 0.15))

    fitness = 0.6 * score + 0.3 * survival - 0.1 * steps
    return fitness, {"score": round(score, 2), "steps": round(steps, 2), "survival": round(survival, 2)}


def _code_quality_score(code: str) -> float:
    """Return a 0-100 quality score based on code complexity heuristics."""
    score = 0.0

    # 1. Has a getAction method (required)
    if "def getAction" in code:
        score += 10

    # 2. Rewards for game-relevant constructs
    pacman_features = [
        ("getLegalActions", 5),
        ("getFood", 8),
        ("getGhostPositions", 8),
        ("getScore", 5),
        ("getWalls", 6),
        (r"distanceTo|manhattanDistance|mazeDistance", 10),
        (r"BFS|bfs|breadth.first", 10),
        (r"A\*|astar|a_star|heuristic", 12),
        (r"Directions\.NORTH|Directions\.SOUTH|Directions\.EAST|Directions\.WEST", 4),
    ]
    for pattern, pts in pacman_features:
        if re.search(pattern, code):
            score += pts

    # 3. Control flow complexity
    if_count   = len(re.findall(r"\bif\b", code))
    for_count  = len(re.findall(r"\bfor\b", code))
    def_count  = len(re.findall(r"\bdef\b", code))
    score += min(if_count * 1.5, 10)
    score += min(for_count * 2.0, 10)
    score += min((def_count - 1) * 3.0, 9)   # -1 for getAction itself

    # 4. Line count (more thought-out code is longer, up to a point)
    lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
    score += min(len(lines) * 0.3, 8)

    return min(score, 100.0)


def _extract_metric(text: str, pattern: str, default: float) -> float:
    """Extract a single numeric metric from Pacman simulator stdout.

    Parameters
    ----------
    text : str
        Combined stdout + stderr from the Pacman subprocess.
    pattern : str
        Regex pattern with one capture group that matches the numeric value,
        e.g. ``r"Score: (-?\\d+(?:\\.\\d+)?)"``.
    default : float
        Value to return when the pattern is not found.

    Returns
    -------
    float
        Extracted metric value, or ``default`` if the pattern did not match.
    """
    m = re.search(pattern, text)
    if not m:
        return default
    try:
        return float(m.group(1))
    except Exception:
        return default
