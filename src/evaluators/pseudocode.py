"""Pseudocode / Algorithm Description Evaluator.

Bonus requirement from the CS5381 project spec:
  "Design Evolve for Pseudocode or a structured algorithm description.
   Possible fitness functions include correctness, running time, code length,
   and readability. You can configure fitness criteria via the UI."

This evaluator treats the candidate as Python source that implements a sorting
or searching algorithm.  Four fitness dimensions are measured:

1. **correctness**  – fraction of test cases passed.
2. **runtime**      – inverse of average execution time (faster = higher score).
3. **code_length**  – penalises unnecessarily long code (shorter = higher score).
4. **readability**  – heuristic based on comment density, naming conventions,
                       and average identifier length.

Weights for each dimension are configurable (they must sum to 1).
"""
from __future__ import annotations

import ast
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class PseudocodeConfig:
    # Fitness weight for each dimension.  Must sum to 1.0.
    w_correctness: float = 0.4
    w_runtime: float = 0.2
    w_length: float = 0.2
    w_readability: float = 0.2

    # Number of test cases to run for correctness / timing.
    samples: int = 10

    # Maximum code length (chars) used to normalise length score.
    max_length: int = 800

    # Maximum execution time (seconds) used to normalise runtime score.
    max_time_s: float = 1.0

    def __post_init__(self) -> None:
        total = round(self.w_correctness + self.w_runtime + self.w_length + self.w_readability, 6)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Fitness weights must sum to 1.0, got {total}")


