import pandas as pd
from typing import Dict, Any, Optional
from utilsforecast.evaluation import evaluate
from utilsforecast.losses import mae, mape
import altair as alt
import os
from typing import List, Union, Dict, Any, Tuple
from enum import Enum
import numpy as np
from typing import Union, Dict, List, Any
from typing import Optional, Union
from statsmodels import api as sm


ModelParam = Dict[str, Any]
ModelParamList = List[ModelParam]
ModelParams = Dict[str, Union[ModelParam, ModelParamList]]


class DemandForecaster:
    """
    Trains and forecasts demand using benchmark and ES models via StatsForecast,
    supporting multiple variants per family.

    Parameters
    ----------
    freq : str
        Pandas frequency string (e.g., 'W' for weekly).
    model_params : Dict[str, Union[Dict, List[Dict]]], optional
        Per-family hyperparameter lists. Keys may include:
          - 'naive':            [{}] or []
          - 'ma':               [{'q': int, 'alias': str}, ...]
          - 'ses':              [{'alpha': float, 'alias': str}, ...]
          - 'holt':             [{'alpha': float, 'beta': float,
                                  'damped': bool, 'alias': str}, ...]
          - 'holt_winters':     [{'season_length': int, 'alpha': float,
                                  'beta': float, 'gamma': float,
                                  'damped': bool, 'alias': str}, ...]
        Each value may be a single dict or a list of dicts; missing entries use one optimized model.
        To skip an entire family, set its value to an empty list.
    """

    def __init__(self, freq: str = "W", model_params: Optional[ModelParams] = None):

        from statsforecast import StatsForecast

        self.freq = freq
        # Normalize params: wrap single dicts into lists
        raw = model_params or {}
        self.model_params: Dict[str, ModelParamList] = {}
        for key, val in raw.items():
            if isinstance(val, dict):
                self.model_params[key] = [val]
            elif isinstance(val, list):
                self.model_params[key] = val
            else:
                raise ValueError(f"model_params['{key}'] must be dict or list of dicts")

        self._build_models()
        self.sf = StatsForecast(models=self.models, freq=self.freq)
        self.sf_optimized = StatsForecast(
            models=self.optimized_models, freq=self.freq
        )

    def _build_models(self):

        from statsforecast.models import (
            Naive,
            WindowAverage,
            SimpleExponentialSmoothing,
            SimpleExponentialSmoothingOptimized,
            Holt,
            HoltWinters,
            AutoETS
        )

        """Instantiate models per family and parameter set."""
        mp = self.model_params
        self.models = []
        self.is_optimized = []

        # 1) Naive: always one if present or default
        for cfg in mp.get("naive", [{}]):
            alias = cfg.get("alias", "Naive")
            self.models.append(Naive(alias=alias))
            self.is_optimized.append(False)

        # 2) Moving Average via ARIMA(0,0,q)
        ma_list = mp.get("ma", [{}])
        for cfg in ma_list:
            q = cfg.get("q")
            alias = cfg.get("alias", f"MA_q{q}" if q is not None else "MA")
            if q is None:
                self.models.append(WindowAverage(window_size=1, alias=alias))
            else:
                self.models.append(WindowAverage(window_size=q, alias=alias))
            self.is_optimized.append(False)

        # 3) Single Exponential Smoothing
        ses_list = mp.get("ses", [{}])
        for cfg in ses_list:
            alpha = cfg.get("alpha")
            alias = cfg.get("alias", f"SES_a{alpha}" if alpha is not None else "SES")
            if alpha is None:
                self.models.append(SimpleExponentialSmoothingOptimized(alias=alias))
                self.is_optimized.append(False)
            else:
                self.models.append(SimpleExponentialSmoothing(alpha=alpha, alias=alias))
                self.is_optimized.append(False)

        # 4) Double Exponential Smoothing (Holt)
        holt_list = mp.get("holt", [{}])
        for cfg in holt_list:
            alpha = cfg.get("alpha")
            beta = cfg.get("beta")
            damped = cfg.get("damped", False)
            alias = cfg.get("alias", "Holt")
            if alpha is None and beta is None:
                self.models.append(Holt(alias=alias))
                self.is_optimized.append(True)
            else:
                raise ValueError("Cannot set Holt parameters")
        # 5) Triple Exponential Smoothing (Holt–Winters)
        hw_list = mp.get("holt_winters", [{}])
        for cfg in hw_list:
            m = cfg.get("season_length", 52)
            alpha = cfg.get("alpha")
            beta = cfg.get("beta")
            gamma = cfg.get("gamma")
            damped = cfg.get("damped", False)
            alias = cfg.get("alias", "Holt-Winters")
            # optimized if no smoothing params
            if alpha is None and beta is None and gamma is None:
                self.models.append(AutoETS(season_length=m, alias=alias, model="AAA", damped=False))
                self.is_optimized.append(True)
            else:
                raise ValueError("Cannot set Holt-Winters parameters")

        self.optimized_models = [
            model for model, is_opt in zip(self.models, self.is_optimized) if is_opt
        ]

            
                

        
    def get_params(self) -> Dict[str, ModelParamList]:
        """
        Get the model parameters used for this forecaster.

        Returns
        -------
        Dict[str, ModelParamList]
            A dictionary with model families as keys and lists of parameter dictionaries as values.
        """
        params = {}
        for model in self.sf_optimized.models:
            if hasattr(model, "model_"):
                params[model.alias] = {
                    'params': model.model_['par'] if 'par' in model.model_ else None,
                    "type": model.__class__.__name__,
                    "alias": model.alias,
                    "hasparams": hasattr(model, "params"),
                }
            else:
                params[model.alias] = {
                    "type": model.__class__.__name__,
                    "alias": model.alias,
                    "hasparams": hasattr(model, "params"),
                }
        return params


    def fit(self, df: pd.DataFrame) -> "DemandForecaster":
        """
        Fit all models on the provided data.

        Parameters
        ----------
        df : pd.DataFrame
            Long-format DataFrame with columns ['unique_id', 'date', 'demand'].
        """
        self.sf.fit(df, id_col="unique_id", time_col="date", target_col="demand")
        self.sf_optimized.fit(df, id_col="unique_id", time_col="date", target_col="demand")
        return self

    def forecast(self, h: int) -> pd.DataFrame:
        """
        Forecast the next `h` periods for all series and models.

        Parameters
        ----------
        h : int
            Forecast horizon (number of periods ahead).

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ['unique_id','date',<model_aliases>].
        """
        return self.sf.predict(h=h)

    def cross_validation(self, **kwargs) -> pd.DataFrame:
        """
        Perform cross-validation on the fitted models.

        Parameters
        ----------
        **kwargs : dict
            Additional parameters for cross-validation.

        Returns
        -------
        pd.DataFrame
            A DataFrame with cross-validation results.
        """

        self.sf_optimized.cross_validation(
            **kwargs, id_col="unique_id", time_col="date", target_col="demand",refit=False)

        return self.sf.cross_validation(
            **kwargs, id_col="unique_id", time_col="date", target_col="demand",
        )


