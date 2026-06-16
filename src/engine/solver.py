"""
src/engine/solver.py

FORGE V3 -- Two-Phase Physics Solver with type-aware reasoning.

PHASE 1 -- PLAN
    Build dependency graph, find ALL paths, rank, group by answer_type.

PHASE 2 -- EXECUTE
    Execute one representative (shortest) path per answer_type.
    This produces ALL distinct answers, each with its interpretation.

Type-aware selection:
    If the question specifies wanted_type (e.g. "average"),
    the matching path's answer is the primary answer.
    All other answer types are still reported as alternatives.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
from src.store.func_store import FuncIndex
from src.engine.graph import DependencyGraph, PathFinder, PathRanker, Path
from src.engine.executor import execute


@dataclass
class DerivationStep:
    t:        int
    fired:    List[str]
    produced: Dict[str, Any]


@dataclass
class AnswerVariant:
    """One distinct answer, tied to its interpretation."""
    answer_type: str
    value:       Any
    path:        Path
    assumptions: List[str]
    trace:       List[DerivationStep]


@dataclass
class SolverResult:
    success:        bool
    target:         str
    all_paths:      List[Path]
    variants:       List[AnswerVariant]   # one per distinct answer_type
    primary:        Optional[AnswerVariant]  # the one matching wanted_type
    final_K:        Dict[str, Any]

    @property
    def answer(self):
        """Convenience -- the primary answer value."""
        return self.primary.value if self.primary else None

    @property
    def selected_path(self):
        return self.primary.path if self.primary else None

    @property
    def trace(self):
        return self.primary.trace if self.primary else []


# ─────────────────────────────────────────────────────────
# Execute a single path -- returns (value, trace)
# ─────────────────────────────────────────────────────────

def _execute_path(
    given:  Dict[str, Any],
    target: str,
    path:   Path,
    index:  FuncIndex
):
    """Run one specific path wave by wave. Returns (value, trace)."""
    K = dict(given)
    path_funcs = set(path.funcs)
    t = 0
    trace = []

    while target not in K:
        Et = []
        for fn in path_funcs:
            inputs = index.inputs_of(fn)
            output = index.output_of(fn)
            if all(i in K for i in inputs) and output not in K:
                Et.append(fn)
        Et.sort(key=lambda fn: index.priority_of(fn))

        if not Et:
            return None, trace  # could not complete

        produced = {}
        fired = []
        for fn in Et:
            out = index.output_of(fn)
            if out in produced:
                continue
            produced[out] = execute(fn, K)
            fired.append(fn)

        trace.append(DerivationStep(t=t, fired=fired, produced=produced))
        K.update(produced)
        t += 1

    return K[target], trace


# ─────────────────────────────────────────────────────────
# FORGE_SOLVE
# ─────────────────────────────────────────────────────────

def FORGE_SOLVE(
    given:       Dict[str, Any],
    target:      str,
    index:       FuncIndex,
    wanted_type: str = None,
    verbose:     bool = True
) -> SolverResult:
    """
    FORGE_SOLVE V3 -- type-aware physics solver.

    given       : { variable_path -> value }
    target      : variable to find
    wanted_type : "average" | "instantaneous" | "exact" | None
                  if None, no preferred interpretation -- all reported equally
    """

    given_keys = set(given.keys())

    # ── PHASE 1 -- PLAN ──────────────────────────────────────
    graph     = DependencyGraph.build(index)
    finder    = PathFinder(graph=graph, given=given_keys, index=index)
    all_paths = finder.find_all(target)

    if not all_paths:
        if verbose:
            print(f"\n  No derivation path found to {target.split('/')[-1]}")
            print(f"  UNSOLVABLE -- insufficient information")
        return SolverResult(
            success=False, target=target,
            all_paths=[], variants=[], primary=None,
            final_K=dict(given)
        )

    ranker = PathRanker(index)
    ranked = ranker.rank(all_paths)

    # ── Group paths by answer_type ──────────────────────────
    groups = ranker.group_by_type(ranked)

    # ── PHASE 2 -- EXECUTE one shortest path per type ───────
    variants: List[AnswerVariant] = []
    for atype, paths_of_type in groups.items():
        # shortest path of this type
        best = ranker.rank(paths_of_type)[0]
        value, trace = _execute_path(given, target, best, index)
        if value is not None:
            variants.append(AnswerVariant(
                answer_type=atype,
                value=value,
                path=best,
                assumptions=best.all_assumptions(index),
                trace=trace
            ))

    if not variants:
        return SolverResult(
            success=False, target=target,
            all_paths=ranked, variants=[], primary=None,
            final_K=dict(given)
        )

    # ── Choose primary answer ───────────────────────────────
    # If wanted_type given and a matching variant exists, that's primary.
    # Otherwise, the variant from the globally shortest path is primary.
    primary = None
    if wanted_type:
        for v in variants:
            if v.answer_type == wanted_type:
                primary = v
                break
    if primary is None:
        # pick variant whose path is globally shortest
        primary = min(variants, key=lambda v: v.path.length)

    return SolverResult(
        success=True, target=target,
        all_paths=ranked, variants=variants, primary=primary,
        final_K=dict(given)
    )
