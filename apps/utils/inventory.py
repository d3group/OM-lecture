import numpy as np
import pandas as pd
from dataclasses import dataclass
import altair as alt
from scipy.stats import norm



@dataclass
class InventoryConfig:
    order_cost: float        # Fixed cost per order
    holding_cost: float      # Cost per unit held per period
    stockout_cost: float     # Cost per unit shortage
    lead_time: int           # Lead time in periods (days)

class EOQCalculator:
    """
    Computes the Economic Order Quantity (EOQ) for a given demand rate and cost parameters.
    """
    def __init__(self, demand_rate: float, order_cost: float, holding_cost: float):
        self.demand_rate = demand_rate
        self.order_cost = order_cost
        self.holding_cost = holding_cost

    def optimal_order_quantity(self) -> float:
        return np.sqrt(2 * self.demand_rate * self.order_cost / self.holding_cost)

    def total_cost(self, Q: float = None) -> float:
        if Q is None:
            Q = self.optimal_order_quantity()
        return (self.demand_rate / Q) * self.order_cost + (Q / 2) * self.holding_cost
    


class QRPolicy:
    """
    Implements a (Q, R) inventory policy and fits Q and R to minimize total cost.
    """
    def __init__(self, config: InventoryConfig):
        self.config = config
        self.history = None
        self.params = {"Q": None, "R": None, "cost": None, "avg_cost": None}
        self.type = "QR"

    @staticmethod
    def _simulate_cost_jit(demands, Q, R, K, H, S_cost, L):
        """
        Pure-Python / NumPy implementation of the original numba-compiled simulator.
        Logic unchanged: arrivals are scheduled L periods after an order, reorder when
        inventory + future arrivals <= R, and costs accumulated per period.
        """
        n = len(demands)
        # integer arrays for arrivals; use int64 for safety on sums
        arrivals = np.zeros(n, dtype=np.int64)
        inv_level = int(R)
        total_order_cost = 0.0
        total_holding_cost = 0.0
        total_stockout_cost = 0.0

        # Iterate through periods (sequential dynamics require a loop)
        for i in range(n):
            # incorporate any arrivals that occur at this time
            inv_level += int(arrivals[i])

            # sum of arrivals in the next L-1 periods (i .. i+L-1) is the "future" arrival within lead time
            # This mirrors the original logic: future_arrival = np.sum(arrivals[i:i + L])
            if L > 0:
                # slice is efficient in NumPy; cast sum to Python int
                future_arrival = int(arrivals[i:i + L].sum())
            else:
                future_arrival = 0

            # decide whether to place an order
            if inv_level + future_arrival <= R:
                if i + L < n:
                    arrivals[i + L] += int(Q)
                total_order_cost += float(K)

            # serve demand
            d = int(demands[i])
            inv_level -= d

            # holding and stockout calculation
            hold = inv_level if inv_level > 0 else 0
            short = -inv_level if inv_level < 0 else 0

            total_stockout_cost += short * float(S_cost)
            total_holding_cost += hold * float(H)

        average_costs = (total_order_cost + total_holding_cost + total_stockout_cost) / n
        # return float average cost (keeps monetary meaning; previous int truncation removed for accuracy)
        return float(average_costs)

    def _simulate_cost(self, demands: np.ndarray, Q: int = None, R: int = None) -> float:
        """
        Simulates the cost of a (Q, R) policy given demand data.

        Args:
            demands (np.ndarray): Array of demand values.
            Q (int): Order quantity.
            R (int): Reorder point.

        Returns:
            float: Total cost of the policy.
        """
        if Q is None or R is None:
            if self.params["Q"] is not None and self.params["R"] is not None:
                Q = self.params["Q"]
                R = self.params["R"]
            else:
                raise ValueError("Q and R must be specified or set in params.")

        return self._simulate_cost_jit(demands, Q, R,
                                       self.config.order_cost,
                                       self.config.holding_cost,
                                       self.config.stockout_cost,
                                       self.config.lead_time)
    
    def set_params(self, demand: pd.Series, Q: int, R: int):
        """
        Set the parameters for the (Q, R) policy based on historical demand.

        Args:
            demand (pd.Series): Historical demand series.
            Q (int): Order quantity.
            R (int): Reorder point.
        """
        self.params["Q"] = Q
        self.params["R"] = R
        self.params["avg_cost"] = self._simulate_cost(demand.values.astype(np.int64), Q, R)
        self.params["cost"] = self.params["avg_cost"] * len(demand)
        return self 


    def _generate_candidates(self, history: pd.Series):
        mean_demand = history.mean()
        eoq = EOQCalculator(mean_demand, self.config.order_cost, self.config.holding_cost).optimal_order_quantity()
        q_candidates = np.arange(1, int(eoq * 2) + 1)
        r_candidates = np.arange(1, int(eoq * 2) + 1)
        return q_candidates, r_candidates
    


    def fit(self, history: pd.Series, q_candidates=None, r_candidates=None, parallel=False):
        """
        Fit the (Q, R) policy parameters using historical demand data.

        Args:
            history (pd.Series): Historical demand series.
            q_candidates (iterable, optional): Possible Q values.
            r_candidates (iterable, optional): Possible R values.
            parallel (bool): Whether to run simulation in parallel.

        Returns:
            dict: Best parameters {'Q': Q, 'R': R, 'cost': total_cost}.
        """
        self.history = history
        demands = history.values.astype(np.int64)

        if q_candidates is None or r_candidates is None:
            q_candidates, r_candidates = self._generate_candidates(history)

        best_cost = np.inf
        best_Q = 0
        best_R = 0


        # The parallel flag previously used numba.prange; with a NumPy/Python simulator we
        # revert to standard loops. The simulation itself uses NumPy arrays for numeric work.
        for Q in q_candidates:
            for R in r_candidates:
                cost = self._simulate_cost(demands, Q, R)
                if cost < best_cost:
                    best_cost = cost
                    best_Q = Q
                    best_R = R
        best_cost = int(round(best_cost, 0))
        self.params = {'Q': best_Q, 'R': best_R, 'avg_cost': best_cost, 'cost': best_cost * len(history)}
        return self


