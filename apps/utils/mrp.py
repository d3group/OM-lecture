import pandas as pd
import numpy as np

class MRPLogic:
    """
    Implements Material Requirements Planning (MRP) logic.
    """
    
    @staticmethod
    def calculate_mrp(
        gross_requirements: pd.Series,
        initial_inventory: int,
        lead_time: int,
        safety_stock: int = 0,
        lot_size_rule: str = "L4L", # L4L (Lot for Lot) or FOQ (Fixed Order Quantity)
        fixed_order_qty: int = 0
    ) -> pd.DataFrame:
        """
        Calculates the MRP table.

        Args:
            gross_requirements (pd.Series): Gross requirements per period. Index should be periods (1..N).
            initial_inventory (int): Starting inventory on hand.
            lead_time (int): Lead time in periods.
            safety_stock (int): Minimum inventory level to maintain.
            lot_size_rule (str): 'L4L' for Lot-for-Lot, 'FOQ' for Fixed Order Quantity.
            fixed_order_qty (int): Quantity for FOQ rule.

        Returns:
            pd.DataFrame: MRP table with columns:
                - Gross Requirements
                - Scheduled Receipts (assumed 0 for now, can be extended)
                - Projected On Hand
                - Net Requirements
                - Planned Order Receipts
                - Planned Order Releases
        """
        n_periods = len(gross_requirements)
        periods = gross_requirements.index
        
        # Initialize arrays
        gross_req = gross_requirements.values
        scheduled_receipts = np.zeros(n_periods, dtype=int) # Placeholder
        projected_on_hand = np.zeros(n_periods, dtype=int)
        net_requirements = np.zeros(n_periods, dtype=int)
        planned_order_receipts = np.zeros(n_periods, dtype=int)
        planned_order_releases = np.zeros(n_periods, dtype=int)
        
        current_inventory = initial_inventory
        
        for i in range(n_periods):
            # 1. Projected On Hand (before replenishment)
            # Inventory from prev period + Scheduled Receipts - Gross Req
            # Note: In standard MRP, Projected On Hand for period t is often calculated 
            # as (On Hand t-1) + (Sched Rec t) + (Planned Rec t) - (Gross Req t)
            # Here we calculate what we HAVE before planning new orders.
            
            # Available for this period from previous
            available = current_inventory + scheduled_receipts[i]
            
            # 2. Net Requirements
            # If available < Gross Req + Safety Stock, we need more.
            # Net Req = (Gross Req + Safety Stock) - Available
            
            if available - gross_req[i] < safety_stock:
                net_req = (gross_req[i] + safety_stock) - available
                net_requirements[i] = net_req
            else:
                net_requirements[i] = 0
                
            # 3. Planned Order Receipts
            if net_requirements[i] > 0:
                if lot_size_rule == "L4L":
                    receipt_qty = net_requirements[i]
                elif lot_size_rule == "FOQ":
                    if fixed_order_qty <= 0:
                        raise ValueError("fixed_order_qty must be > 0 for FOQ")
                    # Multiples of fixed_order_qty
                    num_orders = int(np.ceil(net_requirements[i] / fixed_order_qty))
                    receipt_qty = num_orders * fixed_order_qty
                else:
                    raise ValueError(f"Unknown lot size rule: {lot_size_rule}")
                
                planned_order_receipts[i] = receipt_qty
            else:
                planned_order_receipts[i] = 0
                
            # 4. Projected On Hand (End of Period)
            current_inventory = available + planned_order_receipts[i] - gross_req[i]
            projected_on_hand[i] = current_inventory
            
            # 5. Planned Order Releases
            # Offset by lead time
            release_period = i - lead_time
            if release_period >= 0:
                planned_order_releases[release_period] += planned_order_receipts[i]
                
        # Create DataFrame
        df = pd.DataFrame({
            "Period": periods,
            "Gross Requirements": gross_req,
            "Scheduled Receipts": scheduled_receipts,
            "Projected On Hand": projected_on_hand,
            "Net Requirements": net_requirements,
            "Planned Order Receipts": planned_order_receipts,
            "Planned Order Releases": planned_order_releases
        }).set_index("Period")
        
        return df
