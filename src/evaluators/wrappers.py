from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .pacman import PacmanEvaluator
from .matrix import MatrixEvaluator
from .pseudocode import PseudocodeEvaluator


_SAFE_AGENT = (
    "from game import Directions\nimport random\n\n"
    "class MyAgent:\n"
    "    def getAction(self, state):\n"
    "        legal = state.getLegalActions()\n"
    "        return random.choice(legal) if legal else Directions.STOP\n"
)


def _clean_code(code: str) -> str:
    """Sanitize code before writing to disk. Falls back to a safe agent on failure."""
    try:
        from ..llm.ollama_client import OllamaLLM
        cleaned = OllamaLLM._sanitize_code(code)
    except Exception:
        cleaned = code
    try:
        ast.parse(cleaned)
        return cleaned
    except SyntaxError:
        pass
    # Last resort: return a guaranteed-valid minimal agent
    return _SAFE_AGENT


@dataclass
class PacmanWrapper:
    evaluator: PacmanEvaluator
    agent_path: str
    agent_name: str = "MyAgent"

    def evaluate(self, code: str) -> Tuple[float, dict]:
        path = Path(self.agent_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_clean_code(code))
        return self.evaluator.evaluate(self.agent_name)


@dataclass
class MatrixWrapper:
    evaluator: MatrixEvaluator

    def evaluate(self, code: str) -> Tuple[float, dict]:
        return self.evaluator.evaluate(code)


@dataclass
class PseudocodeWrapper:
    evaluator: PseudocodeEvaluator

    def evaluate(self, code: str) -> Tuple[float, dict]:
        return self.evaluator.evaluate(code)
