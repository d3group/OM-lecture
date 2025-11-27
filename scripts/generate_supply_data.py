import os
import numpy as np
import pandas as pd


def _inventory_position(on_hand: int, pipeline: list[int]) -> int:
    """Inventory position = on hand + on order."""
    return on_hand + sum(pipeline)


def generate_supply_data():
    """Generate daily DC orders for the slides."""
    rng = np.random.default_rng(42)  # deterministic

    n_dcs = 17
    n_days = 20
    start_date = "2025-05-06"
    dates = pd.date_range(start=start_date, periods=n_days)

    records = []

    for dc_id in range(1, n_dcs + 1):
        dc_name = f"DC{dc_id}"

        # DC-specific params for variety
        avg_demand = rng.integers(80, 110)
        std_dev = 18
        lead_time = 5  # fixed lead time

        # Order policy
        Q = int(rng.integers(400, 601))  # smaller lot sizes to increase order frequency
        R = max(200, int(avg_demand * lead_time * 1.4))  # tuned to prompt regular orders

        start_factor = float(rng.uniform(1.1, 1.5))
        on_hand = int(R * start_factor)  # start above R to avoid day-1 orders
        pipeline = []  # list of (arrival_idx, qty)

        for i, date in enumerate(dates):
            # Receive arrivals scheduled for today
            received = 0
            remaining_pipeline = []
            for arrival_idx, qty in pipeline:
                if arrival_idx <= i:
                    received += qty
                else:
                    remaining_pipeline.append((arrival_idx, qty))
            pipeline = remaining_pipeline

            # Update on-hand with receipts, then consume demand
            on_hand += received
            demand = int(max(0, rng.normal(avg_demand, std_dev)))
            opening_inv = on_hand
            on_hand = max(0, on_hand - demand)

            # Inventory position after demand (includes pipeline)
            on_order = sum(q for _, q in pipeline)
            ip = _inventory_position(on_hand, [q for _, q in pipeline])

            # Place order if at/below R
            order_placed = 0
            # Do not place an order on day 0 to avoid immediate orders; afterwards follow (Q, R)
            if i > 0 and ip <= R:
                order_placed = Q
                pipeline.append((i + lead_time, Q))
                on_order += Q
                ip += Q

            records.append(
                {
                    "DC": dc_name,
                    "Date": date,
                    "Demand": demand,
                    "Opening_Inventory": opening_inv,
                    "End_Inventory": on_hand,
                    "Inventory_Position": ip,
                    "Reorder_Point": R,
                    "Order_Placed_Qty": order_placed,
                    "Order_Received_Qty": received,
                    "Order_Policy_Q": Q,
                }
            )

    df = pd.DataFrame(records)

    # Natural outcomes only; no artificial injections

    output_dir = "apps/public/data/supply_planning"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "supply_plan_simulation_v2.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated data at {output_path}")

    non_zero_orders = df[df["Order_Placed_Qty"] > 0].shape[0]
    total_rows = df.shape[0]
    print(f"Non-zero orders: {non_zero_orders} out of {total_rows} rows ({non_zero_orders/total_rows:.1%})")


if __name__ == "__main__":
    generate_supply_data()
