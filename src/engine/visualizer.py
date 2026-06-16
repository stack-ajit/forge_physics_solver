"""
src/engine/visualizer.py

Renders all derivation paths as a readable graph-like text representation.
Shows the user every possible route from given variables to the target.
"""

from __future__ import annotations
from typing import List
from src.store.func_store import FuncIndex
from src.engine.graph import Path


def _short(var: str) -> str:
    """Shorten a URI path to its last segment for display."""
    return var.split("/")[-1]


def render_all_paths(paths: List[Path], target: str, given: set, index: FuncIndex) -> str:
    """
    Build a readable multi-path graph representation.

    Returns a string that shows, for each path, the flow of variables
    from given inputs through equations to the target.
    """
    lines = []
    short_target = _short(target)

    lines.append("")
    lines.append("+" + "-" * 58 + "+")
    lines.append(f"|  DERIVATION GRAPH  ->  target: {short_target:<24}|")
    lines.append("+" + "-" * 58 + "+")
    lines.append("")
    lines.append(f"  GIVEN: {{ {', '.join(_short(g) for g in given)} }}")
    lines.append("")

    for i, path in enumerate(paths):
        is_selected = (i == 0)
        tag = "  [SELECTED - shortest]" if is_selected else ""
        lines.append("  " + "=" * 54)
        lines.append(f"  PATH {i+1}   ({path.length} equations){tag}")
        lines.append("  " + "=" * 54)
        lines.append("")

        # Render each equation as a flow block
        for step, fn in enumerate(path.funcs, 1):
            inputs  = [_short(x) for x in index.inputs_of(fn)]
            output  = _short(index.output_of(fn))
            formula = index.label_of(fn)

            # input row
            in_str = " , ".join(inputs)
            lines.append(f"     [{in_str}]")
            lines.append(f"        |")
            lines.append(f"        |  ({formula})")
            lines.append(f"        v")
            lines.append(f"     ( {output} )")
            if step < len(path.funcs):
                lines.append(f"        |")
                lines.append(f"        |  feeds into next step")
                lines.append(f"        v")
            lines.append("")

        lines.append(f"     => {short_target} obtained")
        lines.append("")

    return "\n".join(lines)


def render_compact_paths(paths: List[Path], target: str, index: FuncIndex) -> str:
    """
    A compact one-line-per-path representation.
    Good for quick overview before the detailed graph.
    """
    lines = []
    short_target = _short(target)
    lines.append("")
    lines.append(f"  ALL PATHS TO '{short_target}'  ({len(paths)} found)")
    lines.append("  " + "-" * 54)

    for i, path in enumerate(paths):
        tag = "  <- shortest" if i == 0 else ""
        chain = "  ->  ".join(index.label_of(fn) for fn in path.funcs)
        lines.append(f"  P{i+1} ({path.length}): {chain}{tag}")

    lines.append("")
    return "\n".join(lines)
