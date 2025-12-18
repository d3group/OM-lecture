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


def solve_production_planning(capacity=1800, penalty=5.0, holding=0.5, init_inv=200):
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

    # Set timeLimit to 500s, gapRel=0.0 (exact solution)
    model.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=500, gapRel=0.0))

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



def solve_wrapper(kwargs):
    """Helper for parallel execution."""
    return solve_production_planning(**kwargs)

def generate_cache():
    """Generate all cached solutions using parallel processing."""
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from tqdm import tqdm
    
    print("Generating base solution...", flush=True)
    start = time.time()
    
    # Define all tasks
    tasks = []
    
    # Base
    tasks.append(("base", None, {}))
    
    # Capacity: 800-2500, step=100
    for cap in range(800, 2501, 100):
        tasks.append(("capacity", str(cap), {"capacity": cap}))
        
    # Penalty: 1.0-20.0, step=0.5 (Matches slider)
    for i in range(2, 41):
        pen = i * 0.5
        tasks.append(("penalty", str(pen), {"penalty": pen}))
        
    # Holding: 0.1-5.0, step=0.1 (Matches slider)
    # Using integers to avoid float precision issues in loop
    for i in range(1, 51):
        hold = round(i * 0.1, 1)
        tasks.append(("holding", str(hold), {"holding": hold}))

    # Init Inv: 0-500, step=50
    for inv in range(0, 501, 50):
        tasks.append(("init_inv", str(inv), {"init_inv": inv}))
        
    # Interaction Grid: Optimized for speed (matches coarse sliders)
    # Cap: 1500-2400 step 300 => [1500, 1800, 2100, 2400]
    # Pen: 2-20 step 2 => [2.0, 4.0, ..., 20.0] (10 values)
    # Hold: 0.5-2.0 step 0.5 => [0.5, 1.0, 1.5, 2.0] (4 values)
    interaction_caps = [1500, 1800, 2100, 2400]
    interaction_pens = [float(i) for i in range(2, 21, 2)]
    interaction_holds = [0.5, 1.0, 1.5, 2.0]
    
    for c in interaction_caps:
        for p in interaction_pens:
            for h in interaction_holds:
                key = f"{c}_{p}_{h}"
                tasks.append(("interaction", key, {"capacity": c, "penalty": p, "holding": h}))

    print(f"Starting parallel generation of {len(tasks)} tasks (4 workers)...", flush=True)
    
    cache = {
        "base": None,
        "capacity": {},
        "penalty": {},
        "holding": {},
        "init_inv": {},
        "interaction": {}
    }
    
    import os
    # Run with max workers for server execution
    max_workers = os.cpu_count()
    print(f"Using {max_workers} workers...", flush=True)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(solve_wrapper, params): (cat, key) for cat, key, params in tasks}
        
        for future in tqdm(as_completed(futures), total=len(tasks), desc="Progress"):
            cat, key = futures[future]
            try:
                result = future.result()
                if cat == "base":
                    cache["base"] = result
                else:
                    cache[cat][key] = result
            except Exception as e:
                print(f"Error in {cat} {key}: {e}", flush=True)
            
    print(f"All done ({time.time() - start:.1f}s)", flush=True)
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
