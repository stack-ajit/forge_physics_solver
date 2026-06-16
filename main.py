"""
main.py -- FORGE V3 entry point

This is a thin demo wrapper. For the full interactive experience use:
    python solve_question.py

This file just runs a couple of quick demonstrations directly.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from src.store.func_store import FunctionStore, Stor2Ind
from src.engine.solver import FORGE_SOLVE

DATA = os.path.join(os.path.dirname(__file__), "data", "functions", "physics_functions.json")


def report(result, target, unit):
    if not result.success:
        print(f"  RESULT: UNSOLVABLE -- insufficient information")
        return
    for v in result.variants:
        tag = "  <= PRIMARY" if v is result.primary else ""
        print(f"  [{v.answer_type:13s}] {target.split('/')[-1]} = {round(v.value,4)} {unit}{tag}")


if __name__ == "__main__":
    fs    = FunctionStore.from_json(DATA)
    index = Stor2Ind(fs)
    print(f"\nLoaded {fs}\n")

    power_given = {
        "/quant/physia/initial_velocity": 2.0,
        "/quant/physia/final_velocity":   10.0,
        "/quant/physia/time":             4.0,
        "/quant/physia/mass":             3.0,
    }

    print("DEMO 1 -- Power, asking for AVERAGE:")
    r = FORGE_SOLVE(power_given, "/result/phy/power", index, wanted_type="average", verbose=False)
    report(r, "/result/phy/power", "W")

    print("\nDEMO 2 -- Power, asking for INSTANTANEOUS:")
    r = FORGE_SOLVE(power_given, "/result/phy/power", index, wanted_type="instantaneous", verbose=False)
    report(r, "/result/phy/power", "W")

    print("\nDEMO 3 -- Power, NO interpretation specified (reports both):")
    r = FORGE_SOLVE(power_given, "/result/phy/power", index, wanted_type=None, verbose=False)
    report(r, "/result/phy/power", "W")

    print("\nFor the full interactive solver with graphs, run:")
    print("    python solve_question.py\n")