class InventoryPlotter:
    def __init__(self, demand_df, config: InventoryConfig,
                 date_col: str = "date", demand_col: str = "demand"):
        self.df = demand_df.copy()
        self.date_col = date_col
        self.demand_col = demand_col
        self.config = config
        self.sim_df = None

    def simulate_inventory(self, Q: int, R: int) -> pd.DataFrame:
        dates = self.df[self.date_col].values
        demands = self.df[self.demand_col].values.astype(int)
        n = len(demands)

        inv = np.zeros(n, dtype=int)
        orders = np.zeros(n, dtype=int)
        arrivals = np.zeros(n, dtype=int)

        inv[0] = Q
        L = self.config.lead_time

        for i in range(n):
            if i > 0:
                inv[i] += arrivals[i]
                future_arrival = np.sum(arrivals[i:i + L])
            else:
                future_arrival = 0
            if inv[i] + future_arrival <= R:
                qty = Q
                orders[i] = qty
                if i + L < n:
                    arrivals[i + L] += qty
            if i < n - 1:
                inv[i + 1] = inv[i] - demands[i]

        self.sim_df = pd.DataFrame({
            self.date_col: dates,
            'demand': demands,
            'inventory_level': inv,
            'order_placed': orders,
            'order_arrival': arrivals,
            'reorder_point': R,
            'order_up_to': R + Q
        })
        return self.sim_df

    def plot(self, policy: "QRPolicy"):
        self.simulate_inventory(policy.params['Q'], policy.params['R'])
        self.sim_df['Zero'] = 0.0

        base = (
            alt.Chart(self.sim_df)
            .transform_fold([self.demand_col, 'inventory_level', 'Zero'], as_=['Metric', 'Value'])
            .transform_calculate(
                colorCategory=(
                    "datum.Metric == 'inventory_level' ? 'Inventory' : "
                    "datum.Metric == 'Zero' ? 'Zero' : 'Demand'"
                )
            )
        )

        color_encode = alt.condition(
            (alt.datum.Metric == 'inventory_level') & (alt.datum.Value < 0),
            alt.value('red'),
            alt.Color(
                'colorCategory:N',
                title='Metric',
                scale=alt.Scale(domain=['Demand', 'Inventory', 'Zero'],
                                range=['steelblue', 'orange', 'grey'])
            )
        )

        lines = base.mark_line().encode(
            x=alt.X(f'{self.date_col}:T', title='Date'),
            y=alt.Y('Value:Q', title=''),
            color=color_encode,
            strokeDash=alt.condition(
                alt.datum.Metric == 'Zero',
                alt.value([5, 5]),
                alt.value([])
            )
        )

        points = (
            base.transform_filter("datum.Metric != 'Zero'")
            .mark_point()
            .encode(
                x=alt.X(f'{self.date_col}:T'),
                y=alt.Y('Value:Q'),
                color=color_encode,
                shape=alt.Shape('Metric:N', scale=alt.Scale(
                    domain=[self.demand_col, 'inventory_level'], range=['circle', 'triangle']
                ), legend=None)
            )
        )

        params_text = f"Q={policy.params['Q']}, R={policy.params['R']}"

        return (
            alt.layer(lines, points)
            .properties(title=f'QR-Policy ({params_text}, Avg. Cost: {policy.params["avg_cost"]}, Total Cost: {policy.params["cost"]})',
                        width=800, height=400)
            .resolve_scale(y='independent')
        )


