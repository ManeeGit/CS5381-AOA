"""Mutation operators for the Evolve evolutionary search framework.

A *mutation operator* is a function that takes a piece of Python source code
and returns a modified version.  Each operator targets a different structural
level of the code, from numeric-constant tweaks (low impact) to wholesale
function-body replacement (high impact).

All public operators share the same signature::

    operator(code, [templates]) -> (new_code: str, description: str)

The ``description`` is a human-readable log of exactly what changed, stored
in the ``Candidate.meta`` dict so every mutation decision is traceable.

Operator hierarchy (by impact)
-------------------------------
1. ``replace_function_body``  (weight 3×)  — swap entire algorithm body.
2. ``replace_fragment``        (weight 2×)  — replace a 3–6 line block.
3. ``reorder_loops``           (weight 1×)  — swap adjacent nested for-loops.
4. ``swap_two_lines``          (weight 1×)  — swap two same-indent non-structural lines.
5. ``random_perturb_parameters`` (weight 1×) — tweak integer literals.
6. ``add_early_return``        (weight 1×)  — add an empty-input guard.

The top-level dispatcher ``mutate_with_meta()`` randomly picks an operator
according to these weights and validates the result.  Syntax errors in the
mutated code trigger an automatic fallback to ``replace_function_body``.
"""
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
    """Swap two non-structural lines that share the same indentation level.

    Structural lines (``def``, ``class``, ``for``, ``while``, ``if``,
    ``elif``, ``else:``, ``try:``, ``except``, ``return``, ``with``,
    ``yield``) are explicitly excluded from swapping because moving them
    almost always breaks the algorithm's control flow while still producing
    syntactically valid code (leading the evaluator to silently accept a
    broken algorithm).

    Only assignment and expression lines at the *same indentation level* are
    candidates for swapping, ensuring that we stay within the same lexical
    scope.

    Parameters
    ----------
    code : str
        Python source code to apply the swap to.

    Returns
    -------
    tuple of (str, str)
        ``(new_code, description)`` where ``description`` identifies the
        two line numbers that were swapped, or explains why swapping was
        skipped.
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
    """Replace a short contiguous block of lines with a snippet from a template.

    A random template is chosen, and a random window of 3–6 consecutive
    lines is extracted from its body (skipping ``class``, ``import``, and
    ``from`` lines).  That snippet is then inserted into the current code at
    a random mid-section position, replacing the same number of lines.

    This operator creates *partial hybrids* — candidates that blend logic
    from two different algorithm families.  Most hybrids evaluate poorly,
    but occasionally the transplanted snippet improves a specific path.

    Parameters
    ----------
    code : str
        Python source code to modify.
    templates : list of str
        Pre-written algorithm strings to draw snippets from.

    Returns
    -------
    tuple of (str, str)
        ``(new_code, description)`` identifying the replaced line range,
        or an explanation of why the operation was skipped.
    """
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
    """Replace the entire function body with a body from a randomly chosen template.

    This is the highest-impact mutation operator.  It preserves the current
    file’s header (comments, imports) and the existing function signature
    (the ``def`` line — keeping the function name and argument list) but
    swaps out the entire implementation with the body of a randomly selected
    template algorithm.

    **Why is this powerful?**  Smaller operators like ``swap_two_lines`` can
    only explore the neighbourhood of the current algorithm.  This operator
    jumps the entire population to a completely different point in algorithm
    space (e.g., bubble sort → insertion sort → ``sorted()`` built-in),
    enabling the search to escape local optima that finer-grained mutations
    cannot.

    It is listed with weight 3× in ``mutate_with_meta`` so it is chosen
    roughly one-third of the time.

    Parameters
    ----------
    code : str
        Current Python source code whose function body will be replaced.
    templates : list of str
        Pre-written algorithm strings; one is chosen at random as the donor.

    Returns
    -------
    tuple of (str, str)
        ``(new_code, description)``.  ``new_code`` keeps the original
        signature but has the template’s body.  Returns ``(code, reason)``
        unchanged if no suitable template or function is found.
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
    """Insert an early-return guard clause for trivially sorted inputs.

    Adds the following two lines immediately after the ``def`` line of the
    first function found in the code::

        if len(arr) <= 1:
            return arr[:]

    This is a standard algorithmic optimisation: if the input is empty or
    has only one element it is already sorted, so no further work is needed.
    For practical inputs this rarely changes the fitness score, but it is a
    valid best-practice improvement that good sorting algorithms should have.

    The operator is idempotent — if a guard already exists it returns the
    code unchanged.

    Parameters
    ----------
    code : str
        Python source code of a sorting function.

    Returns
    -------
    tuple of (str, str)
        ``(new_code, description)`` confirming whether the guard was added
        or was already present.
    """
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
    """Swap the order of two adjacent nested for-loops (matrix cache optimisation).

    Scans the source code for the first pair of consecutive ``for`` lines
    where the second loop is indented deeper (i.e., it is genuinely nested
    inside the first).  It then swaps the two loop headers — effectively
    changing the loop traversal order.

    **Why does this matter for matrix multiply?**
    The standard i-j-k loop order accesses column ``b[k][j]`` non-sequentially
    in memory, causing cache misses.  The i-k-j order accesses ``b[k][j]``
    sequentially in the inner-most loop, which is cache-friendly and
    measurably faster on real hardware.  The fitness function rewards fewer
    arithmetic operations, so this can produce a small but real improvement.

    Parameters
    ----------
    code : str
        Python source code potentially containing nested for-loops.

    Returns
    -------
    tuple of (str, str)
        ``(new_code, description)`` identifying the swapped line numbers,
        or an explanation if no suitable nested loops were found.
    """
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
    """Apply one randomly selected mutation and return the modified code.

    Convenience wrapper around ``mutate_with_meta`` that discards the
    provenance metadata.  Use this when only the new code is needed and
    logging is not required.

    Parameters
    ----------
    code : str
        Python source code to mutate.
    templates : list of str
        Algorithm template strings used by replacement operators.

    Returns
    -------
    str
        Mutated Python source code.  Guaranteed to be syntactically valid
        (the dispatcher falls back to ``replace_function_body`` on syntax
        errors).
    """
    new_code, _ = mutate_with_meta(code, templates)
    return new_code


