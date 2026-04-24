"""Thin adapter wrappers that unify evaluator interfaces for the evolution engine.

The evolution engine (``Evolver``) calls a single ``evaluate(code)`` method
on whatever evaluator it receives.  The three problem-specific evaluators
(``PacmanEvaluator``, ``MatrixEvaluator``, ``PseudocodeEvaluator``) each have
slightly different calling conventions.  These dataclass wrappers normalise
that interface without modifying the evaluators themselves.

File-based evaluators (Pacman) also need the code written to disk before the
evaluator can run it; the wrapper handles that transparently.
"""
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
    """Sanitise candidate code before writing it to disk.

    Applies ``OllamaLLM._sanitize_code`` to remove duplicate class
    definitions that models sometimes emit, then validates the result with
    ``ast.parse``.  If sanitisation or parsing fails, falls back to a
    hard-coded minimal valid Pacman agent that always picks a random legal
    action — this guarantees the subsequent Pacman simulation never crashes
    due to a syntax error.

    Parameters
    ----------
    code : str
        Raw Python source code from a candidate.

    Returns
    -------
    str
        Syntactically valid Python code safe to write as a Pacman agent file.
    """
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
    """Wrap ``PacmanEvaluator`` for the standard ``evaluate(code)`` interface.

    Before calling the evaluator this wrapper sanitises the candidate code
    and writes it to ``agent_path`` on disk — the Pacman simulator reads the
    agent from a file.

    Attributes
    ----------
    evaluator : PacmanEvaluator
        The underlying Pacman evaluator instance.
    agent_path : str
        Absolute or relative path where the agent Python file should be
        written before each evaluation run.
    agent_name : str
        Class name inside the agent file that the simulator will instantiate.
        Defaults to ``"MyAgent"``.
    """
    evaluator: PacmanEvaluator
    agent_path: str
    agent_name: str = "MyAgent"

    def evaluate(self, code: str) -> Tuple[float, dict]:
        """Write sanitised code to disk, then run the Pacman simulation.

        Parameters
        ----------
        code : str
            Candidate agent source code.

        Returns
        -------
        tuple of (float, dict)
            Fitness score and metric dictionary from ``PacmanEvaluator.evaluate``.
        """
        path = Path(self.agent_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_clean_code(code))
        return self.evaluator.evaluate(self.agent_name)


@dataclass
class MatrixWrapper:
    """Wrap ``MatrixEvaluator`` for the standard ``evaluate(code)`` interface.

    Attributes
    ----------
    evaluator : MatrixEvaluator
        The underlying matrix-multiplication evaluator instance.
    """
    evaluator: MatrixEvaluator

    def evaluate(self, code: str) -> Tuple[float, dict]:
        """Evaluate a ``matmul3`` candidate implementation.

        Parameters
        ----------
        code : str
            Python source defining ``matmul3(a, b)``.

        Returns
        -------
        tuple of (float, dict)
            Fitness score and metric dictionary from ``MatrixEvaluator.evaluate``.
        """
        return self.evaluator.evaluate(code)


@dataclass
class PseudocodeWrapper:
    """Wrap ``PseudocodeEvaluator`` for the standard ``evaluate(code)`` interface.

    Attributes
    ----------
    evaluator : PseudocodeEvaluator
        The underlying pseudocode-to-Python evaluator instance.
    """
    evaluator: PseudocodeEvaluator

    def evaluate(self, code: str) -> Tuple[float, dict]:
        """Evaluate a pseudocode-style sorting candidate.

        Parameters
        ----------
        code : str
            Python source code implementing a sort algorithm.

        Returns
        -------
        tuple of (float, dict)
            Fitness score and metric dictionary from ``PseudocodeEvaluator.evaluate``.
        """
        return self.evaluator.evaluate(code)