class Evaluator:

    def __init__(
        self,
        forecast: pd.DataFrame,
        historic_forecast: pd.DataFrame= pd.DataFrame(),
        cutoff_col: str = "cutoff",
        date_col: str = "date",
        actual_col: str = "demand",
        unique_id_col: str = "unique_id",
        metric_col: str = "metric",
    ):

        self.forecast = forecast.copy()
        self.historic_forecast = historic_forecast.copy()
        self.cutoff_col = cutoff_col
        self.date_col = date_col
        self.actual_col = actual_col
        self.unique_id_col = unique_id_col
        self.metric_col: str = metric_col

    @staticmethod
    def _rename_metric_columns(df: pd.DataFrame, suffix: str) -> pd.DataFrame:

        return df.rename({"mae": f"mae_{suffix}", "mape": f"mape_{suffix}"})

    def _get_model_columns(self, df: pd.DataFrame) -> List[str]:
        return

    def evaluate(self) -> pd.DataFrame:

        model_cols = [
            col
            for col in self.forecast.columns
            if col
            not in [self.date_col, self.actual_col, self.unique_id_col, self.cutoff_col]
        ]

        evaluation_fc: dict = (
            evaluate(
                df=self.forecast,
                models=model_cols,
                time_col=self.date_col,
                target_col=self.actual_col,
                id_col=self.unique_id_col,
                metrics=[mae, mape],
            )
            .groupby(self.metric_col)[model_cols]
            .mean()
            .to_dict()
        )

        evaluation_hist = (
            evaluate(
                df=self.historic_forecast,
                models=model_cols,
                time_col=self.date_col,
                target_col=self.actual_col,
                id_col=self.unique_id_col,
                metrics=[mae, mape],
            )
            .groupby(self.metric_col)[model_cols]
            .mean()
            .to_dict()
        ) if not self.historic_forecast.empty else None

        # Merge evaluations
        evaluation = {"forecast": evaluation_fc, "history": evaluation_hist}

        return evaluation


