"""Simulate data and produce forecasts.

This script uses DataSimulator to create synthetic demand data and
DemandForecaster (StatsForecast-based) to generate forecasted values.

Example:
  python -m preprocess.main --file-path public/data/forecast_live_session.csv \
	--forecast-path public/data/forecast_live_session_forecasts.csv \
	--start-date 2020-01-01 --end-date 2025-08-01 --frequency daily --h 30
"""

from __future__ import annotations

import argparse
import os
from typing import Literal

import pandas as pd

from preprocess.utils.data import DataSimulator
from preprocess.utils.forecast import DemandForecaster


def _freq_to_pandas(freq: Literal["weekly", "daily"]) -> str:
	return "W" if freq == "weekly" else "D"


def main() -> None:
	parser = argparse.ArgumentParser(description="Simulate and save data, then forecast.")
	parser.add_argument("--file-path", type=str, required=True, help="Output CSV file path for simulated data")
	parser.add_argument("--forecast-path", type=str, required=True, help="Output CSV file path for forecasts")
	parser.add_argument("--start-date", type=str, default="2020-01-01", help="Start date in YYYY-MM-DD format")
	parser.add_argument("--end-date", type=str, default="2025-08-01", help="End date in YYYY-MM-DD format")
	parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
	parser.add_argument(
		"--frequency",
		type=str,
		choices=["weekly", "daily"],
		default="daily",
		help="Frequency of the simulated data (weekly or daily)",
	)
	parser.add_argument("--h", type=int, default=None, help="Forecast horizon (periods). If omitted uses sensible default: 12 for weekly, 30 for daily")

	args = parser.parse_args()

	# Simulate data
	simulator = DataSimulator(start_date=args.start_date, end_date=args.end_date, seed=args.seed)
	df = simulator.simulate(freq=args.frequency)

	# normalize and filter
	df["date"] = pd.to_datetime(df["date"])
	df = df[df["date"] >= pd.to_datetime(args.start_date)].reset_index(drop=True)

	# Ensure output directory exists and save simulated data
	os.makedirs(os.path.dirname(args.file_path), exist_ok=True)
	df.to_csv(args.file_path, index=False)
	print(f"Simulated data saved to: {args.file_path} (rows={len(df)})")

	# Forecasting
	h = args.h
	if h is None:
		h = 12 if args.frequency == "weekly" else 30

	freq_str = _freq_to_pandas(args.frequency)

	# Fit and forecast using DemandForecaster
	try:
		forecaster = DemandForecaster(freq=freq_str)
		# StatsForecast expects sorted time series
		df_sorted = df.sort_values(["unique_id", "date"]).reset_index(drop=True)
		forecaster.fit(df_sorted)
		fc = forecaster.forecast(h=h)

		# fc typically contains columns: unique_id, date, <model aliases...>
		os.makedirs(os.path.dirname(args.forecast_path), exist_ok=True)
		fc.to_csv(args.forecast_path, index=False)
		print(f"Forecasts saved to: {args.forecast_path} (rows={len(fc)})")
	except Exception as exc:  # pragma: no cover - runtime dependency issues possible
		# If StatsForecast or its dependencies are missing, surface a clear message.
		print("Failed to run forecasting step. Ensure 'statsforecast' and its dependencies are installed.")
		print("Exception:", exc)


if __name__ == "__main__":
	main()

