"""
src/engine/executor.py

Maps function names to actual Python computations.
Every function in physics_functions.json has a matching branch here.

To add a new equation:
    1. Add it to physics_functions.json
    2. Add an elif branch here with the math
    The solver loop needs zero changes.
"""

from __future__ import annotations
from typing import Dict, Any
import math


def execute(func_name: str, known: Dict[str, Any]) -> Any:
    """
    Given a function name and the current known set Kt,
    compute and return the output value.

    known  : { variable_path -> value }
    returns: computed numeric output
    """

    def get(path: str) -> float:
        return known[path]

    # ── Kinematics ───────────────────────────────────────────────

    if func_name == "/physi/kinematics/acceleration(u,v,t)":
        # a = (v - u) / t
        u = get("/quant/physia/initial_velocity")
        v = get("/quant/physia/final_velocity")
        t = get("/quant/physia/time")
        return (v - u) / t

    elif func_name == "/physi/kinematics/final_velocity(u,a,t)":
        # v = u + at
        u = get("/quant/physia/initial_velocity")
        a = get("/result/phy/acceleration")
        t = get("/quant/physia/time")
        return u + a * t

    elif func_name == "/physi/kinematics/displacement_uat(u,a,t)":
        # s = ut + 0.5 * a * t^2
        u = get("/quant/physia/initial_velocity")
        a = get("/result/phy/acceleration")
        t = get("/quant/physia/time")
        return u * t + 0.5 * a * t * t

    elif func_name == "/physi/kinematics/displacement_uvt(u,v,t)":
        # s = 0.5 * (u + v) * t
        u = get("/quant/physia/initial_velocity")
        v = get("/quant/physia/final_velocity")
        t = get("/quant/physia/time")
        return 0.5 * (u + v) * t

    elif func_name == "/physi/kinematics/velocity_sq(u,a,s)":
        # v^2 = u^2 + 2as
        u = get("/quant/physia/initial_velocity")
        a = get("/result/phy/acceleration")
        s = get("/result/phy/displacement")
        return u * u + 2 * a * s

    elif func_name == "/physi/kinematics/time_from_uva(u,v,a)":
        # t = (v - u) / a
        u = get("/quant/physia/initial_velocity")
        v = get("/quant/physia/final_velocity")
        a = get("/result/phy/acceleration")
        return (v - u) / a

    # ── Momentum ─────────────────────────────────────────────────

    elif func_name == "/physi/momentum/initial(m,u)":
        # pu = m * u
        m = get("/quant/physia/mass")
        u = get("/quant/physia/initial_velocity")
        return m * u

    elif func_name == "/physi/momentum/final(m,v)":
        # pv = m * v
        m = get("/quant/physia/mass")
        v = get("/quant/physia/final_velocity")
        return m * v

    # ── Kinetic Energy ───────────────────────────────────────────

    elif func_name == "/physi/energy/kinetic_initial(m,u)":
        # Ku = 0.5 * m * u^2
        m = get("/quant/physia/mass")
        u = get("/quant/physia/initial_velocity")
        return 0.5 * m * u * u

    elif func_name == "/physi/energy/kinetic_final(m,v)":
        # Kv = 0.5 * m * v^2
        m = get("/quant/physia/mass")
        v = get("/quant/physia/final_velocity")
        return 0.5 * m * v * v

    # ── Force ────────────────────────────────────────────────────

    elif func_name == "/physi/dynamics/force_from_dp(pu,pv,t)":
        # F = (pv - pu) / t
        pu = get("/result/phy/initial_momentum")
        pv = get("/result/phy/final_momentum")
        t  = get("/quant/physia/time")
        return (pv - pu) / t

    elif func_name == "/physi/dynamics/force_from_ma(m,a)":
        # F = m * a
        m = get("/quant/physia/mass")
        a = get("/result/phy/acceleration")
        return m * a

    # ── Work ─────────────────────────────────────────────────────

    elif func_name == "/physi/energy/work_from_Fs(F,s)":
        # W = F * s
        F = get("/result/phy/force")
        s = get("/result/phy/displacement")
        return F * s

    elif func_name == "/physi/energy/work_from_ke(Kf,Ki)":
        # W = Kv - Ku  (work-energy theorem)
        Kv = get("/result/phy/kinetic_energy_final")
        Ku = get("/result/phy/kinetic_energy_initial")
        return Kv - Ku

    # ── Power ────────────────────────────────────────────────────

    elif func_name == "/physi/power/from_work(W,t)":
        # P = W / t  (average power)
        W = get("/result/phy/work")
        t = get("/quant/physia/time")
        return W / t

    elif func_name == "/physi/power/from_fv(F,v)":
        # P = F * v  (instantaneous power)
        F = get("/result/phy/force")
        v = get("/quant/physia/final_velocity")
        return F * v

    else:
        raise NotImplementedError(
            f"No executor defined for: {func_name}\n"
            f"Add an elif branch in src/engine/executor.py"
        )
