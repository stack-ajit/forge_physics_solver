"""
src/engine/graph.py

Phase 1 of FORGE V2 algorithm:

DependencyGraph -- variable -> equation -> variable graph
PathFinder      -- finds ALL complete paths from G to target
PathRanker      -- ranks by length, selects shortest
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from src.store.func_store import FuncIndex


# ─────────────────────────────────────────────────────────
# Path -- one complete derivation route
# ─────────────────────────────────────────────────────────

@dataclass
class Path:
    """
    A complete derivation path from G to target.

    funcs  : ordered list of equation names to execute
    length : number of equations (shorter = more efficient)
    """
    funcs:  List[str]
    length: int = 0

    def __post_init__(self):
        self.length = len(self.funcs)

    def describe(self, index: FuncIndex) -> str:
        return " -> ".join(index.label_of(fn) for fn in self.funcs)

    def final_func(self) -> str:
        """The last equation -- the one that produces the target."""
        return self.funcs[-1] if self.funcs else ""

    def answer_type(self, index: FuncIndex) -> str:
        """
        The answer_type of a path = the answer_type of its final equation
        (the one producing the target). This determines what KIND of
        answer the path yields: exact, average, instantaneous, etc.
        """
        return index.answer_type_of(self.final_func())

    def all_assumptions(self, index: FuncIndex) -> List[str]:
        """Union of all assumptions made by every equation on this path."""
        seen = []
        for fn in self.funcs:
            for a in index.assumptions_of(fn):
                if a not in seen:
                    seen.append(a)
        return seen


# ─────────────────────────────────────────────────────────
# DependencyGraph
# ─────────────────────────────────────────────────────────

@dataclass
class DependencyGraph:
    """
    Directed graph where:
        nodes = variables
        edges = equations

    backward[var] = list of (func_name, [input_vars])
                    that can produce var.

    Used by PathFinder to trace all routes from G to target.
    """
    backward: Dict[str, List[Tuple[str, List[str]]]] = field(default_factory=dict)

    @classmethod
    def build(cls, index: FuncIndex) -> "DependencyGraph":
        """Build backward graph from FuncIndex."""
        backward: Dict[str, List] = {}

        for fn_name, inputs in index.f2i.items():
            output = index.output_of(fn_name)
            if output not in backward:
                backward[output] = []
            backward[output].append((fn_name, inputs))

        return cls(backward=backward)

    def producers_of(self, var: str) -> List[Tuple[str, List[str]]]:
        """Return all (func_name, inputs) that can produce var."""
        return self.backward.get(var, [])


# ─────────────────────────────────────────────────────────
# PathFinder -- recursive backward DFS from target
# ─────────────────────────────────────────────────────────

class PathFinder:
    """
    Finds all COMPLETE derivation paths from G to target.

    A path is complete when every variable needed is either:
        - already in G (a given), OR
        - produced by another equation already in the path.

    Uses recursive DFS backward from target.
    """

    def __init__(self, graph: DependencyGraph, given: Set[str], index: FuncIndex):
        self.graph = graph
        self.given = given
        self.index = index

    def find_all(self, target: str) -> List[Path]:
        """
        Find all valid paths to target.
        Returns list of Path objects, deduplicated.
        """
        results: List[List[str]] = []
        self._dfs(
            need=target,
            current_funcs=[],
            resolved=set(self.given),
            visiting=set(),
            results=results
        )

        # deduplicate by frozenset of functions used
        seen   = set()
        unique = []
        for funcs in results:
            key = frozenset(funcs)
            if key not in seen:
                seen.add(key)
                unique.append(Path(funcs=list(funcs)))

        return unique

    def _dfs(
        self,
        need:          str,
        current_funcs: List[str],
        resolved:      Set[str],
        visiting:      Set[str],
        results:       List[List[str]]
    ) -> bool:
        """
        Recursively try to resolve variable `need`.

        need          : variable we are trying to derive right now
        current_funcs : equations collected so far on this path
        resolved      : variables known at this point (G + produced so far)
        visiting      : cycle guard
        results       : collector for complete valid paths
        """

        # Base case -- variable already resolved (given or derived earlier)
        if need in resolved:
            return True

        # Cycle guard -- avoid infinite loops
        if need in visiting:
            return False

        visiting.add(need)

        producers = self.graph.producers_of(need)
        if not producers:
            visiting.discard(need)
            return False

        found_any = False

        for fn_name, inputs in producers:

            # Skip if this equation is already on the current path
            if fn_name in current_funcs:
                continue

            # Try to resolve all inputs of this function
            added_funcs:   List[str] = []
            added_resolved: Set[str] = set()
            all_resolved = True

            for inp in inputs:
                if inp in resolved or inp in added_resolved:
                    continue

                # Try to resolve this input recursively
                sub_results: List[List[str]] = []
                self._dfs(
                    need=inp,
                    current_funcs=current_funcs + added_funcs,
                    resolved=resolved | added_resolved,
                    visiting=set(visiting),
                    results=sub_results
                )

                if sub_results:
                    # Use first (shortest) sub-resolution found
                    for fn in sub_results[0]:
                        if fn not in current_funcs and fn not in added_funcs:
                            added_funcs.append(fn)
                    # Track what these sub-equations produce
                    for fn in added_funcs:
                        added_resolved.add(self.index.output_of(fn))
                else:
                    if inp not in resolved and inp not in added_resolved:
                        all_resolved = False
                        break

            if all_resolved:
                # All inputs resolvable -- record this as a valid path
                full_path = current_funcs + added_funcs + [fn_name]
                results.append(full_path)
                found_any = True

        visiting.discard(need)
        return found_any


# ─────────────────────────────────────────────────────────
# PathRanker -- rank and select best path
# ─────────────────────────────────────────────────────────

class PathRanker:
    """
    Ranks all found paths and selects the best one.

    Primary  : shortest path (fewest equations)
    Tiebreak : lowest sum of priorities (prefer more fundamental equations)

    Now also supports:
        - type-aware filtering (match requested answer_type)
        - grouping paths by answer_type (for multi-answer reporting)
    """

    def __init__(self, index: FuncIndex):
        self.index = index

    def rank(self, paths: List[Path]) -> List[Path]:
        """Sort paths -- shortest first, then by priority sum."""
        def score(path: Path):
            pri_sum = sum(self.index.priority_of(fn) for fn in path.funcs)
            return (path.length, pri_sum)
        return sorted(paths, key=score)

    def filter_by_type(self, paths: List[Path], wanted_type: str) -> List[Path]:
        """
        Keep only paths whose answer_type matches what the question wants.
        If wanted_type is None or 'any', return all paths unchanged.
        """
        if not wanted_type or wanted_type == "any":
            return paths
        return [p for p in paths if p.answer_type(self.index) == wanted_type]

    def group_by_type(self, paths: List[Path]) -> dict:
        """
        Group paths by their answer_type.
        Returns { answer_type : [paths] }.
        Used for multi-answer reporting (Phase B).
        """
        groups = {}
        for p in paths:
            t = p.answer_type(self.index)
            groups.setdefault(t, []).append(p)
        return groups

    def select(self, paths: List[Path], wanted_type: str = None) -> Path:
        """
        Return the best path.

        If wanted_type is given, first filter to matching paths,
        then pick shortest among them. If no path matches the wanted
        type, fall back to shortest overall (so we still answer).
        """
        candidates = self.filter_by_type(paths, wanted_type)
        if not candidates:
            candidates = paths  # fallback -- no exact type match
        ranked = self.rank(candidates)
        return ranked[0] if ranked else None


# ─────────────────────────────────────────────────────────
# Path report printer
# ─────────────────────────────────────────────────────────

def print_path_report(paths: List[Path], target: str, index: FuncIndex):
    """Print Phase 1 report -- all paths found, ranked, selected marked."""
    short_target = target.split("/")[-1]

    print("\n" + "=" * 60)
    print("  PHASE 1 -- PATH PLANNING")
    print(f"  TARGET : {short_target}")
    print(f"  FOUND  : {len(paths)} derivation path(s)")
    print("=" * 60)

    for i, path in enumerate(paths):
        marker = "  <- SELECTED (shortest)" if i == 0 else ""
        print(f"\n  PATH {i+1}  ({path.length} equation(s)){marker}")
        for step, fn in enumerate(path.funcs, 1):
            print(f"    Step {step} : {index.label_of(fn)}")

    print()
