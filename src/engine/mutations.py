from __future__ import annotations

import ast
import random
from typing import Dict, List, Tuple


# -------------------------------------------------------------------------
# Individual mutation operators
# Each returns (new_code, description) so callers can log what happened.
# -------------------------------------------------------------------------

# Lines starting with these keywords are "structural" — swapping them almost
# always produces syntactically valid but semantically broken code.
_STRUCTURAL_KEYWORDS = (
    "def ", "class ", "for ", "while ", "if ", "elif ", "else:",
    "try:", "except", "return", "with ", "yield",
)


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
    """Swap two non-structural lines at the same indentation level.

    Only swaps assignment / expression lines — never def/for/while/return/if
    lines which would break the algorithm's control flow.
    """
    lines = code.splitlines()

    def _is_swappable(line: str) -> bool:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return False
        return not any(stripped.startswith(kw) for kw in _STRUCTURAL_KEYWORDS)

    # Group swappable lines by indent so we only swap within the same scope
    by_indent: Dict[int, List[int]] = {}
    for idx, line in enumerate(lines):
        if _is_swappable(line):
            indent = len(line) - len(line.lstrip())
            by_indent.setdefault(indent, []).append(idx)

    candidates = [idxs for idxs in by_indent.values() if len(idxs) >= 2]
    if not candidates:
        return code, "Line swap skipped (no safe swappable lines)"

    idxs = random.choice(candidates)
    i, j = random.sample(idxs, 2)
    lines[i], lines[j] = lines[j], lines[i]
    return "\n".join(lines), f"Safely swapped lines {i + 1} and {j + 1} (same indent)"


def replace_fragment(code: str, templates: List[str]) -> Tuple[str, str]:
    """Replace a small random code segment with a short snippet from a template."""
    if not templates:
        return code, "Fragment replacement skipped (no templates)"
    template_lines = random.choice(templates).splitlines()
    body_lines = [l for l in template_lines if not l.startswith(("class ", "import ", "from "))]
    if not body_lines:
        return code, "Fragment replacement skipped (no body lines in template)"
    snippet_len = min(len(body_lines), random.randint(3, 6))
    snip_start = random.randrange(0, max(1, len(body_lines) - snippet_len + 1))
    snippet = body_lines[snip_start: snip_start + snippet_len]

    lines = code.splitlines()
    if len(lines) < 4:
        return code, "Fragment replacement skipped (code too short)"
    insert_at = random.randrange(2, max(3, len(lines) - 2))
    replace_end = min(len(lines) - 2, insert_at + snippet_len)
    new_lines = lines[:insert_at] + snippet + lines[replace_end:]
    return "\n".join(new_lines), f"Replaced lines {insert_at + 1}-{replace_end} with {snippet_len}-line template snippet"


def replace_function_body(code: str, templates: List[str]) -> Tuple[str, str]:
    """Replace the entire body of the first function with a body from a template.

    This is the most powerful random mutation for algorithm-level improvements:
    it swaps the whole implementation while preserving the function signature,
    allowing the population to explore completely different algorithm families
    (e.g. bubble sort → insertion sort → merge sort).
    """
    if not templates:
        return code, "Function body replacement skipped (no templates)"

    # Find the function signature in the current code
    lines = code.splitlines()
    func_line_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("def ")), None)
    if func_line_idx is None:
        return code, "Function body replacement skipped (no function found in code)"

    # Pick a random template and find its function signature
    tpl_lines = random.choice(templates).splitlines()
    tpl_func_idx = next((i for i, l in enumerate(tpl_lines) if l.strip().startswith("def ")), None)
    if tpl_func_idx is None:
        return code, "Function body replacement skipped (no function in template)"

    # Keep the current file's header (comments, imports) + current signature
    # but replace the body with the template's body
    header = lines[:func_line_idx]
    current_sig = lines[func_line_idx]
    tpl_body = tpl_lines[tpl_func_idx + 1:]  # everything after def line in template

    new_code = "\n".join(header + [current_sig] + tpl_body)
    return new_code, "Replaced entire function body with template algorithm"


def add_early_return(code: str) -> Tuple[str, str]:
    """Add an early-return optimisation for empty/single-element input."""
    if "if len(arr) <= 1" in code or "if not arr" in code:
        return code, "Early-return already present"
    lines = code.splitlines()
    # Insert after the def line
    func_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("def ")), None)
    if func_idx is None:
        return code, "Early-return skipped (no function found)"
    indent = "    "
    guard = f"{indent}if len(arr) <= 1:\n{indent}    return arr[:]"
    new_lines = lines[:func_idx + 1] + [guard] + lines[func_idx + 1:]
    return "\n".join(new_lines), "Added early-return guard for empty/single-element input"


def reorder_loops(code: str) -> Tuple[str, str]:
    """Try swapping the order of two adjacent nested for-loops (matrix optimisation)."""
    lines = code.splitlines()
    for i in range(len(lines) - 1):
        if (lines[i].strip().startswith("for ") and
                lines[i + 1].strip().startswith("for ")):
            indent_outer = len(lines[i]) - len(lines[i].lstrip())
            indent_inner = len(lines[i + 1]) - len(lines[i + 1].lstrip())
            if indent_inner > indent_outer:
                # Swap the variable names in the two for-lines
                # e.g. "for i in range(n):" <-> "for j in range(n):"
                lines[i], lines[i + 1] = lines[i + 1], lines[i]
                return "\n".join(lines), f"Swapped nested for-loops at lines {i+1} and {i+2}"
    return code, "Loop reorder skipped (no adjacent nested for-loops found)"


# -------------------------------------------------------------------------
# Top-level mutate function
# -------------------------------------------------------------------------

def mutate(code: str, templates: List[str]) -> str:
    """Apply a random mutation and return the new code (discard description)."""
    new_code, _ = mutate_with_meta(code, templates)
    return new_code


def mutate_with_meta(code: str, templates: List[str]) -> Tuple[str, Dict[str, str]]:
    """Apply a random mutation and return (new_code, meta_dict).

    Operator weights are tuned so that high-impact structural mutations
    (replace_function_body) are used often enough to escape local minima,
    while cheaper perturbation operators fill the rest of the budget.

    The meta dict contains:
    - ``op``: short operation name
    - ``op_description``: human-readable description of the transformation
    """
    ops = [
        # weight 3 — high impact: swap entire algorithm implementation
        ("replace_body",    lambda c: replace_function_body(c, templates)),
        ("replace_body2",   lambda c: replace_function_body(c, templates)),
        ("replace_body3",   lambda c: replace_function_body(c, templates)),
        # weight 2 — medium impact: structural / loop tweaks
        ("replace_fragment", lambda c: replace_fragment(c, templates)),
        ("replace_fragment2", lambda c: replace_fragment(c, templates)),
        ("reorder_loops",    lambda c: reorder_loops(c)),
        # weight 1 — low impact: cosmetic / numeric changes
        ("swap_lines",       lambda c: swap_two_lines(c)),
        ("perturb",          lambda c: random_perturb_parameters(c)),
        ("early_return",     lambda c: add_early_return(c)),
    ]
    op_name, op_fn = random.choice(ops)
    # Normalise op_name (strip trailing digit used for weighting)
    op_key = op_name.rstrip("0123456789")
    new_code, description = op_fn(code)

    # Validate — if the mutation broke syntax, fall back to replace_function_body
    try:
        ast.parse(new_code)
    except SyntaxError:
        new_code, description = replace_function_body(code, templates)
        op_key = "replace_body_fallback"
        description = "[syntax-fixed] " + description

    meta = {
        "op": op_key,
        "op_description": description,
    }
    return new_code, meta

