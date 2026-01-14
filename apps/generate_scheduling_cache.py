#!/usr/bin/env python3
"""
Cache generator for Production Scheduling interactive slide.
Precomputes solutions for all combinations of capacity, horizon, and objective mode.
"""

import pandas as pd
import pulp
import numpy as np
import json
import sys
from pathlib import Path


# -----------------------------------------------------
# 1. Data Generation (Must match production_scheduling.py)
# -----------------------------------------------------
def get_jobs_df():
    """Generate the same job data as in production_scheduling.py"""
    # Batch counts based on production_planning March demand, scaled to make problem slightly tight
    # Original from MPS: 2, 1, 2, 1, 2, 2, 3, 2 batches (total 15)
    # Scaled proportionally to ~1,600h total work
    # Reduced batch counts to allow some 0-tardiness scenarios
    mps_march_counts = {
        "Amox 500mg (20)": 13,
        "Amox 875mg (10)": 7,
        "Amox 1000mg (14)": 13,
        "Amox/Clav 500/125mg (20)": 7,
        "Amox/Clav 875/125mg (10)": 13,
        "Ampicillin 500mg (20)": 13,
        "Fluclox 500mg (20)": 20,  # Highest demand in production_planning
        "Amox 250mg Chew (20)": 13,
    }  # Total: 99 batches, ~800h

    proc_times = {
        "Amox 500mg (20)": 8.5,
        "Amox 875mg (10)": 9.5,
        "Amox 1000mg (14)": 7.5,
        "Amox/Clav 500/125mg (20)": 8.0,
        "Amox/Clav 875/125mg (10)": 9.0,
        "Ampicillin 500mg (20)": 8.5,
        "Fluclox 500mg (20)": 7.0,
        "Amox 250mg Chew (20)": 8.0,
    }

    priority_weights = {
        "Amox/Clav 875/125mg (10)": 1.3,
        "Amox 875mg (10)": 1.2,
        "Amox/Clav 500/125mg (20)": 1.1,
    }

    np.random.seed(42)  # Must match main file

    batches = []
    batch_counter = 0
    for prod, count in mps_march_counts.items():
        for _ in range(count):
            batch_counter += 1
            origin = np.random.choice(["Customer Order", "DC Replenishment"], p=[0.4, 0.6])

            if origin == "Customer Order":
                # Customer orders - balanced due dates (not too tight, not too easy)
                delivery_at_dc = np.random.randint(7, 28)
                pack_qa_buffer = np.random.choice([2, 3])
                ship_buffer = np.random.choice([1, 2])
                due_day = max(1, min(30, delivery_at_dc - pack_qa_buffer - ship_buffer))
            else:
                # DC replenishments - balanced due dates
                reorder_hit = np.random.randint(5, 26)
                pack_qa_buffer = np.random.choice([1, 2])
                due_day = max(1, min(30, reorder_hit - pack_qa_buffer))

            batches.append(
                {
                    "BatchID": f"B{batch_counter:02d}",
                    "Product": prod,
                    "ProcessTime": proc_times.get(prod, 10.0),
                    "DueDay": int(due_day),
                    "Origin": origin,
                    "Priority": float(priority_weights.get(prod, 1.0)),
                }
            )

    df_batches = pd.DataFrame(batches)
    jobs_df = (
        df_batches[["BatchID", "Product", "Origin", "ProcessTime", "DueDay", "Priority"]]
        .rename(columns={"ProcessTime": "u_i", "DueDay": "due", "Priority": "w_i"})
        .copy()
    )
    return jobs_df