class QRForecasting(QRPolicy):
    """
    Implements a (Q, R) inventory policy using forecast data and newsvendor model.
    """
    def __init__(self, config: InventoryConfig):
        self.config = config
        self.history = None
        self.params = {"Q": None, "R": None, "cost": None, "avg_cost": None}
        self.type = "QR_Forecast"

    def set_params(self, forecast_mean: float, forecast_mae: float, data: pd.DataFrame, Q: int = None, R: int = None):
        """
        Set the parameters for the (Q, R) policy based on forecast statistics.

        Args:
            forecast_mean (float): Mean of the forecast.
            forecast_mae (float): Mean Absolute Error of the forecast.
            data (pd.DataFrame): Historical demand data for cost simulation.
            Q (int, optional): Order quantity. If None, calculated using EOQ.
            R (int, optional): Reorder point. If None, calculated using newsvendor.
        """
        if Q is None:
            # Use EOQ formula
            eoq_calc = EOQCalculator(forecast_mean, self.config.order_cost, self.config.holding_cost)
            Q = int(np.ceil(eoq_calc.optimal_order_quantity()))
        
        if R is None:
            # Use newsvendor formula with forecast error as demand uncertainty
            # Assume forecast error follows normal distribution with std = MAE * sqrt(π/2)
            forecast_std = forecast_mae * np.sqrt(np.pi / 2)
            
            # Critical ratio for newsvendor model
            critical_ratio = self.config.stockout_cost / (self.config.stockout_cost + self.config.holding_cost)
            
            # Safety stock using normal distribution
            safety_stock = norm.ppf(critical_ratio) * forecast_std * np.sqrt(self.config.lead_time)
            
            # Reorder point = expected demand during lead time + safety stock
            R = int(np.ceil(forecast_mean * self.config.lead_time + safety_stock))
        
        self.params["Q"] = Q
        self.params["R"] = R
        
        # Calculate costs using simulation like in QRPolicy
        demands = data['demand'].values.astype(np.int64)
        # Use the unified simulator entry point (pure-Python/NumPy implementation)
        avg_cost = self._simulate_cost(demands, Q, R)
        self.params["avg_cost"] = avg_cost
        self.params["cost"] = avg_cost * len(data)
        
        return self
    
    def fit(self, forecast_mean: float, forecast_mae: float, data: pd.DataFrame):
        """
        Fit the (Q, R) policy parameters using forecast statistics.

        Args:
            forecast_mean (float): Mean of the forecast.
            forecast_mae (float): Mean Absolute Error of the forecast.

        Returns:
            self: Returns self for method chaining.
        """
        return self.set_params(forecast_mean, forecast_mae, data)


class SimpleForecastPlotter:
    """Simple plotter for forecast vs actuals with basic metrics calculation."""
    
    def __init__(self, 
                    history: pd.DataFrame,
                    forecast: pd.DataFrame = pd.DataFrame(),
                    date_col: str = "date",
                    actual_col: str = "demand",
                    forecast_col: str = "forecast"):
        self.history = history.copy()
        self.forecast = forecast.copy()
        self.date_col = date_col
        self.actual_col = actual_col
        self.forecast_col = forecast_col
        self.mae_ = None
        self.mape_ = None
        
    def _calculate_metrics(self):
        """Calculate MAE and MAPE for the forecast period."""
        # Get actual values for forecast period
        forecast_dates = self.forecast[self.date_col]
        actuals_in_forecast = self.history[
            self.history[self.date_col].isin(forecast_dates)
        ][self.actual_col].values
        
        if len(actuals_in_forecast) > 0:
            forecast_values = self.forecast[self.forecast_col].values[:len(actuals_in_forecast)]
            self.mae_ = np.mean(np.abs(actuals_in_forecast - forecast_values))
            self.mape_ = np.mean(np.abs((actuals_in_forecast - forecast_values) / actuals_in_forecast)) * 100

    def plot(self, title: str = "Forecast vs Actuals", model_col: str = "Model") -> alt.Chart:
        """Create a simple forecast plot with metrics."""
        
        # Historical data
        hist_chart = alt.Chart(self.history).mark_line(
            point=True, color='steelblue'
        ).encode(
            x=alt.X(f'{self.date_col}:T', title='Date'),
            y=alt.Y(f'{self.actual_col}:Q', title='Demand'),
            tooltip=[f'{self.date_col}:T', f'{self.actual_col}:Q']
        )
        chart = hist_chart
        
        # Forecast data

        if not self.forecast.empty:

            self._calculate_metrics()

            forecast_chart = alt.Chart(self.forecast).mark_line(
                point=False, color='orange', strokeDash=[5, 5]
            ).encode(
                x=alt.X(f'{self.date_col}:T'),
                y=alt.Y(f'{self.forecast_col}:Q'),
            tooltip=[f'{self.date_col}:T', f'{self.forecast_col}:Q']
            )
            chart += forecast_chart
            

        
        # Combine charts
        chart = chart.resolve_scale(color='independent')
        
        # Add metrics to title
        if self.mae_ is not None and self.mape_ is not None:
            mae = int(round(self.mae_, 0))
            mape = round(self.mape_, 1)
            title += f" (MAE: {mae}, MAPE: {mape:.1f}%)"
        
        return chart.properties(
            title=title,
            width=800,
            height=400
        ).configure_title(
            fontSize=16,
            fontWeight='bold'
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14
        )
    

