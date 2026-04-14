from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .pacman import PacmanEvaluator
from .matrix import MatrixEvaluator


@dataclass
class PacmanWrapper:
    evaluator: PacmanEvaluator
    agent_path: str
    agent_name: str = "MyAgent"

    def evaluate(self, code: str) -> Tuple[float, dict]:
        path = Path(self.agent_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code)
        return self.evaluator.evaluate(self.agent_name)


@dataclass
class MatrixWrapper:
    evaluator: MatrixEvaluator

    def evaluate(self, code: str) -> Tuple[float, dict]:
        return self.evaluator.evaluate(code)
