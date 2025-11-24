import pandas as pd
import numpy as np
import os

def generate_supply_data():
    # Parameters
    n_dcs = 16
    # Generate more days to ensure we have enough history/future, but we focus on the 10 day horizon
    n_days = 20 
    start_date = "2025-05-06"
    dates = pd.date_range(start=start_date, periods=n_days)
    
    data = []
    
    for dc_id in range(1, n_dcs + 1):
        dc_name = f"DC{dc_id}"
        
        # DC specific parameters to create variety
        avg_demand = np.random.randint(40, 80)
        std_dev = 10
        # Supplier lead time is rather short (3 days) as requested
        lead_time = 3
        
        # Q, R parameters
        # Make Q smaller to trigger more frequent orders
        # Make R higher to trigger orders sooner
        # We want to ensure orders happen within the first 10 days
        Q = int(avg_demand * 2.0)  # Order roughly every 2 days
        R = int(avg_demand * lead_time * 1.3) # Higher safety stock to trigger early orders
        
        # Start inventory closer to R to trigger immediate orders
        inventory = int(R * 1.05)
        inventory_pos = inventory
        
        pipeline_orders = [] # List of (arrival_date, qty)
        
        for i, date in enumerate(dates):
            # Daily Demand
            demand = int(max(0, np.random.normal(avg_demand, std_dev)))
            
            # Receive orders
            received_qty = 0
            new_pipeline = []
            for arrival_date, qty in pipeline_orders:
                if arrival_date <= i:
                    received_qty += qty
                else:
                    new_pipeline.append((arrival_date, qty))
            pipeline_orders = new_pipeline
            
            # Update Inventory
            opening_inv = inventory
            inventory = max(0, inventory + received_qty - demand)
            end_inv = inventory
            
            # Place Order Logic
            order_placed_qty = 0
            if inventory_pos <= R:
                order_placed_qty = Q
                inventory_pos += Q
                pipeline_orders.append((i + lead_time, Q))
            
            # Update Inventory Position (Inventory + On Order - Backorders)
            # Simplified: Inventory Position tracks what we own (on hand + on order)
            # But here we just decreased it by demand and increased by order placed
            inventory_pos -= demand
            
            data.append({
                "DC": dc_name,
                "Date": date,
                "Demand": demand,
                "Opening_Inventory": opening_inv,
                "End_Inventory": end_inv,
                "Inventory_Position": inventory_pos + demand, # Correction for display
                "Reorder_Point": R,
                "Order_Placed_Qty": order_placed_qty,
                "Order_Received_Qty": received_qty
            })
            
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_dir = "apps/public/data/supply_planning"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "supply_plan_simulation_v2.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated data at {output_path}")
    
    # Verify we have enough non-zero orders
    non_zero_orders = df[df["Order_Placed_Qty"] > 0].shape[0]
    total_rows = df.shape[0]
    print(f"Non-zero orders: {non_zero_orders} out of {total_rows} rows ({non_zero_orders/total_rows:.1%})")

if __name__ == "__main__":
    generate_supply_data()
