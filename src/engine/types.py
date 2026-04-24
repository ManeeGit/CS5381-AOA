"""Core data containers shared across the entire Evolve framework.

This module defines the two dataclasses that act as the common language
between the evolution engine, evaluators, LLM layer, and cache:

* ``Candidate``  — one individual piece of code with its fitness score.
* ``GenerationResult`` — a snapshot of a single evolutionary generation.

Neither class contains logic; they are purely data holders (like structs
in other languages). Keeping them here prevents circular imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Candidate:
    """Represents one individual code solution in the evolutionary population.

    A Candidate is born either from the original base code (seed) or by
    mutating / LLM-improving a parent Candidate.  Its ``fitness`` and
    ``metrics`` fields start as None / empty and are filled in by
    ``Evolver._evaluate()`` before selection happens.

    Attributes
    ----------
    code : str
        The full Python source code of this candidate.
    meta : dict
        Provenance log — records how this candidate was created:
        ``op`` (mutation operator name), ``op_description`` (plain-English
        explanation), and ``parent_fitness`` (fitness of the parent).
    fitness : float or None
        Overall fitness score assigned by the evaluator.  Higher is better.
        Remains ``None`` until ``_evaluate()`` is called.
    metrics : dict
        Sub-dimension scores returned alongside the overall fitness.
        For example: ``{"correct": 1.0, "ops": 2.0}`` for matrix multiply.
        Empty dict until evaluated.
    """

    code: str
    meta: Dict[str, str] = field(default_factory=dict)
    fitness: float | None = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """A snapshot of one complete generation in the evolutionary loop.

    After every generation the ``Evolver`` appends one ``GenerationResult``
    to its history list.  This history is later flattened into a DataFrame
    by ``runner.history_to_df()`` for charting and CSV export.

    Attributes
    ----------
    generation : int
        Zero-based generation index (0 = first generation, 1 = second, …).
        The runner and dashboard display this as 1-based for readability.
    candidates : list of Candidate
        All candidates that existed in this generation, sorted best-first
        by fitness at the time of capture.
    best : Candidate
        Shortcut reference to the top-ranked (highest fitness) candidate
        in this generation.  Equivalent to ``candidates[0]``.
    """

    generation: int
    candidates: List[Candidate]
    best: Candidate
