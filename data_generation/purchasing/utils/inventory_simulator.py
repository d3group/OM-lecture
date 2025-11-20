import datetime
import pandas as pd



class InventorySimulator:
    def __init__(self, demand_df, policy_df, lead_time_days):
        self.demand_df = demand_df.sort_values(['DC', 'Date'])
        self.policy_df = policy_df.set_index('DC')
        self.lead_time_days = lead_time_days

    def run(self):
        simulation_results = []
        
        # Iterate over each DC to simulate inventory independently
        for dc in self.demand_df['DC'].unique():
            dc_demand = self.demand_df[self.demand_df['DC'] == dc].copy()
            
            if dc not in self.policy_df.index:
                continue

            # Get Policy Parameters for this DC
            Q = self.policy_df.loc[dc, 'Q_OrderQty']
            R = self.policy_df.loc[dc, 'R_ReorderPoint']

            # Initial State
            # Starting with full inventory (R + Q) to avoid immediate stockout
            current_inventory = R + Q  
            pipeline_orders = [] # List of tuples: (arrival_date, quantity)

            for index, row in dc_demand.iterrows():
                current_date = row['Date']
                daily_demand = row['Demand']
                
                # 1. Receive Orders (Check pipeline)
                # Move items from pipeline to on-hand if they arrive today (or earlier)
                arriving_qty = sum(qty for date, qty in pipeline_orders if date <= current_date)
                pipeline_orders = [(date, qty) for date, qty in pipeline_orders if date > current_date]
                
                current_inventory += arriving_qty

                # 2. Fulfill Demand
                current_inventory -= daily_demand
                
                # 3. Check Inventory Position and Place Order
                # Inventory Position = On Hand + On Order
                on_order_qty = sum(qty for _, qty in pipeline_orders)
                inventory_position = current_inventory + on_order_qty
                
                qty_ordered = 0
                if inventory_position <= R:
                    qty_ordered = Q
                    arrival_date = current_date + datetime.timedelta(days=self.lead_time_days)
                    pipeline_orders.append((arrival_date, Q))
                
                # 4. Log Data
                simulation_results.append({
                    'DC': dc,
                    'Date': current_date,
                    'Demand': daily_demand,
                    'Opening_Inventory': current_inventory + daily_demand, # approx
                    'End_Inventory': current_inventory,
                    'Inventory_Position': inventory_position,
                    'Reorder_Point': R,
                    'Order_Placed_Qty': qty_ordered,
                    'Order_Received_Qty': arriving_qty
                })

        return pd.DataFrame(simulation_results)