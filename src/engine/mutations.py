from __future__ import annotations

import random
from typing import Dict, List, Tuple


# -------------------------------------------------------------------------
# Individual mutation operators
# Each returns (new_code, description) so callers can log what happened.
# -------------------------------------------------------------------------

def random_perturb_parameters(code: str) -> Tuple[str, str]:
    """Randomly tweak numeric literals by ±1 or ±2."""
    lines = code.splitlines()
    out = []
    changed: List[str] = []
    for line in lines:
        if any(ch.isdigit() for ch in line) and random.random() < 0.2:
            new_line = ""
            for token in line.split():
                if token.isdigit():
                    val = int(token)
                    delta = random.choice([-2, -1, 1, 2])
                    new_token = str(max(0, val + delta))
                    if new_token != token:
                        changed.append(f"{token}→{new_token}")
                    token = new_token
                new_line += token + " "
            out.append(new_line.rstrip())
        else:
            out.append(line)
    desc = f"Perturbed numeric constants: {', '.join(changed)}" if changed else "Parameter perturbation (no change)"
    return "\n".join(out), desc


def swap_two_lines(code: str) -> Tuple[str, str]:
    """Swap two randomly chosen lines of code."""
    lines = code.splitlines()
    if len(lines) < 2:
        return code, "Line swap skipped (too few lines)"
    i, j = random.sample(range(len(lines)), 2)
    lines[i], lines[j] = lines[j], lines[i]
    return "\n".join(lines), f"Swapped lines {i + 1} and {j + 1}"


def replace_fragment(code: str, templates: List[str]) -> Tuple[str, str]:
    """Replace a random code segment with a fragment from the template library."""
    if not templates:
        return code, "Fragment replacement skipped (no templates)"
    template = random.choice(templates)
    lines = code.splitlines()
    if not lines:
        return template, "Replaced entire code with template"
    start = random.randrange(0, len(lines))
    end = min(len(lines), start + max(1, len(template.splitlines()) // 2))
    new_lines = lines[:start] + template.splitlines() + lines[end:]
    return "\n".join(new_lines), f"Replaced lines {start + 1}–{end} with template fragment"


# -------------------------------------------------------------------------
# Top-level mutate function
# -------------------------------------------------------------------------

def mutate(code: str, templates: List[str]) -> str:
    """Apply a random mutation and return the new code (discard description)."""
    new_code, _ = mutate_with_meta(code, templates)
    return new_code


def mutate_with_meta(code: str, templates: List[str]) -> Tuple[str, Dict[str, str]]:
    """Apply a random mutation and return (new_code, meta_dict).

    The meta dict contains:
    - ``op``: short operation name (e.g. ``"perturb"``)
    - ``op_description``: human-readable description of the transformation
    """
    ops = [
        ("perturb", lambda c: random_perturb_parameters(c)),
        ("swap_lines", lambda c: swap_two_lines(c)),
        ("replace_fragment", lambda c: replace_fragment(c, templates)),
    ]
    op_name, op_fn = random.choice(ops)
    new_code, description = op_fn(code)
    meta = {
        "op": op_name,
        "op_description": description,
    }
    return new_code, meta