class PseudocodeEvaluator:
    """Evaluates a candidate Python function (sorting or searching algorithm)."""

    def __init__(self, cfg: PseudocodeConfig | None = None):
        self.cfg = cfg or PseudocodeConfig()

    def evaluate(self, code: str) -> Tuple[float, Dict[str, float]]:
        func = self._load_function(code)
        if func is None:
            return 0.0, {
                "correctness": 0.0,
                "runtime": 0.0,
                "length": 0.0,
                "readability": 0.0,
            }

        correctness = self._score_correctness(func)
        runtime = self._score_runtime(func)
        length = self._score_length(code)
        readability = self._score_readability(code)

        fitness = (
            self.cfg.w_correctness * correctness
            + self.cfg.w_runtime * runtime
            + self.cfg.w_length * length
            + self.cfg.w_readability * readability
        )
        return round(fitness, 6), {
            "correctness": correctness,
            "runtime": runtime,
            "length": length,
            "readability": readability,
        }

    # ------------------------------------------------------------------
    # Individual dimension scorers
    # ------------------------------------------------------------------

    def _score_correctness(self, func) -> float:
        """Measure what fraction of sorting test cases the function solves correctly.

        Runs ``cfg.samples`` trials with lists of lengths 0–20, containing
        random integers in \u2212100…100, using a fixed seed (42) for
        reproducibility.  Supports both copy-returning and in-place sort
        semantics — if the function returns ``None`` the input copy is
        inspected instead.

        Parameters
        ----------
        func : callable
            A Python function extracted from candidate code.

        Returns
        -------
        float
            Score in [0, 1] — 1.0 means all test cases passed.
        """
        rng = random.Random(42)
        passed = 0
        for _ in range(self.cfg.samples):
            n = rng.randint(0, 20)
            lst = [rng.randint(-100, 100) for _ in range(n)]
            expected = sorted(lst)
            try:
                result = func(lst[:])   # pass a copy so in-place sorts work
                if result is None:
                    # in-place sort — compare lst itself
                    # (we already passed a copy so this won't work;
                    #  try calling on original and checking)
                    tmp = lst[:]
                    func(tmp)
                    result = tmp
                if list(result) == expected:
                    passed += 1
            except Exception:
                pass
        return passed / self.cfg.samples

    def _score_runtime(self, func) -> float:
        """Score execution speed as an inverse-normalised average time.

        Runs ``cfg.samples`` trials on 50-element random integer lists,
        timing each with ``time.perf_counter``.  The average time is
        normalised against ``cfg.max_time_s``:

            score = max(0, 1 − avg_time / max_time_s)

        A perfectly instant function scores 1.0; a function that takes
        exactly ``max_time_s`` or longer scores 0.0.

        Parameters
        ----------
        func : callable
            A Python function extracted from candidate code.

        Returns
        -------
        float
            Speed score in [0, 1].  Higher is faster.
        """
        rng = random.Random(99)
        times = []
        for _ in range(self.cfg.samples):
            lst = [rng.randint(-1000, 1000) for _ in range(50)]
            cpy = lst[:]
            t0 = time.perf_counter()
            try:
                func(cpy)
            except Exception:
                pass
            times.append(time.perf_counter() - t0)
        avg = sum(times) / len(times) if times else self.cfg.max_time_s
        score = max(0.0, 1.0 - avg / self.cfg.max_time_s)
        return round(score, 6)

    def _score_length(self, code: str) -> float:
        """Penalise unnecessarily long code; shorter (but non-empty) scores higher.

        Computes ``max(0, 1 \u2212 len(code) / cfg.max_length)``.
        An empty string returns 0.0 to avoid rewarding trivially empty code.

        Parameters
        ----------
        code : str
            Python source code of the candidate.

        Returns
        -------
        float
            Length score in [0, 1].  Shorter code scores higher.
        """
        length = len(code.strip())
        if length == 0:
            return 0.0
        score = max(0.0, 1.0 - length / self.cfg.max_length)
        return round(score, 6)

    def _score_readability(self, code: str) -> float:
        """Heuristic readability score (0–1) from two sub-scores.

        Sub-score 1 — **Comment density** (50 % weight):
            ``min(1.0, comment_lines / total_lines \u00d7 5)``
            So one comment per five lines achieves the maximum sub-score.

        Sub-score 2 — **Identifier quality** (50 % weight):
            The average length of all ``ast.Name`` identifiers is compared
            to an ideal of 7 characters.  The further the average drifts
            from 7, the lower the score.

        Both sub-scores are in [0, 1]; the readability score is their
        equal-weight average.

        Parameters
        ----------
        code : str
            Python source code of the candidate.

        Returns
        -------
        float
            Readability score in [0, 1].
        """
        lines = code.splitlines()
        if not lines:
            return 0.0

        # Comment density
        comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
        comment_score = min(1.0, comment_lines / max(len(lines), 1) * 5)

        # Identifier quality
        try:
            tree = ast.parse(code)
            names = [
                node.id for node in ast.walk(tree)
                if isinstance(node, ast.Name)
            ]
            if names:
                avg_len = sum(len(n) for n in names) / len(names)
                # ideal identifier length: 3-12 chars
                name_score = 1.0 - abs(avg_len - 7) / 14
                name_score = max(0.0, min(1.0, name_score))
            else:
                name_score = 0.5
        except Exception:
            name_score = 0.0

        readability = 0.5 * comment_score + 0.5 * name_score
        return round(readability, 6)

    # ------------------------------------------------------------------
    # Code loading (sandboxed)
    # ------------------------------------------------------------------

    def _load_function(self, code: str):
        """
        Parse and exec the candidate code, then return the first callable
        that looks like a sorting function.  Returns None on failure.
        Globals are shared with locals so recursive functions work correctly.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None

        # Use a shared namespace for globals AND locals so recursive calls resolve
        shared_ns: Dict = {"__builtins__": __builtins__}
        try:
            exec(compile(tree, "<pseudocode_candidate>", "exec"), shared_ns, shared_ns)
        except Exception:
            return None

        # Look for a function named 'sort', 'algorithm', or any single function
        preferred = ["sort", "algorithm", "solve", "run"]
        for name in preferred:
            if callable(shared_ns.get(name)):
                return shared_ns[name]

        # Fall back to any callable defined in the namespace (skip builtins)
        for key, val in shared_ns.items():
            if callable(val) and not key.startswith("_"):
                return val

        return None
