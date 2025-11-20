
import pandas as pd
import numpy as np
from scipy.stats import norm
import io



# --- 2. The Policy Calculator ---
class InventoryPolicyCalculator:
    def __init__(self, demand_data_lines):
        """
        Expects a list of strings in CSV format: "DC,Date,Demand"
        """
        # Convert list of strings to a Pandas DataFrame
        csv_string = "\n".join(demand_data_lines)
        self.df = pd.read_csv(io.StringIO(csv_string))
        
        # Ensure correct data types
        self.df['Demand'] = pd.to_numeric(self.df['Demand'])
        self.df['Date'] = pd.to_datetime(self.df['Date'])

    def calculate_parameters(self, lead_time_days=5, service_level=0.95, 
                             ordering_cost=50.0, holding_cost_unit_year=12.0):
        """
        Calculates Q (EOQ) and R (Reorder Point) per DC.
        
        Args:
            lead_time_days (int): Time in days to receive an order.
            service_level (float): Target probability of not stocking out (0.0 to 1.0).
            ordering_cost (float): Fixed cost to place one order (S).
            holding_cost_unit_year (float): Cost to hold 1 unit for 1 year (H).
        """
        
        # Calculate daily statistics per DC
        stats = self.df.groupby('DC')['Demand'].agg(['mean', 'std']).reset_index()
        stats.rename(columns={'mean': 'avg_daily_demand', 'std': 'daily_std_dev'}, inplace=True)

        # 1. Calculate Z-Score based on Service Level (e.g., 0.95 -> 1.645)
        z_score = norm.ppf(service_level)

        # 2. Calculate Reorder Point (R)
        # R = (Avg Daily Demand * Lead Time) + Safety Stock
        # Safety Stock = Z * Daily StdDev * sqrt(Lead Time)
        
        stats['lead_time_demand'] = stats['avg_daily_demand'] * lead_time_days
        stats['safety_stock'] = z_score * stats['daily_std_dev'] * np.sqrt(lead_time_days)
        stats['R_ReorderPoint'] = np.ceil(stats['lead_time_demand'] + stats['safety_stock'])

        # 3. Calculate Order Quantity (Q) using EOQ
        # EOQ = Sqrt( (2 * Annual_Demand * Ordering_Cost) / Holding_Cost )
        # We approximate Annual Demand = Avg Daily Demand * 365
        
        stats['annual_demand'] = stats['avg_daily_demand'] * 365
        stats['Q_OrderQty'] = np.sqrt(
            (2 * stats['annual_demand'] * ordering_cost) / holding_cost_unit_year
        )
        stats['Q_OrderQty'] = np.ceil(stats['Q_OrderQty'])

        return stats