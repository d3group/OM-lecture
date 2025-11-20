
import pandas as pd
import numpy as np
from scipy.stats import norm
import io



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

    def get_demand_df(self):
        return self.df

    def calculate_parameters(self, lead_time_days=5, service_level=0.95, 
                             ordering_cost=50.0, holding_cost_unit_year=12.0):
        """
        Calculates Q (EOQ) and R (Reorder Point) per DC.
        """
        
        # Calculate daily statistics per DC
        stats = self.df.groupby('DC')['Demand'].agg(['mean', 'std']).reset_index()
        stats.rename(columns={'mean': 'avg_daily_demand', 'std': 'daily_std_dev'}, inplace=True)

        # 1. Calculate Z-Score based on Service Level (e.g., 0.95 -> 1.645)
        z_score = norm.ppf(service_level)

        # 2. Calculate Reorder Point (R)
        # R = (Avg Daily Demand * Lead Time) + Safety Stock
        stats['lead_time_demand'] = stats['avg_daily_demand'] * lead_time_days
        stats['safety_stock'] = z_score * stats['daily_std_dev'] * np.sqrt(lead_time_days)
        stats['R_ReorderPoint'] = np.ceil(stats['lead_time_demand'] + stats['safety_stock'])

        # 3. Calculate Order Quantity (Q) using EOQ
        stats['annual_demand'] = stats['avg_daily_demand'] * 365
        stats['Q_OrderQty'] = np.sqrt(
            (2 * stats['annual_demand'] * ordering_cost) / holding_cost_unit_year
        )
        stats['Q_OrderQty'] = np.ceil(stats['Q_OrderQty'])

        return stats