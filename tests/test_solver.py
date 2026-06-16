"""tests/test_solver.py -- FORGE V3 test suite (type-aware)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.store.func_store import FunctionStore, Stor2Ind
from src.engine.solver import FORGE_SOLVE

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "functions", "physics_functions.json")

def load():
    fs = FunctionStore.from_json(DATA)
    return fs, Stor2Ind(fs)

POWER_GIVEN = {
    "/quant/physia/initial_velocity": 2.0,
    "/quant/physia/final_velocity":   10.0,
    "/quant/physia/time":             4.0,
    "/quant/physia/mass":             3.0,
}

def test_store_loads():
    fs, _ = load()
    assert len(fs) > 0
    print(f"PASS  test_store_loads -- {len(fs)} functions")

def test_answer_type_loaded():
    fs, index = load()
    # power from_work should be average, from_fv should be instantaneous
    assert index.answer_type_of("/physi/power/from_work(W,t)") == "average"
    assert index.answer_type_of("/physi/power/from_fv(F,v)") == "instantaneous"
    print("PASS  test_answer_type_loaded")

def test_average_power_correct():
    # wants average -> must be 36 W (W/t), NOT 60 (F*v)
    _, index = load()
    r = FORGE_SOLVE(POWER_GIVEN, "/result/phy/power", index, wanted_type="average", verbose=False)
    assert r.success
    assert abs(r.answer - 36.0) < 0.01, f"Expected 36.0 (average), got {r.answer}"
    print(f"PASS  test_average_power_correct -- {r.answer} W")

def test_instantaneous_power_correct():
    # wants instantaneous -> must be 60 W (F*v)
    _, index = load()
    r = FORGE_SOLVE(POWER_GIVEN, "/result/phy/power", index, wanted_type="instantaneous", verbose=False)
    assert r.success
    assert abs(r.answer - 60.0) < 0.01, f"Expected 60.0 (instantaneous), got {r.answer}"
    print(f"PASS  test_instantaneous_power_correct -- {r.answer} W")

def test_multiple_variants_reported():
    # unspecified -> should produce BOTH average and instantaneous
    _, index = load()
    r = FORGE_SOLVE(POWER_GIVEN, "/result/phy/power", index, wanted_type=None, verbose=False)
    assert r.success
    types = {v.answer_type for v in r.variants}
    assert "average" in types and "instantaneous" in types, f"Got types: {types}"
    print(f"PASS  test_multiple_variants_reported -- {len(r.variants)} variants: {types}")

def test_variants_have_assumptions():
    _, index = load()
    r = FORGE_SOLVE(POWER_GIVEN, "/result/phy/power", index, wanted_type=None, verbose=False)
    for v in r.variants:
        assert isinstance(v.assumptions, list)
    print("PASS  test_variants_have_assumptions")

def test_displacement():
    _, index = load()
    given = {
        "/quant/physia/initial_velocity": 0.0,
        "/result/phy/acceleration":       5.0,
        "/quant/physia/time":             3.0,
    }
    r = FORGE_SOLVE(given, "/result/phy/displacement", index, wanted_type="exact", verbose=False)
    assert r.success
    assert abs(r.answer - 22.5) < 0.01
    print(f"PASS  test_displacement -- {r.answer} m")

def test_acceleration():
    _, index = load()
    given = {
        "/quant/physia/initial_velocity": 5.0,
        "/quant/physia/final_velocity":   25.0,
        "/quant/physia/time":             4.0,
    }
    r = FORGE_SOLVE(given, "/result/phy/acceleration", index, wanted_type="average", verbose=False)
    assert r.success
    assert abs(r.answer - 5.0) < 0.01
    print(f"PASS  test_acceleration -- {r.answer} m/s^2")

def test_deadlock():
    _, index = load()
    given = {"/quant/physia/mass": 3.0, "/result/phy/acceleration": 2.0}
    r = FORGE_SOLVE(given, "/result/phy/power", index, wanted_type="average", verbose=False)
    assert not r.success
    print("PASS  test_deadlock -- correctly UNSOLVABLE")

def test_fallback_when_type_missing():
    # ask for a type that no path produces -> should still answer (fallback)
    _, index = load()
    r = FORGE_SOLVE(POWER_GIVEN, "/result/phy/power", index, wanted_type="total", verbose=False)
    assert r.success, "Should fall back to an answer even if 'total' type doesn't exist"
    print(f"PASS  test_fallback_when_type_missing -- fell back to {r.primary.answer_type}")

if __name__ == "__main__":
    print("\nRunning FORGE V3 test suite...\n")
    test_store_loads()
    test_answer_type_loaded()
    test_average_power_correct()
    test_instantaneous_power_correct()
    test_multiple_variants_reported()
    test_variants_have_assumptions()
    test_displacement()
    test_acceleration()
    test_deadlock()
    test_fallback_when_type_missing()
    print("\nAll tests passed.")
