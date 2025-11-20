
import pandas as pd
import os

from .utils.demand_generator import DemandGenerator
from .utils.qr_generator import InventoryPolicyCalculator

# --- 3. Execution Block ---
if __name__ == "__main__":
    print("--- Generating Demand ---")
    # Generate 1 year of data
    gen = DemandGenerator(start_date="2023-01-01", end_date="2023-12-31", dc_count=5)
    raw_data = gen.generate()
    print(f"Generated {len(raw_data)-1} data points.")

    print("\n--- Calculating QR Parameters ---")
    # Configuration for the supply chain context
    calculator = InventoryPolicyCalculator(raw_data)
    
    # Assumptions:
    # Lead Time: 3 days to get goods
    # Service Level: 90% target
    # Ordering Cost: $45 per order
    # Holding Cost: $5.00 per unit per year
    policy_df = calculator.calculate_parameters(
        lead_time_days=3,
        service_level=0.9,
        ordering_cost=45.0,
        holding_cost_unit_year=5.0
    )

    # Display Results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    # Formatting for cleaner output
    output_cols = ['DC', 'avg_daily_demand', 'daily_std_dev', 'safety_stock', 'R_ReorderPoint', 'Q_OrderQty']
    print(policy_df[output_cols].round(2))
    
    # Write results to the specified directory
    output_dir = "../../apps/public/data/supply_planning"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "qr_policy_parameters.csv")
    policy_df.to_csv(output_path, index=False)
    print(f"\nResults written to: {output_path}")

    print("\nInterpretation:")
    example_dc = policy_df.iloc[0]
    print(f"For {example_dc['DC']}:")
    print(f"  - When inventory drops to {int(example_dc['R_ReorderPoint'])} units (Reorder Point)...")
    print(f"  - Order {int(example_dc['Q_OrderQty'])} units (Order Quantity).")
    print(f"  - This accounts for a {int(example_dc['safety_stock'])} unit safety buffer.")