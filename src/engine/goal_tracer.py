"""
src/engine/goal_tracer.py

backward_trace() -- builds minimal U0 from target variable only.

Sir's feedback: U0 = V \ G is too large.
Fix: trace backwards from target, collect only variables
     that are actually on the dependency path to the target.
"""

from __future__ import annotations
from typing import Set
from src.store.func_store import FuncIndex


def backward_trace(target: str, index: FuncIndex) -> Set[str]:
    """
    Starting from target variable, trace backwards through
    FuncIndex to find all variables that could possibly
    contribute to deriving it.

    Returns the minimal set of relevant variables.
    This becomes U0 instead of the entire universe V.

    Example for target = /result/phy/power:
        power  <- needs work, time          via f_power
        work   <- needs force, displacement via f_work
        force  <- needs pu, pv, time        via f_force
        ...
    Only these variables enter U0. Unrelated ones never tracked.
    """
    visited:  Set[str] = set()
    relevant: Set[str] = set()

    def _trace(var: str):
        if var in visited:
            return
        visited.add(var)
        relevant.add(var)

        # which functions produce this variable?
        for func_name in index.funcs_producing(var):
            # what inputs does that function need?
            for inp in index.inputs_of(func_name):
                _trace(inp)

    _trace(target)
    return relevant
