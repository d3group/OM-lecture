import pandas as pd
from typing import Dict, Any, Optional
from typing import List, Union, Dict, Any
from typing import Union, Dict, List, Any
from typing import Optional, Union
from statsforecast import StatsForecast
from statsforecast.models import (
    Naive,
    WindowAverage,
    SimpleExponentialSmoothing,
    SimpleExponentialSmoothingOptimized,
    Holt,
    AutoETS
)

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