class ForecastLoader:
    """
    Manages loading or generating forecasts and historic forecasts using DemandForecaster.

    Attributes:
        forecast_path (str): File path for saving/loading the forecast results.
        historic_path (str): File path for saving/loading the historic forecast results.
    """

    def __init__(
        self,

    ):
        self.date_col = "date"

    def _load(self, path: str) -> pd.DataFrame:
        """
        Loads a DataFrame from CSV or pickle based on file extension.
        """
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path, index_col=0, parse_dates=True)
        elif ext in (".pkl", ".pickle"):
            df = pd.read_pickle(path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
        df[self.date_col] = pd.to_datetime(df[self.date_col])
        return df

        


    def load_data(
        self,
        forecast_path: str,
        historic_path: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load or persist the provided DataFrames to forecast_path / historic_path.
        Does NOT run any forecasting or use DemandForecaster anymore.

        Args:
            data (pd.DataFrame): DataFrame to save/load as the 'forecast' artifact.
            history (pd.DataFrame): DataFrame to save/load as the 'historic forecast' artifact.
            n_windows, step_size, h, historic_n_windows: kept for compatibility but unused.

        Returns:
            If historic_path and historic_n_windows provided: (forecast_df, historic_df)
            Otherwise: forecast_df
        """
        forecast = self._load(forecast_path)

        if historic_path is None:
            return forecast
        else:
            historic_forecast = self._load(historic_path)
            return forecast, historic_forecast


    


class PlotMode(Enum):
    HISTORY = "history"
    FORECAST = "forecast"

    @classmethod
    def from_str(cls, mode: str):
        """Convert a string to a PlotMode enum."""
        if mode.lower() == "history":
            return cls.HISTORY
        elif mode.lower() == "forecast":
            return cls.FORECAST
        else:
            raise ValueError(f"Invalid plot mode: {mode}. Use 'history' or 'forecast'.")


class ForecastPlotter:
    """Handles plotting of history, actuals, forecast with provided performance metrics, via Altair."""

    def __init__(
        self,
        history: pd.DataFrame,
        actuals: pd.DataFrame = pd.DataFrame(),
        forecast: pd.DataFrame = None,
        historic_forecast: pd.DataFrame = None,
        metrics: dict = None,
        date_col: str = "date",
        actual_col: str = "demand",
        xlabel: str = "Date",
        ylabel: str = "Demand",
        history_label: str = "Historical Demand",
        actuals_label: str = "Actuals",
        horizon_label: str = "Forecast Horizon",
    ):
        self.history = history.copy()
        self.actuals = actuals.copy()
        self.forecast = forecast.copy() if forecast is not None else pd.DataFrame()
        self.historic_forecast = (
            historic_forecast.copy()
            if historic_forecast is not None
            else pd.DataFrame()
        )
        self.metrics = metrics
        self.date_col = date_col
        self.actual_col = actual_col
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.history_label = history_label
        self.actuals_label = actuals_label
        self.horizon_label = horizon_label

    def add_forecast(self, forecast: pd.DataFrame):
        """Add forecast DataFrame (must contain date_col and model forecast column)."""
        self.forecast = forecast.copy()
        return

    def add_historic_forecast(self, historic_forecast: pd.DataFrame):
        """Add historic forecast DataFrame (must contain date_col and model forecast column)."""
        self.historic_forecast = historic_forecast.copy()
        return

    def add_metrics(self, metrics: pd.DataFrame):
        """Add performance metrics DataFrame (indexed by metric_col)."""
        self.metrics = metrics.copy()
        return

    def plot(
        self,
        model_col: str = None,
        title: str = "Demand Forecast",
        forecast_label: str = None,
        vertical_line: bool = True,
        shade: bool = True,
        plot_mode: Union[str, PlotMode] = PlotMode.FORECAST,
    ) -> alt.Chart:
        """
        Return an Altair chart with history, actuals, optional forecast, and metrics annotation.
        """

        plot_mode = (
            PlotMode.from_str(plot_mode) if isinstance(plot_mode, str) else plot_mode
        )

        metrics_descr = ""

        # Add metrics text annotation
        if self.metrics and model_col:

            ms = self.metrics[plot_mode.value][model_col]
            mae = int(round(ms["mae"], 0))
            mape = round((ms["mape"] * 100), 1)

            metrics_descr += f" (MAE: {mae}, MAPE: {mape:.1f}%)"

        # Combine history + actuals for base line
        base = pd.concat([self.history, self.actuals], ignore_index=True)

        # Base line chart
        line_all = (
            alt.Chart(base)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    f"{self.date_col}:T",
                    title=self.xlabel,
                    axis=alt.Axis(format="%b %Y"),
                ),
                y=alt.Y(f"{self.actual_col}:Q", title=self.ylabel),
                tooltip=[
                    alt.Tooltip(
                        f"{self.date_col}:T", title=self.xlabel, format="%b %Y"
                    ),
                    alt.Tooltip(
                        f"{self.actual_col}:Q", title=self.ylabel, format=".1f"
                    ),
                ],
            )
            .properties(title=title + metrics_descr)
        )

        layers = [line_all]

        # Forecast layer

        if plot_mode == PlotMode.FORECAST and not self.forecast.empty:

            fc_label = forecast_label or f"{model_col} Forecast"
            line_fc = (
                alt.Chart(self.forecast)
                .mark_line(color="orange")
                .encode(
                    x=alt.X(f"{self.date_col}:T"),
                    y=alt.Y(f"{model_col}:Q"),
                    tooltip=[
                        alt.Tooltip(
                            f"{self.date_col}:T", title=self.xlabel, format="%b %d, %Y"
                        ),
                        alt.Tooltip(f"{model_col}:Q", title=fc_label, format=".2f"),
                    ],
                )
                .properties(name=fc_label)
            )
            layers.append(line_fc)

        elif plot_mode == PlotMode.HISTORY and not self.historic_forecast.empty:

            fc_label = forecast_label or f"{model_col} Forecast"
            line_fc = (
                alt.Chart(self.historic_forecast)
                .mark_line(color="orange")
                .encode(
                    x=alt.X(f"{self.date_col}:T"),
                    y=alt.Y(f"{model_col}:Q"),
                    tooltip=[
                        alt.Tooltip(
                            f"{self.date_col}:T", title=self.xlabel, format="%b %d, %Y"
                        ),
                        alt.Tooltip(f"{model_col}:Q", title=fc_label, format=".2f"),
                    ],
                )
                .properties(name=fc_label)
            )
            layers.append(line_fc)

        # Vertical line for cutoff date

        if vertical_line:

            cutoff_date = (
                self.actuals[self.date_col].min()
                if plot_mode == PlotMode.FORECAST
                else self.historic_forecast[self.date_col].min()
            )
            vline = (
                alt.Chart(pd.DataFrame({"cutoff": [cutoff_date]}))
                .mark_rule(
                    color="blue",
                    strokeDash=[2, 2],  # Creates a dotted line pattern
                    strokeWidth=2,  # Optional: sets the line thickness
                )
                .encode(
                    x=alt.X(
                        "cutoff:T",
                    ),
                    tooltip=alt.Tooltip("cutoff:T", format="%b %d, %Y"),
                )
            )
            layers.append(vline)

            # Add other vertical lines between the cutoff date and the end of the forecast (one line for each 4 weeks)
            end_date = (
                self.actuals[self.date_col].max()
                if plot_mode == PlotMode.FORECAST
                else self.historic_forecast[self.date_col].max()
            )

            n_four_weeks = (end_date - cutoff_date).days // (
                7 * 4
            )  # Number of 4-week intervals

            for i in range(1, n_four_weeks + 1):
                line = (
                    alt.Chart(
                        pd.DataFrame(
                            {"cutoff": [cutoff_date + pd.DateOffset(weeks=i * 4)]}
                        )
                    )
                    .mark_rule(
                        color="blue",
                        strokeDash=[2, 2],  # Creates a dotted line pattern
                        strokeWidth=2,  # Optional: sets the line thickness
                        opacity=0.3,
                    )
                    .encode(
                        x=alt.X("cutoff:T"),
                        tooltip=alt.Tooltip("cutoff:T", format="%b %d, %Y"),
                    )
                )
                layers.append(line)

        # Shaded region for forecast horizon
        if shade:

            # Define the forecast horizon
            start_shade = (
                self.actuals[self.date_col].min()
                if plot_mode == PlotMode.FORECAST
                else self.historic_forecast[self.date_col].min()
            )
            end_shade = (
                self.actuals[self.date_col].max()
                if plot_mode == PlotMode.FORECAST
                else self.historic_forecast[self.date_col].max()
            )

            # Create a DataFrame for the shaded region
            shaded_region = pd.DataFrame({"start": [start_shade], "end": [end_shade]})

            # Create the shaded rectangle
            span = (
                alt.Chart(shaded_region)
                .mark_rect(opacity=0.1, color="grey")
                .encode(x="start:T", x2="end:T")
            )

            # Insert the shaded region at the bottom layer
            layers.insert(0, span)

        # Combine layers
        chart = alt.layer(*layers).resolve_scale(color="independent")

        return (
            chart.configure_title(fontSize=16, fontWeight="bold")
            .configure_axis(labelFontSize=12, titleFontSize=14)
            .properties(width=1000)
        )


class HoltDoubleExpPlotter:
    """
    Adapted for 4-week forecasts per cutoff window with base level, trend, and window separators.
    
    Attributes:
        alpha (float): Level smoothing factor.
        beta (float): Trend smoothing factor.
        history_ (pd.DataFrame): All historical data.
        forecast_df_ (pd.DataFrame): Forecasts with cutoff groups.
        mae_ (float): Mean Absolute Error.
        mape_ (float): Mean Absolute Percentage Error.
        fitted (bool): Whether the model has been fitted.
    """

    def __init__(self):
        self.alpha = None
        self.beta = None
        self.history_ = None
        self.forecast_df_ = None
        self.mae_ = None
        self.mape_ = None
        self.fitted = False

    def _set_params(self, alpha: float, beta: float):
        self.alpha = alpha
        self.beta = beta

    def fit(self, df: pd.DataFrame, alpha: float = 0.8, beta: float = 0.2,
            date_col='date', value_col='demand', cutoff_col='cutoff') -> 'HoltDoubleExpPlotter':
        """
        Fit Holt's method for each cutoff window and forecast 4 weeks ahead.
        """
        self._set_params(alpha, beta)
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df[cutoff_col] = pd.to_datetime(df[cutoff_col])
        df = df.sort_values(date_col)
        self.history_ = df

        forecasts = []
        for cutoff in df[cutoff_col].unique():
            hist_df = df[df[date_col] <= cutoff]
            if len(hist_df) < 2:
                continue
            y = hist_df[value_col].values
            n = len(y)
            level = np.zeros(n)
            trend = np.zeros(n)

            # initial trend via OLS
            X = sm.add_constant(np.arange(n))
            model = sm.OLS(y, X).fit()
            trend[0] = model.params[1]
            level[0] = y[0]

            # smoothing
            for t in range(1, n):
                level[t] = alpha * y[t] + (1 - alpha) * (level[t-1] + trend[t-1])
                trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * trend[t-1]

            # forecast
            future_df = df[df[cutoff_col] == cutoff].copy()
            h = np.arange(1, len(future_df) + 1)
            last_level = level[-1]
            last_trend = trend[-1]
            future_df['forecast'] = last_level + h * last_trend
            future_df['level'] = last_level
            future_df['trend'] = h * last_trend

            forecasts.append(future_df)

        if forecasts:
            self.forecast_df_ = pd.concat(forecasts).sort_values(date_col)
            self._calculate_forecast_error(value_col)
            self.fitted = True
        return self

    def _calculate_forecast_error(self, value_col='demand'):
        if self.forecast_df_ is None:
            return
        y_true = self.forecast_df_[value_col]
        y_pred = self.forecast_df_['forecast']
        self.mae_ = np.mean(np.abs(y_true - y_pred))
        self.mape_ = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    def plot(self) -> alt.Chart:
        """Create plot with observed values, forecast, base level, trend, and cutoff separators."""
        if not self.fitted:
            raise RuntimeError("Model must be fitted before plotting.")

        # Base chart for timeline
        base = alt.Chart(self.history_).encode(x=alt.X('date:T', title='Date'))

        # Observed demand points
        demand = base.mark_point(color='gray', opacity=0.7, size=60).encode(
            y=alt.Y('demand:Q', title='Demand / Component'),
            tooltip=['date:T', 'demand:Q']
        )

        # Prepare long-format DataFrame for Level, Trend, Forecast
        df_long = pd.concat([
            self.forecast_df_.assign(Component='Level', Value=self.forecast_df_['level']),
            self.forecast_df_.assign(Component='Trend', Value=self.forecast_df_['trend']),
            self.forecast_df_.assign(Component='Forecast', Value=self.forecast_df_['forecast']),
        ], ignore_index=True)

        # Line chart with legend
        line_chart = alt.Chart(df_long).mark_line(strokeWidth=3).encode(
            x='date:T',
            y='Value:Q',
            color=alt.Color('Component:N',
                            scale=alt.Scale(
                                domain=['Level', 'Trend', 'Forecast'],
                                range=['#2ca02c', '#ff7f0e', '#1f77b4']
                            ),
                            legend=alt.Legend(title='Component')
            ),
            strokeDash=alt.StrokeDash('Component:N',
                                      scale=alt.Scale(
                                          domain=['Level', 'Trend', 'Forecast'],
                                          range=[[5,5], [5,5], []]
                                      ),
                                      legend=None
            ),
            tooltip=['date:T', 'Component:N', 'Value:Q']
        )

        # Vertical cutoff separators
        cutoffs = self.forecast_df_['cutoff'].unique()
        vlines = alt.Chart(pd.DataFrame({'cutoff': cutoffs})).mark_rule(
            strokeDash=[5, 5], opacity=0.4, strokeWidth=1.5, color='black'
        ).encode(x='cutoff:T')

        # Combine layers
        chart = (demand + line_chart + vlines).properties(width=800, height=400)

        # Add title with error metrics
        if self.mae_ is not None and self.mape_ is not None:
            mae = int(round(self.mae_, 0))
            mape = round(self.mape_, 1)
            title = f"Holt's Double Exp Smoothing (α={self.alpha}, β={self.beta}) - MAE: {mae}, MAPE: {mape}%"
        else:
            title = f"Holt's Double Exp Smoothing (α={self.alpha}, β={self.beta})"

        return chart.properties(title=title).configure_title(
            fontSize=16, anchor='start', fontWeight='bold'
        ).configure_axis(
            labelFontSize=12, titleFontSize=14
        ).configure_legend(
            titleFontSize=13, labelFontSize=12
        )



class HoltWintersPlotter:
    """
    A class for plotting additive Holt-Winters triple exponential smoothing
    (level + trend + seasonality) using Altair.

    Attributes:
        alpha (float): Level smoothing factor.
        beta (float): Trend smoothing factor.
        gamma (float): Seasonal smoothing factor.
        seasonal_periods (int): Number of periods in a season.
        history_ (pd.DataFrame): Original historical data with 'date', 'demand', and optional 'cutoff'.
        level_ (np.ndarray): Smoothed level series.
        trend_ (np.ndarray): Smoothed trend series.
        seasonal_ (np.ndarray): Smoothed seasonal indices.
        forecast_ (np.ndarray): In-sample one-step forecasts.
        fitted (bool): Whether the model has been fitted.
    """
    def __init__(self):
        self.alpha = None
        self.beta = None
        self.gamma = None
        self.seasonal_periods = None
        self.history_ = None
        self.level_ = None
        self.trend_ = None
        self.seasonal_ = None
        self.forecast_ = None
        self.fitted = False

    def _set_params(self, alpha: float, beta: float, gamma: float, seasonal_periods: int):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.seasonal_periods = seasonal_periods

    def fit(self, df: pd.DataFrame, seasonal_periods: int,
            alpha: float = 0.8, beta: float = 0.2, gamma: float = 0.2,
            date_col='date', value_col='demand', cutoff_col=None) -> 'HoltWintersPlotter':
        """
        Fit additive Holt-Winters to the data using linear regression for initial trend.

        Args:
            df (pd.DataFrame): DataFrame with historical data.
            seasonal_periods (int): Number of periods in a season.
            alpha (float): Level smoothing factor.
            beta (float): Trend smoothing factor.
            gamma (float): Seasonal smoothing factor.
            date_col (str): Column name for dates.
            value_col (str): Column name for observed values.
            cutoff_col (str, optional): Column name for cutoff dates to draw separators.
        """
        self._set_params(alpha, beta, gamma, seasonal_periods)
        df = df.copy().dropna(subset=[date_col, value_col])
        df[date_col] = pd.to_datetime(df[date_col])
        if cutoff_col:
            df[cutoff_col] = pd.to_datetime(df[cutoff_col])
        df = df.sort_values(date_col).reset_index(drop=True)

        cols = {date_col: 'date', value_col: 'demand'}
        if cutoff_col:
            cols[cutoff_col] = 'cutoff'
        self.history_ = df[list(cols.keys())].rename(columns=cols)

        n = len(df)
        m = seasonal_periods
        level = np.zeros(n)
        trend = np.zeros(n)
        seasonal = np.zeros(n)
        forecast = np.zeros(n)

        # --- Linear Regression Initialization for Trend ---
        y = df['demand'].iloc[:2 * m].values
        X = sm.add_constant(np.arange(len(y)))
        linreg = sm.OLS(y, X).fit()
        init_level = y[:m].mean()
        init_trend = linreg.params[1]

        level[0], trend[0] = init_level, init_trend
        for i in range(m):
            seasonal[i] = df['demand'].iloc[i] - init_level

        # Holt-Winters smoothing
        for t in range(1, n):
            seasonal_prev = seasonal[t - m] if t >= m else seasonal[t]
            forecast[t] = level[t - 1] + trend[t - 1] + seasonal_prev
            level[t] = alpha * (df['demand'].iloc[t] - seasonal_prev) + (1 - alpha) * (level[t - 1] + trend[t - 1])
            trend[t] = beta * (level[t] - level[t - 1]) + (1 - beta) * trend[t - 1]
            seasonal[t] = gamma * (df['demand'].iloc[t] - level[t - 1] - trend[t - 1]) + (1 - gamma) * seasonal_prev

        self.level_, self.trend_, self.seasonal_, self.forecast_ = level, trend, seasonal, forecast
        self.demand_ = df['demand'].values
        self.fitted = True

        self._calculate_forecast_error()
        return self

    def _calculate_forecast_error(self):
        if not self.fitted:
            raise RuntimeError("Model must be fitted before calculating forecast error.")
        mask = ~np.isnan(self.forecast_)
        self.mae_ = np.mean(np.abs(self.demand_[mask] - self.forecast_[mask]))
        self.mape_ = np.mean(np.abs((self.demand_[mask] - self.forecast_[mask]) / self.demand_[mask])) * 100

    def plot(self) -> alt.Chart:
        """
        Create an Altair chart showing:
        - Observed demand (points)
        - Smoothed level + seasonal (dashed green)
        - Trend (dashed orange)
        - Seasonal component (dashed purple)
        - In-sample forecast (solid blue)
        - Cutoff separators (if provided)
        - Legend for components
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before plotting.")

        df_plot = self.history_.copy()
        df_plot['Level'] = self.level_
        df_plot['Trend'] = self.trend_
        df_plot['Seasonal'] = self.seasonal_
        df_plot['Forecast'] = self.forecast_

        df_long = df_plot.melt(
            id_vars=['date', 'demand'],
            value_vars=['Level', 'Trend', 'Seasonal', 'Forecast'],
            var_name='Component',
            value_name='Value'
        )

        base = alt.Chart(df_plot).encode(x=alt.X('date:T', title='Date'))

        demand = base.mark_point(color='gray', opacity=0.5).encode(
            y=alt.Y('demand:Q', title='Demand / Component'),
            tooltip=['date:T', 'demand:Q']
        )

        line_chart = alt.Chart(df_long).mark_line(strokeWidth=3).encode(
            x='date:T',
            y='Value:Q',
            color=alt.Color('Component:N',
                            scale=alt.Scale(
                                domain=['Level', 'Trend', 'Seasonal', 'Forecast'],
                                range=['#2ca02c', '#ff7f0e', '#9467bd', '#1f77b4']
                            ),
                            legend=alt.Legend(title="Component")
            ),
            strokeDash=alt.StrokeDash('Component:N',
                                      scale=alt.Scale(
                                          domain=['Level', 'Trend', 'Seasonal', 'Forecast'],
                                          range=[[5,5], [5,5], [5,5], []]
                                      ),
                                      legend=None
            ),
            tooltip=['date:T', 'Component:N', 'Value:Q']
        )

        # Add cutoff separators if present
        layers = [demand, line_chart]
        if 'cutoff' in df_plot.columns:
            cutoffs = df_plot['cutoff'].unique()
            vlines = alt.Chart(pd.DataFrame({'cutoff': cutoffs})).mark_rule(
                strokeDash=[5, 5], opacity=0.4, strokeWidth=1.5, color='black'
            ).encode(x='cutoff:T')
            layers.append(vlines)

        mae = int(round(self.mae_, 0))
        mape = round(self.mape_, 1)

        chart = alt.layer(*layers).properties(
            width=800, height=400,
            title=f"Holt-Winters Additive (α: {self.alpha}, β: {self.beta}, γ: {self.gamma}), MAE: {mae}, MAPE: {mape}%"
        ).configure_title(fontSize=16, anchor='start', fontWeight='bold')

        return chart



class TimeSeriesDecompositionPlotter:
    """
    A class for plotting simple time series decomposition of historic demand.
    Decomposes the data into trend (linear regression) and seasonal (average by calendar week).
    
    Attributes:
        history_ (pd.DataFrame): Original historical data with 'date' and 'demand'.
        trend_ (np.ndarray): Linear trend component.
        seasonal_ (np.ndarray): Seasonal component based on calendar week averages.
        residual_ (np.ndarray): Residual component (observed - trend - seasonal).
        fitted (bool): Whether the model has been fitted.
    """
    
    def __init__(self):
        self.history_ = None
        self.trend_ = None
        self.seasonal_ = None
        self.residual_ = None
        self.fitted = False

    def fit(self, df: pd.DataFrame, date_col='date', value_col='demand'):
        """
        Fit the decomposition model to the data.
        
        Args:
            df (pd.DataFrame): DataFrame with historical data.
            date_col (str): Column name for dates.
            value_col (str): Column name for observed values.
        """
        df = df.copy().dropna(subset=[date_col, value_col])
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)
        
        # Store history
        self.history_ = df[[date_col, value_col]].rename(columns={date_col: 'date', value_col: 'demand'})
        
        n = len(df)
        y = df[value_col].values
        
        # Calculate linear trend using OLS
        X = sm.add_constant(np.arange(n))
        trend_model = sm.OLS(y, X).fit()
        self.trend_ = trend_model.predict(X)
        
        # Calculate seasonal component based on calendar week
        df['week'] = df[date_col].dt.isocalendar().week
        weekly_means = df.groupby('week')[value_col].mean()
        
        # Map weekly means to each observation
        self.seasonal_ = df['week'].map(weekly_means).values
        
        # Remove the overall mean from seasonal to center it around 0
        self.seasonal_ = self.seasonal_ - np.mean(self.seasonal_)
        
        # Calculate residual
        self.residual_ = y - self.trend_ - self.seasonal_
        
        self.fitted = True
        return self
        
    def plot(self) -> alt.Chart:
        """
        Create an Altair chart showing the decomposition:
        - Original demand (gray points)
        - Trend component (solid red line)
        - Seasonal component (dashed green line)
        - Residual component (dashed blue line)
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before plotting.")
            
        df_plot = self.history_.copy()
        df_plot['Trend'] = self.trend_
        df_plot['Seasonal'] = self.seasonal_
        df_plot['Residual'] = self.residual_
        
        # Create long format for components
        df_long = df_plot.melt(
            id_vars=['date', 'demand'],
            value_vars=['Trend', 'Seasonal', 'Residual'],
            var_name='Component',
            value_name='Value'
        )
        
        # Base chart
        base = alt.Chart(df_plot).encode(x=alt.X('date:T', title='Date'))
        
        # Original demand points
        demand = base.mark_point(color='gray', opacity=0.6, size=40).encode(
            y=alt.Y('demand:Q', title='Demand / Component'),
            tooltip=['date:T', 'demand:Q']
        )
        
        # Component lines
        line_chart = alt.Chart(df_long).mark_line(strokeWidth=2).encode(
            x='date:T',
            y='Value:Q',
            color=alt.Color('Component:N',
                            scale=alt.Scale(
                                domain=['Trend', 'Seasonal', 'Residual'],
                                range=['#d62728', '#2ca02c', '#1f77b4']
                            ),
                            legend=alt.Legend(title="Component")
            ),
            strokeDash=alt.StrokeDash('Component:N',
                                        scale=alt.Scale(
                                            domain=['Trend', 'Seasonal', 'Residual'],
                                            range=[[], [5,5], [3,3]]
                                        ),
                                        legend=None
            ),
            tooltip=['date:T', 'Component:N', 'Value:Q']
        )
        
        # Combine layers
        chart = alt.layer(demand, line_chart).properties(
            width=800, 
            height=400,
            title="Time Series Decomposition: Trend + Seasonal + Residual"
        ).configure_title(
            fontSize=16, 
            anchor='start', 
            fontWeight='bold'
        ).configure_axis(
            labelFontSize=12, 
            titleFontSize=14
        ).configure_legend(
            titleFontSize=13, 
            labelFontSize=12
        )
        
        return chart