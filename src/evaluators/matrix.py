"""Fitness evaluator for matrix-multiplication algorithms.

The matrix problem asks the evolution engine to discover a function
``matmul3(a, b)`` that correctly multiplies two 3×3 integer matrices while
using as few arithmetic operations (``*`` and ``+``) as possible.

Fitness score (0 – 1)
----------------------
* 70 % correctness  — fraction of random test cases that match ``numpy @ b``.
* 30 % ops efficiency — ``max(0, (max_ops - actual_ops) / max_ops)``.

The goal is to discover an implementation close to Strassen’s algorithm
(which multiplies two 2×2 matrices with 7 instead of 8 multiplications)
or other sub-cubic approaches.
"""
from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class MatrixConfig:
    """Configuration for the matrix-multiplication evaluator.

    Attributes
    ----------
    size : int
        Matrix dimension (both rows and columns).  Default 3 gives 3×3
        matrices; the evaluator looks for a function named ``matmul3``.
    samples : int
        Number of random test cases run per evaluation.  Higher values
        reduce noise but slow down evaluation.
    max_ops : int
        Theoretical upper bound on arithmetic operations.  A naive 3×3
        triple-loop performs 27 multiplications + 18 additions = 45 ops;
        ``max_ops=60`` gives headroom so the ops_score is never negative
        for typical implementations.
    """
    size: int = 3
    samples: int = 5
    max_ops: int = 60


class MatrixEvaluator:
    """Evaluate a ``matmul3`` Python function for correctness and efficiency.

    Parameters
    ----------
    cfg : MatrixConfig
        Evaluation hyperparameters (matrix size, test count, ops ceiling).
    """

    def __init__(self, cfg: MatrixConfig):
        self.cfg = cfg

    def evaluate(self, code: str) -> Tuple[float, Dict[str, float]]:
        """Score a candidate ``matmul3`` implementation.

        Compiles and executes the code, then runs ``cfg.samples`` random
        multiplication trials, comparing results against ``numpy``’s reference
        implementation.

        Parameters
        ----------
        code : str
            Python source code that must define a function named ``matmul3``.

        Returns
        -------
        tuple of (float, dict)
            ``(fitness, metrics)`` where:

            * ``fitness``         — weighted score in [0, 1].
            * ``metrics["correct"]`` — fraction of test cases passed.
            * ``metrics["ops"]``     — estimated arithmetic operation count.
        """
        func = self._load_function(code)
        if func is None:
            return 0.0, {"correct": 0.0, "ops": float(self.cfg.max_ops)}

        correct = 0
        for _ in range(self.cfg.samples):
            a = np.random.randint(0, 5, (self.cfg.size, self.cfg.size))
            b = np.random.randint(0, 5, (self.cfg.size, self.cfg.size))
            try:
                res = np.array(func(a.tolist(), b.tolist()))
            except Exception:
                continue
            if np.array_equal(res, a @ b):
                correct += 1
        correctness = correct / self.cfg.samples
        ops = self._estimate_ops(code)
        ops_score = max(0.0, (self.cfg.max_ops - ops) / self.cfg.max_ops)
        fitness = 0.7 * correctness + 0.3 * ops_score
        return fitness, {"correct": correctness, "ops": float(ops)}

    def _load_function(self, code: str):
        """Compile and execute ``code``, then return the ``matmul3`` function object.

        Uses ``ast.parse`` + ``compile`` + ``exec`` in a clean namespace so
        the candidate code cannot affect the main process state.  Any syntax
        or runtime error at compile / definition time returns ``None``.

        Parameters
        ----------
        code : str
            Python source code to compile.

        Returns
        -------
        callable or None
            The ``matmul3`` function, or ``None`` if the code could not be
            compiled or does not define ``matmul3``.
        """
        try:
            mod = ast.parse(code)
        except Exception:
            return None
        local_ns = {}
        try:
            exec(compile(mod, "<candidate>", "exec"), {}, local_ns)
        except Exception:
            return None
        return local_ns.get("matmul3")

    def _estimate_ops(self, code: str) -> int:
        """Estimate the number of arithmetic operations in ``code``.

        Uses a simple token-count heuristic: counts all ``*`` and ``+``
        characters in the source string.  This is not a true operation count
        but correlates well with actual multiply-add pairs in straight-line
        matrix code.

        Parameters
        ----------
        code : str
            Python source code to scan.

        Returns
        -------
        int
            Estimated operation count.
        """
        # Rough estimate: count '*' and '+' occurrences
        return code.count("*") + code.count("+")
