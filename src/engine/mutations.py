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
    """Replace a small random code segment with a short snippet from a template."""
    if not templates:
        return code, "Fragment replacement skipped (no templates)"
    template_lines = random.choice(templates).splitlines()
    # Extract a small snippet (3-6 lines) from a random position in the template,
    # skipping import/class header lines to avoid duplicating the class skeleton.
    body_lines = [l for l in template_lines if not l.startswith(("class ", "import ", "from "))]
    if not body_lines:
        return code, "Fragment replacement skipped (no body lines in template)"
    snippet_len = min(len(body_lines), random.randint(3, 6))
    snip_start = random.randrange(0, max(1, len(body_lines) - snippet_len + 1))
    snippet = body_lines[snip_start: snip_start + snippet_len]

    lines = code.splitlines()
    if len(lines) < 4:
        return code, "Fragment replacement skipped (code too short)"
    # Only replace within the body (avoid first 2 and last 2 lines to preserve structure)
    insert_at = random.randrange(2, max(3, len(lines) - 2))
    replace_end = min(len(lines) - 2, insert_at + snippet_len)
    new_lines = lines[:insert_at] + snippet + lines[replace_end:]
    return "\n".join(new_lines), f"Replaced lines {insert_at + 1}–{replace_end} with {snippet_len}-line template snippet"


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

