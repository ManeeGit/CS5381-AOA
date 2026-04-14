from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class MatrixConfig:
    size: int = 3
    samples: int = 5
    max_ops: int = 60


class MatrixEvaluator:
    def __init__(self, cfg: MatrixConfig):
        self.cfg = cfg

    def evaluate(self, code: str) -> Tuple[float, Dict[str, float]]:
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
        # Rough estimate: count '*' and '+' occurrences
        return code.count("*") + code.count("+")
