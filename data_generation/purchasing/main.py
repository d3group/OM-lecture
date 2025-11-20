
import pandas as pd
import os

from .utils.demand_generator import DemandGenerator
from .utils.qr_generator import InventoryPolicyCalculator
from .utils.inventory_simulator import InventorySimulator

if __name__ == "__main__":
    # Configuration
    LEAD_TIME = 2
    SERVICE_LEVEL = 0.7
    NUM_DCS = 16
    ORDER_COST = 10
    HOLDING_COST_UNIT_YEAR = 15.0

    START_DATE = "2025-05-06"
    END_DATE = "2025-05-15"

    NUM_DAYS = (pd.to_datetime(END_DATE) - pd.to_datetime(START_DATE)).days + 1
    
    print("--- 1. Generating Demand ---")
    gen = DemandGenerator(start_date=START_DATE, end_date=END_DATE, dc_count=NUM_DCS)
    raw_data = gen.generate()
    
    print("--- 2. Calculating QR Parameters ---")
    calc = InventoryPolicyCalculator(raw_data)
    policy_df = calc.calculate_parameters(
        lead_time_days=LEAD_TIME,
        service_level=SERVICE_LEVEL,
        ordering_cost=ORDER_COST,
        holding_cost_unit_year=HOLDING_COST_UNIT_YEAR
    )

    # Display Policy Summary
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print("\nPolicy Parameters:")
    print(policy_df[['DC', 'R_ReorderPoint', 'Q_OrderQty']].head())

    print("\n--- 3. Simulating Inventory Levels ---")
    simulator = InventorySimulator(calc.get_demand_df(), policy_df, LEAD_TIME)
    sim_results_df = simulator.run()

    # Show a snippet of the simulation
    print("\nSimulation Snippet (First 10 days of DC1):")
    print(sim_results_df[sim_results_df['DC'] == 'DC1'][['Date', 'End_Inventory', 'Order_Placed_Qty', 'Order_Received_Qty']].head(10))

    # --- 4. Saving Results ---
    output_dir = "apps/public/data/supply_planning"
    os.makedirs(output_dir, exist_ok=True)

    # Print the output directory
    print(f"\nSaving results to directory: {output_dir}")
    
    # Save Parameters
    param_path = os.path.join(output_dir, "qr_policy_parameters.csv")
    policy_df.to_csv(param_path, index=False)
    
    # Save Simulation
    sim_path = os.path.join(output_dir, "supply_plan_simulation.csv")
    sim_results_df.to_csv(sim_path, index=False)
    
    print(f"\nFiles generated successfully in {output_dir}:")
    print(f"1. {os.path.basename(param_path)}")
    print(f"2. {os.path.basename(sim_path)}")