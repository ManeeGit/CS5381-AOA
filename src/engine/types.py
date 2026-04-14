from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Candidate:
    code: str
    meta: Dict[str, str] = field(default_factory=dict)
    fitness: float | None = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class GenerationResult:
    generation: int
    candidates: List[Candidate]
    best: Candidate
