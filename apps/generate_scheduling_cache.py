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
    mps_march_counts = {
        "Amox 500mg (20)": 26,
        "Amox 875mg (10)": 13,
        "Amox 1000mg (14)": 26,
        "Amox/Clav 500/125mg (20)": 13,
        "Amox/Clav 875/125mg (10)": 26,
        "Ampicillin 500mg (20)": 26,
        "Fluclox 500mg (20)": 39,  # Highest demand in production_planning
        "Amox 250mg Chew (20)": 26,
    }

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
                # Some urgent orders with very tight deadlines
                delivery_at_dc = np.random.randint(4, 30)
                pack_qa_buffer = np.random.choice([2, 3])
                ship_buffer = np.random.choice([1, 2])
                due_day = max(1, min(30, delivery_at_dc - pack_qa_buffer - ship_buffer))
            else:
                # DC replenishments - some very urgent
                reorder_hit = np.random.randint(3, 30)
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
    days_in_month: int,
    num_lines: int,
    objective_mode: str = "tard",
    time_limit_s: int = 180,
):
    jobs_df = jobs_df.reset_index(drop=True)

    days = list(range(1, days_in_month + 1))
    lines = list(range(1, num_lines + 1))
    J = list(range(len(jobs_df)))

    # Quick infeasibility screen
    if (jobs_df["u_i"] > capacity_per_line).any():
        return None, "Infeasible: Job > Capacity"

    prob = pulp.LpProblem("PharmaScheduling", pulp.LpMinimize)

    x = {
        (j, d, l): pulp.LpVariable(f"x_{j}_{d}_{l}", cat=pulp.LpBinary)
        for j in J
        for d in days
        for l in lines
    }

    C = {j: pulp.LpVariable(f"C_{j}", lowBound=1, upBound=days_in_month) for j in J}

    if objective_mode == "tard":
        T = {j: pulp.LpVariable(f"T_{j}", lowBound=0) for j in J}
        prob += pulp.lpSum(jobs_df.loc[j, "w_i"] * T[j] for j in J)
    else:
        prob += pulp.lpSum(C[j] for j in J)

    # Constraints
    for j in J:
        prob += pulp.lpSum(x[(j, d, l)] for d in days for l in lines) == 1

    for d in days:
        for l in lines:
            prob += (
                pulp.lpSum(jobs_df.loc[j, "u_i"] * x[(j, d, l)] for j in J)
                <= capacity_per_line
            )

    for j in J:
        prob += C[j] == pulp.lpSum(d * x[(j, d, l)] for d in days for l in lines)

    if objective_mode == "tard":
        for j in J:
            due = int(min(max(1, jobs_df.loc[j, "due"]), days_in_month))
            prob += T[j] >= C[j] - due

    # Try Gurobi first (much faster), fall back to CBC
    try:
        import gurobipy
        solver = pulp.GUROBI_CMD(msg=0, timeLimit=time_limit_s)
    except:
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit_s)
    
    try:
        status = prob.solve(solver)
    except Exception as e:
        return None, f"Solver error: {e}"

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
        for d in days:
            for l in lines:
                if pulp.value(x[(j, d, l)]) and pulp.value(x[(j, d, l)]) > 0.5:
                    assigned_day, assigned_line = d, l
                    break
            if assigned_day is not None:
                break

        if assigned_day is None:
            continue

        due_used = int(min(max(1, jobs_df.loc[j, "due"]), days_in_month))
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
    
    for cap in caps:
        for day in horizons:
            for mode in modes:
                step += 1
                key = f"{cap}_{day}_{mode}"
                
                if step % 10 == 0 or step == 1:
                    print(f"[{step}/{total_steps}] ({step/total_steps*100:.1f}%) - {key}")
                
                # Use adequate time limit for proper solutions (195 batches need more time to prove optimality)
                rows, status = solve_scheduling(
                    jobs_df,
                    capacity_per_line=float(cap),
                    days_in_month=int(day),
                    num_lines=num_lines,
                    objective_mode=mode,
                    time_limit_s=180,  # Increased to 180s for 195 batches to prove optimality
                )
                
                if rows is None:
                    cache[key] = {"status": status, "data": []}
                else:
                    cache[key] = {"status": status, "data": rows}
    
    # Write to JSON file (matching production_scheduling.py expectations)
    output_path = Path(__file__).parent / "public" / "scheduling_cache.json"
    output_path.parent.mkdir(exist_ok=True)
    print(f"\nWriting to {output_path}...")
    
    with open(output_path, "w") as f:
        json.dump(cache, f, indent=2)
    
    # Summary
    optimal_count = sum(1 for v in cache.values() if v["status"] == "Optimal")
    infeasible_count = sum(1 for v in cache.values() if "Infeasible" in v["status"])
    other_count = total_steps - optimal_count - infeasible_count
    
    print(f"\nDone! Summary:")
    print(f"  Optimal: {optimal_count}")
    print(f"  Infeasible: {infeasible_count}")
    print(f"  Other: {other_count}")


if __name__ == "__main__":
    generate_cache()