class SafetyStockPlotter:
    """
    Plot demand during lead time as a normal density and mark safety stock / reorder point
    for a target service level alpha.

    Usage:
        plotter = SafetyStockPlotter(history_df, date_col="date", demand_col="demand")
        chart = plotter.plot(alpha=0.95, lead_time=7)
    """
    def __init__(self, history: pd.DataFrame, date_col: str = "date", demand_col: str = "demand"):
        self.history = history.copy()
        self.date_col = date_col
        self.demand_col = demand_col

    def plot(self,
                alpha: float,
                lead_time: int,
                use_sample_stats: bool = True,
                mean_daily: float = None,
                std_daily: float = None,
                points: int = 500) -> alt.Chart:
        """
        Create an Altair chart of the Normal(D_L) density with safety stock and R marked.

        Args:
            alpha: target service level (e.g. 0.95).
            lead_time: lead time L (in same time units as daily demand).
            use_sample_stats: if True, estimate mean/std from history.
            mean_daily: if use_sample_stats is False, must provide mean daily demand.
            std_daily: if use_sample_stats is False, must provide daily std dev of demand.
            points: number of points to draw the density.

        Returns:
            alt.Chart: layered chart showing density, mu, R and annotations.
        """
        if use_sample_stats:
            series = self.history[self.demand_col].values.astype(float)
            mean_daily = float(np.mean(series))
            # population std (ddof=0) to match normal assumption
            std_daily = float(np.std(series, ddof=0))
        else:
            if mean_daily is None or std_daily is None:
                raise ValueError("mean_daily and std_daily must be provided when use_sample_stats is False")

        # Avoid zero std
        std_daily = max(std_daily, 1e-9)

        mu_DL = lead_time * mean_daily
        sigma_DL = np.sqrt(lead_time) * std_daily

        z_alpha = float(norm.ppf(alpha))
        R = mu_DL + z_alpha * sigma_DL
        SS = z_alpha * sigma_DL

        # x-range for plotting
        x_min = max(0.0, mu_DL - 4 * sigma_DL)
        x_max = mu_DL + 4 * sigma_DL
        xs = np.linspace(x_min, x_max, points)
        pdf = norm.pdf(xs, loc=mu_DL, scale=sigma_DL)

        plot_df = pd.DataFrame({"x": xs, "pdf": pdf})

        density = (
            alt.Chart(plot_df)
            .mark_area(color="lightsteelblue", opacity=0.7)
            .encode(
                x=alt.X("x:Q", title=f"Demand during lead time (L={lead_time})"),
                y=alt.Y("pdf:Q", title="Density")
            )
        )

        line_mu = (
            alt.Chart(pd.DataFrame({"x": [mu_DL]}))
            .mark_rule(color="black", strokeDash=[4, 4])
            .encode(x="x:Q")
        )

        line_R = (
            alt.Chart(pd.DataFrame({"x": [R]}))
            .mark_rule(color="red")
            .encode(x="x:Q")
        )

        # annotation positions
        ymax = pdf.max()
        ann_df = pd.DataFrame([
            {"x": mu_DL, "y": ymax * 0.95, "text": f"DL = {mu_DL:.1f}"},
            {"x": R, "y": ymax * 0.75, "text": f"R = {R:.1f}"},
            {"x": R, "y": ymax * 0.60, "text": f"SS = {SS:.1f}"},
            {"x": x_min + (x_max - x_min) * 0.02, "y": ymax * 0.95,
                "text": f"Service level α = {alpha:.3f}, z = {z_alpha:.3f}"}
        ])

        annotations = (
            alt.Chart(ann_df)
            .mark_text(align="left", dx=5, fontSize=14)
            .encode(x="x:Q", y="y:Q", text="text:N")
        )

        title = f"Demand Distribution during Lead Time (Normal) — Service level α={alpha:.3f}, z={z_alpha:.3f}"

        chart = (
            alt.layer(density, line_mu, line_R, annotations)
            .properties(title=title, width=700, height=350)
            .configure_title(fontSize=14, fontWeight="bold")
        )

        return chart