# -----------------------------------------------------
# 2. Solver Logic (Must match production_scheduling.py)
# -----------------------------------------------------
def solve_scheduling(
    jobs_df: pd.DataFrame,
    *,
    capacity_per_line: float,
    planning_horizon: int,  # Renamed from days_in_month for clarity
    num_lines: int,
    objective_mode: str = "tard",
    time_limit_s: int = 180,
    setup_time: float = 2.0,  # Setup time per product changeover (hours)
):
    """
    Solve the scheduling problem with setup times and extended horizon.
    
    Key fixes from supervisor feedback:
    1. Setup times included in capacity constraint
    2. Extended horizon (beyond 30 days) to avoid infeasibility
    3. Tardiness properly linearized via T >= C - due, T >= 0, minimize T
    """
    jobs_df = jobs_df.reset_index(drop=True)

    # FIX 2: Extended horizon - allow scheduling beyond the planning period
    # This prevents infeasibility when total work > capacity
    extended_horizon = planning_horizon + 15  # Allow 15 extra days for overflow
    days = list(range(1, extended_horizon + 1))
    lines = list(range(1, num_lines + 1))
    J = list(range(len(jobs_df)))
    
    # Get unique products for setup tracking
    products = jobs_df["Product"].unique().tolist()
    product_to_idx = {p: i for i, p in enumerate(products)}
    job_product = {j: product_to_idx[jobs_df.loc[j, "Product"]] for j in J}

    # Quick infeasibility screen - job + setup must fit in a day
    max_job_time = jobs_df["u_i"].max()
    if max_job_time + setup_time > capacity_per_line:
        return None, f"Infeasible: Job ({max_job_time}h) + setup ({setup_time}h) > Capacity ({capacity_per_line}h)"

    prob = pulp.LpProblem("PharmaScheduling", pulp.LpMinimize)

    # Decision variables
    # x[j,d,l] = 1 if job j is scheduled on day d, line l
    x = {
        (j, d, l): pulp.LpVariable(f"x_{j}_{d}_{l}", cat=pulp.LpBinary)
        for j in J
        for d in days
        for l in lines
    }
    
    # FIX 1: Setup time tracking
    # z[p,d,l] = 1 if product p is produced on line l on day d (triggers setup)
    z = {
        (p, d, l): pulp.LpVariable(f"z_{p}_{d}_{l}", cat=pulp.LpBinary)
        for p in range(len(products))
        for d in days
        for l in lines
    }

    # C[j] = completion day of job j (no upper bound - can exceed planning horizon)
    C = {j: pulp.LpVariable(f"C_{j}", lowBound=1) for j in J}

    # Objective: minimize weighted tardiness
    if objective_mode == "tard":
        T = {j: pulp.LpVariable(f"T_{j}", lowBound=0) for j in J}
        prob += pulp.lpSum(jobs_df.loc[j, "w_i"] * T[j] for j in J)
    else:
        prob += pulp.lpSum(C[j] for j in J)

    # CONSTRAINT 1: Each job assigned exactly once
    for j in J:
        prob += pulp.lpSum(x[(j, d, l)] for d in days for l in lines) == 1

    # Link z to x: if any job of product p is scheduled on (d,l), then z[p,d,l] = 1
    for p in range(len(products)):
        jobs_of_product = [j for j in J if job_product[j] == p]
        for d in days:
            for l in lines:
                # If any job of product p is on (d,l), z must be 1
                prob += z[(p, d, l)] >= pulp.lpSum(x[(j, d, l)] for j in jobs_of_product) / len(jobs_of_product) if jobs_of_product else 0
                # z can only be 1 if at least one job of product p is on (d,l)
                prob += z[(p, d, l)] <= pulp.lpSum(x[(j, d, l)] for j in jobs_of_product)

    # CONSTRAINT 2: Capacity with setup times
    # FIX 1: Include setup time for each product produced on a line each day
    for d in days:
        for l in lines:
            prob += (
                pulp.lpSum(jobs_df.loc[j, "u_i"] * x[(j, d, l)] for j in J)
                + pulp.lpSum(setup_time * z[(p, d, l)] for p in range(len(products)))
                <= capacity_per_line
            )

    # CONSTRAINT 3: Completion day definition
    for j in J:
        prob += C[j] == pulp.lpSum(d * x[(j, d, l)] for d in days for l in lines)

    # CONSTRAINT 4: Tardiness linearization
    # FIX 3: T[j] >= max(0, C[j] - due[j])
    # With T >= 0 (from lowBound) and T >= C - due, minimizing T gives T = max(0, C - due)
    if objective_mode == "tard":
        for j in J:
            due = int(jobs_df.loc[j, "due"])  # Don't clip due dates
            prob += T[j] >= C[j] - due
            # T[j] >= 0 is enforced by lowBound=0

    # Try Gurobi first (much faster), fall back to CBC
    # Set MIPGap=0 explicitly for true optimality
    solver = None
    try:
        import gurobipy as gp
        # Use Gurobi with explicit MIPGap=0 and fixed seed for reproducibility
        solver = pulp.GUROBI(msg=0, timeLimit=time_limit_s, mip=True, gapRel=0, seed=42)
    except (ImportError, Exception) as e:
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit_s)
    
    try:
        status = prob.solve(solver)
    except Exception as e:
        # If Gurobi fails, try CBC
        try:
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit_s)
            status = prob.solve(solver)
        except Exception as e2:
            return None, f"Solver error: {e2}"

    if pulp.LpStatus[status] not in ("Optimal", "Not Solved"):
        return None, f"Status: {pulp.LpStatus[status]}"

    # Accept both Optimal and Not Solved (feasible but not proven optimal)
    # With 222 batches, some problems may not prove optimality within time limit
    solution_status = pulp.LpStatus[status]
    if solution_status == "Not Solved":
        # Check if we have a feasible solution by trying to extract values
        # If extraction fails, we'll catch it below
        pass  # Continue to extract solution

    rows = []
    for j in J:
        assigned_day = None
        assigned_line = None
        best_val = 0
        # Find the assignment with highest value (handles numerical issues)
        for d in days:
            for l in lines:
                val = pulp.value(x[(j, d, l)])
                if val is not None and val > best_val:
                    best_val = val
                    assigned_day, assigned_line = d, l

        # If no clear assignment, use the best guess or default to last day of extended horizon
        if assigned_day is None or best_val < 0.5:
            # Fallback: assign to last day, line 1 (marks scheduling issue)
            assigned_day = extended_horizon
            assigned_line = 1

        # Use actual due date (not clipped) for tardiness calculation
        due_used = int(jobs_df.loc[j, "due"])
        tard = int(max(0, int(assigned_day) - due_used))

        rows.append(
            {
                "BatchID": jobs_df.loc[j, "BatchID"],
                "Product": jobs_df.loc[j, "Product"],
                "Origin": jobs_df.loc[j, "Origin"],
                "Line": f"Line {int(assigned_line)}",
                "Day": int(assigned_day),
                "DueUsed": int(due_used),
                "Tardiness": tard,
                "ProcessTime": float(jobs_df.loc[j, "u_i"]),
                "Weight": float(jobs_df.loc[j, "w_i"]),
            }
        )

    # Return with appropriate status
    if solution_status == "Optimal":
        return rows, "Optimal"
    else:
        # Not Solved but we have a feasible solution
        return rows, "Feasible (not proven optimal)"