def mutate_with_meta(code: str, templates: List[str]) -> Tuple[str, Dict[str, str]]:
    """Apply one randomly selected mutation and return the result with metadata.

    This is the primary entry point used by ``Evolver`` when producing
    children.  It selects an operator from a weighted list, applies it,
    validates the result, and returns both the new code and a provenance
    dictionary that is stored in ``Candidate.meta`` for full traceability.

    Operator selection weights
    --------------------------
    Operators are represented multiple times in the list to implement
    integer weights without extra logic:

    * ``replace_function_body``  ×3 (33 % chance)
    * ``replace_fragment``       ×2 (22 % chance)
    * ``reorder_loops``          ×1 (11 % chance)
    * ``swap_two_lines``         ×1 (11 % chance)
    * ``random_perturb_parameters`` ×1 (11 % chance)
    * ``add_early_return``       ×1 (11 % chance)

    Syntax-error fallback
    ---------------------
    If the chosen operator produces code that ``ast.parse()`` rejects,
    ``replace_function_body`` is retried as a safe fallback (it always
    produces valid Python when templates are available).  The ``op`` key
    in the returned metadata is prefixed with ``[syntax-fixed]`` to signal
    the fallback was used.

    Parameters
    ----------
    code : str
        Current Python source code to mutate.
    templates : list of str
        Pre-written algorithm strings available as replacement bodies.

    Returns
    -------
    tuple of (str, dict)
        ``(new_code, meta)`` where ``meta`` contains:

        * ``op`` — short operator key (e.g. ``"replace_body"``, ``"swap_lines"``)
        * ``op_description`` — plain-English description of the transformation
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

