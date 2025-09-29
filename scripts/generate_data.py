from apps.utils.data import DataSimulator
import argparse
import os
import pandas as pd

parser = argparse.ArgumentParser(description="Simulate and save data.")
parser.add_argument("--file-path", type=str, required=True, help="Output CSV file path")
parser.add_argument("--start-date", type=str, default="2020-01-01", help="Start date in YYYY-MM-DD format")
parser.add_argument("--end-date", type=str, default="2025-08-01", help="End date in YYYY-MM-DD format")
parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
parser.add_argument("--frequency", type=str, choices=["weekly", "daily"], default="daily",
                    help="Frequency of the simulated data (weekly or daily)")
args = parser.parse_args()



# Simulate data
simulator = DataSimulator(
    start_date=args.start_date, end_date=args.end_date, seed=args.seed
)
df = simulator.simulate(freq=args.frequency)
# Filter data based on start date
df = df[df["date"] >= pd.to_datetime(args.start_date)].reset_index(drop=True)
# Ensure directory exists
os.makedirs(os.path.dirname(args.file_path), exist_ok=True)
# Save to CSV
df.to_csv(args.file_path, index=False)