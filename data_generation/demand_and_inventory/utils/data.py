import numpy as np
import pandas as pd
from typing_extensions import Literal


class DataSimulator:
    """Simulates weekly demand data with realistic trend, pronounced seasonality,
    holiday effects, and heteroskedastic noise. Generates data from start_date to end_date.
    """

    def __init__(self, start_date: str, end_date: str, seed: int = 42):
        """
        Args:
            start_date (str): Simulation start date in ISO format (e.g., '2020-01-01').
            end_date (str): Simulation end date in ISO format (e.g., '2025-01-01').
            seed (int): Random seed for reproducibility.
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.dates = pd.date_range(start=self.start_date, end=self.end_date, freq="W")
        self.periods = len(self.dates)


        np.random.seed(seed)

    def _simulate_weekly_demand(self) -> pd.Series:
        t = np.arange(self.periods)

        # Create base component
        base = 300

        # 1. Linear Trend 0.4 first 85 weeks, then -0.4 units/ week
        split = 110
        factor = 0.9  # Trend factor
        trend = np.zeros(self.periods)
        trend[:split] = factor * t[:split]  # Increasing trend
        trend[split:] = factor * split #- factor * (t[split:] - split)  # Decreasing trend

        year_index = ((t - 1) // 52).astype(int)

        # Generate different amplitudes per year (example: linearly increasing or random)
        # You can replace this with any logic, e.g., seasonal_amplitudes = [60, 70, 65, ...]
        unique_years = np.max(year_index) + 1
        seasonal_amplitudes = 60 + 10 * np.sin(0.5 * np.arange(unique_years)) 

        week_of_year = self.dates.isocalendar().week
        holiday_effect = np.where((week_of_year >= 51) | (week_of_year <= 1), 15, 0)
        summer_dip = np.where((week_of_year >= 28) & (week_of_year <= 32), -10, 0)

        # Map amplitude to each time step
        amplitude_per_week = seasonal_amplitudes[year_index]

        # Seasonal component with varying amplitude
        seasonal = amplitude_per_week * np.cos(2 * np.pi * (t - 1) / 52)

        # 3. Homoscedastic Noise (constant variance)
        noise = np.random.normal(0, 25, self.periods)  
        
        # 4. Combine components and scale
        demand = base + trend + seasonal + noise + holiday_effect + summer_dip
        demand = np.maximum(demand, 0).round().astype(int)   # Ensure non-negative


        # 5. Create DataFrame
        df = pd.DataFrame({"date": self.dates, "demand": demand})
        df["unique_id"] = "Amoxicillin"
        return df
    
        
    def _simulate_daily_demand(self) -> pd.DataFrame:
        weekly_df = self._simulate_weekly_demand()

        daily_records = []

        for _, row in weekly_df.iterrows():
            week_start = row["date"] - pd.Timedelta(days=6)
            week_demand = row["demand"]

            # Draw 7 samples from a uniform distribution and convert to proportions
            week_day_proportions = np.random.uniform(0.1, 0.3, 7)
            week_day_proportions /= week_day_proportions.sum()  # Normalize to sum

            # Calculate daily demand based on proportions
            daily_demand = (week_demand * week_day_proportions).round().astype(int)

            for i in range(7):
                daily_date = week_start + pd.Timedelta(days=i)
                if daily_date < self.start_date or daily_date > self.end_date:
                    continue
                daily_records.append({
                    "unique_id": "Demand Amoxicillin Fürth",
                    "date": daily_date,
                    "demand": daily_demand[i]
                })

        return pd.DataFrame(daily_records)


    def simulate(self, freq: Literal['weekly', 'daily'] = 'weekly') -> pd.DataFrame:
       
        if freq == 'weekly':
            df = self._simulate_weekly_demand() 
        
        elif freq == 'daily':
            df = self._simulate_daily_demand()
        else:
            raise ValueError("Frequency must be 'weekly' or 'daily'.")

        return df[["unique_id", "date", "demand"]]