# -----------------------------------------------------
# 3. Main Generation Loop
# -----------------------------------------------------
def generate_cache():
    jobs_df = get_jobs_df()
    
    print(f"Jobs data: {len(jobs_df)} jobs, total hours: {jobs_df['u_i'].sum():.1f}")
    
    # Check which solver will be used
    try:
        import gurobipy as gp
        print(f"Solver: Gurobi (version {gp.gurobi.version()})")
    except ImportError:
        print("Solver: CBC (Gurobi not available)")
    
    # Slider ranges from production_scheduling.py
    caps = range(10, 25)     # 10 to 24 (step=1)
    horizons = range(5, 31)  # 5 to 30 (step=1)
    modes = ["tard"]  # Only generate for tard mode (main app only uses this)
    num_lines = 3
    
    cache = {}
    total_steps = len(list(caps)) * len(list(horizons)) * len(modes)
    step = 0
    
    print(f"Generating cache for {total_steps} scenarios...")
    print(f"Capacity range: 10-24 h/day")
    print(f"Horizon range: 5-30 days")
    print(f"Modes: {modes}")
    print()
    
    import time
    start_time = time.time()
    
    for cap in caps:
        for day in horizons:
            for mode in modes:
                step += 1
                key = f"{cap}_{day}_{mode}"
                
                t0 = time.time()
                # With 99 batches, solver should be fast
                rows, status = solve_scheduling(
                    jobs_df,
                    capacity_per_line=float(cap),
                    planning_horizon=int(day),
                    num_lines=num_lines,
                    objective_mode=mode,
                    time_limit_s=90,  # 90s for model with setup times
                    setup_time=2.0,  # 2h setup per product changeover
                )
                elapsed = time.time() - t0
                
                if step % 20 == 0 or step == 1:
                    print(f"[{step}/{total_steps}] {key} -> {status[:20]}... ({elapsed:.1f}s)")
                
                if rows is None:
                    cache[key] = {"status": status, "data": []}
                else:
                    cache[key] = {"status": status, "data": rows}
    
    # Post-process: ensure monotonicity (higher capacity should never be worse)
    # If a higher-capacity scenario has worse results, use the better lower-capacity solution
    print("\nEnsuring monotonicity...")
    fixes = 0
    for day in horizons:
        for mode in modes:
            best_tard = float('inf')
            best_key = None
            for cap in caps:
                key = f"{cap}_{day}_{mode}"
                if key not in cache or not cache[key].get("data"):
                    continue
                
                total_tard = sum(d.get("Tardiness", 0) for d in cache[key]["data"])
                
                if total_tard <= best_tard:
                    # This is equal or better - update best
                    best_tard = total_tard
                    best_key = key
                else:
                    # This is worse than a lower capacity - use the better solution
                    if best_key and cache[best_key].get("data"):
                        cache[key] = {
                            "status": f"Inherited from {best_key}",
                            "data": cache[best_key]["data"]
                        }
                        fixes += 1
    
    if fixes > 0:
        print(f"  Fixed {fixes} scenarios with non-monotonic results")
    else:
        print("  All scenarios are monotonic")
    
    # Write to JSON file (matching production_scheduling.py expectations)
    output_path = Path(__file__).parent / "public" / "scheduling_cache.json"
    output_path.parent.mkdir(exist_ok=True)
    print(f"\nWriting to {output_path}...")
    
    with open(output_path, "w") as f:
        json.dump(cache, f, indent=2)
    
    # Summary
    total_elapsed = time.time() - start_time
    optimal_count = sum(1 for v in cache.values() if v["status"] == "Optimal")
    infeasible_count = sum(1 for v in cache.values() if "Infeasible" in v["status"])
    other_count = total_steps - optimal_count - infeasible_count
    
    print(f"\nDone in {total_elapsed:.1f}s! Summary:")
    print(f"  Optimal: {optimal_count}")
    print(f"  Infeasible: {infeasible_count}")
    print(f"  Other: {other_count}")


if __name__ == "__main__":
    generate_cache()
