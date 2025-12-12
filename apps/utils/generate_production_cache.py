#!/usr/bin/env python3
"""
Pre-compute all production planning optimization solutions for WASM caching.
Run this once locally to generate the cache file.
"""
import json
import numpy as np
import pandas as pd
import pulp
from pathlib import Path

# Generate same data as production_planning.py
products_list = [
    "Amox 500mg (20)", "Amox 875mg (10)", "Amox 1000mg (14)", 
    "Amox/Clav 500/125mg (20)", "Amox/Clav 875/125mg (10)",
    "Ampicillin 500mg (20)", "Fluclox 500mg (20)", "Amox 250mg Chew (20)"
]
months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

# Reproducible random data (same seed as notebook)
np.random.seed(42)
_demand_data = np.random.randint(500, 3000, size=(8, 6))
df_demand = pd.DataFrame(_demand_data, columns=months_list, index=products_list)

_usage_per_unit = np.round(np.random.uniform(0.05, 0.15, size=8), 3)
_batch_sizes = (np.random.randint(5, 20, size=8) * 100).astype(int)
_setup_times = np.round(np.random.uniform(2.0, 5.0, size=8), 1)

df_usage = pd.DataFrame({
    "Hours/Unit": _usage_per_unit,
    "Batch Size": _batch_sizes,
    "Setup Hours": _setup_times
}, index=products_list)


def solve_production_planning(capacity=1500, penalty=5.0, holding=0.5, init_inv=200):
    """Solve the production planning model with given parameters using PuLP + CBC."""
    _batch_sizes = df_usage["Batch Size"].to_dict()
    _run_time = {p: df_usage.loc[p, "Hours/Unit"] * df_usage.loc[p, "Batch Size"] for p in products_list}
    _setup_times = df_usage["Setup Hours"].to_dict()
    _holding_cost = {p: holding for p in products_list}
    _penalty_cost = {p: penalty for p in products_list}
    _M = {p: 20 for p in products_list}
    _I_0 = {p: init_inv for p in products_list}

    model = pulp.LpProblem("ProductionPlanning", pulp.LpMinimize)
    
    y = pulp.LpVariable.dicts("y", (products_list, months_list), lowBound=0, cat='Integer')
    z = pulp.LpVariable.dicts("z", (products_list, months_list), cat='Binary')
    Ip = pulp.LpVariable.dicts("Ip", (products_list, months_list), lowBound=0)
    Im = pulp.LpVariable.dicts("Im", (products_list, months_list), lowBound=0)

    model += pulp.lpSum(
        _holding_cost[p] * Ip[p][t] + _penalty_cost[p] * Im[p][t]
        for p in products_list for t in months_list
    )

    for p in products_list:
        for t_idx, t in enumerate(months_list):
            prev_inv = _I_0[p] if t_idx == 0 else (Ip[p][months_list[t_idx-1]] - Im[p][months_list[t_idx-1]])
            demand = df_demand.loc[p, t]
            production = _batch_sizes[p] * y[p][t]
            model += Ip[p][t] - Im[p][t] == prev_inv + production - demand
            model += y[p][t] <= _M[p] * z[p][t]

    for t in months_list:
        model += pulp.lpSum(
            _run_time[p] * y[p][t] + _setup_times[p] * z[p][t]
            for p in products_list
        ) <= capacity

    # Use CBC solver with time limit
    model.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=120))

    if model.status == pulp.LpStatusOptimal:
        result = {
            "status": "optimal",
            "total_cost": pulp.value(model.objective),
            "total_backorders": sum(Im[p][t].varValue or 0 for p in products_list for t in months_list),
            "total_holding": sum(Ip[p][t].varValue or 0 for p in products_list for t in months_list),
            "solution": {},
            "inventory": {}
        }
        for p in products_list:
            result["solution"][p] = {t: int(y[p][t].varValue or 0) for t in months_list}
            result["inventory"][p] = {t: int((Ip[p][t].varValue or 0) - (Im[p][t].varValue or 0)) for t in months_list}
        return result
    else:
        return {"status": "infeasible"}


def generate_cache():
    """Generate all cached solutions."""
    import time
    
    print("Generating base solution...", flush=True)
    start = time.time()
    cache = {
        "base": solve_production_planning(),  # Default parameters
        "capacity": {},
        "penalty": {},
        "holding": {},
        "init_inv": {}
    }
    print(f"  Base: done ({time.time() - start:.1f}s)", flush=True)

    # Capacity sensitivity: 800-2500, step=100
    cap_values = list(range(800, 2501, 100))
    print(f"Computing capacity sensitivity ({len(cap_values)} values)...", flush=True)
    for i, cap in enumerate(cap_values):
        start = time.time()
        cache["capacity"][str(cap)] = solve_production_planning(capacity=cap)
        print(f"  [{i+1}/{len(cap_values)}] Capacity {cap}: done ({time.time() - start:.1f}s)", flush=True)

    # Penalty cost sensitivity: 1.0-20.0, step=0.5
    pen_values = [x/10.0 for x in range(10, 201, 5)]
    print(f"Computing penalty sensitivity ({len(pen_values)} values)...", flush=True)
    for i, pen in enumerate(pen_values):
        start = time.time()
        cache["penalty"][str(pen)] = solve_production_planning(penalty=pen)
        print(f"  [{i+1}/{len(pen_values)}] Penalty {pen}: done ({time.time() - start:.1f}s)", flush=True)

    # Holding cost sensitivity: 0.1-5.0, step=0.1
    hold_values = [x/10.0 for x in range(1, 51)]
    print(f"Computing holding sensitivity ({len(hold_values)} values)...", flush=True)
    for i, hold in enumerate(hold_values):
        start = time.time()
        cache["holding"][str(hold)] = solve_production_planning(holding=hold)
        print(f"  [{i+1}/{len(hold_values)}] Holding {hold}: done ({time.time() - start:.1f}s)", flush=True)

    # Initial inventory sensitivity: 0-500, step=50
    inv_values = list(range(0, 501, 50))
    print(f"Computing init_inv sensitivity ({len(inv_values)} values)...", flush=True)
    for i, inv in enumerate(inv_values):
        start = time.time()
        cache["init_inv"][str(inv)] = solve_production_planning(init_inv=inv)
        print(f"  [{i+1}/{len(inv_values)}] Init Inv {inv}: done ({time.time() - start:.1f}s)", flush=True)

    return cache


if __name__ == "__main__":
    print("Generating production planning solution cache...")
    cache = generate_cache()
    
    output_path = Path(__file__).parent.parent / "public" / "mps" / "production_cache.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(cache, f, indent=2)
    
    print(f"\nCache saved to: {output_path}")
    print(f"Total solutions: {1 + len(cache['capacity']) + len(cache['penalty']) + len(cache['holding']) + len(cache['init_inv'])}")
