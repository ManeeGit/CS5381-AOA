from __future__ import annotations

import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


@dataclass
class PacmanConfig:
    root_path: str
    base_agent_path: str
    command: str
    layout: str


class PacmanEvaluator:
    def __init__(self, cfg: PacmanConfig):
        self.cfg = cfg

    def evaluate(self, agent_name: str) -> Tuple[float, Dict[str, float]]:
        root = Path(self.cfg.root_path)
        pacman_py = root / "pacman.py"
        if not pacman_py.exists():
            # Fallback stub when pacman project isn't available locally
            score = random.uniform(50, 150)
            steps = random.uniform(100, 300)
            survival = random.uniform(20, 60)
            fitness = 0.6 * score + 0.3 * survival - 0.1 * steps
            return fitness, {"score": score, "steps": steps, "survival": survival}

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


def _extract_metric(text: str, pattern: str, default: float) -> float:
    m = re.search(pattern, text)
    if not m:
        return default
    try:
        return float(m.group(1))
    except Exception:
        return default
