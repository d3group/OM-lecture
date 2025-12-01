import random
import datetime


class DemandGenerator:
    def __init__(self, start_date, end_date, dc_count=16):
        self.start = datetime.date.fromisoformat(start_date)
        self.end = datetime.date.fromisoformat(end_date)
        self.dc_count = dc_count
        self.dates = [
            (self.start + datetime.timedelta(days=i)).isoformat()
            for i in range((self.end - self.start).days + 1)
        ]

    def generate(self):
        lines = []
        # Header for easier pandas parsing later
        lines.append("DC,Date,Demand")
        for dc in range(1, self.dc_count + 1):
            base_avg = random.randint(30, 70)
            for date in self.dates:
                noise = random.randint(-15, 15)
                demand = max(0, base_avg + noise)
                lines.append(f"DC{dc},{date},{demand}")
        return lines

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
