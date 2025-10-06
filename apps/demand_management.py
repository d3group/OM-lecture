import marimo

__generated_with = "0.15.5"
app = marimo.App(
    width="medium",
    app_title="Demand Management",
    css_file="d3.css",
)



@app.cell(hide_code=True)
def _():
    GH_USER = "moobeck"
    GH_REPO = "OM-lecture"
    BRANCH = "main"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    class DataURLs:
        BASE = raw_url("apps", "public", "data")
        DEMAND = f"{BASE}/daily_demand_data_fuerth.csv"
        FORECAST = f"{BASE}/forecast_fuerth.csv"
        HISTORIC_FORECAST = f"{BASE}/historic_forecast_fuerth.csv"

    class ImageURLs:
        BASE = raw_url("apps", "public", "images")
        DISTRIBUTION_CENTER = f"{BASE}/distribution_center_fuerth.png"

    class UtilsURLs:
        BASE = raw_url("apps", "utils")
        FILES = {
            "data.py": f"{BASE}/data.py",
            "forecast.py": f"{BASE}/forecast.py",
            "slides.py": f"{BASE}/slides.py",
            "inventory.py": f"{BASE}/inventory.py",
        }
        PACKAGES = [
            "pandas",
            "altair",
            "scikit-learn",
            "numpy",
            "statsmodels",
            "scipy",
            "typing_extensions",
            "utilsforecast"
        ]

    return (DataURLs, ImageURLs, UtilsURLs)



@app.cell(hide_code=True)
async def _(UtilsURLs):
    import micropip
    import urllib.request
    import os

    class UtilsManager:
        def __init__(self, dest_folder="utils", files_map=None, packages=None):
            self.dest_folder = dest_folder
            self.files_map = files_map or {}
            self.files = list(self.files_map.keys())
            self.packages = packages or []
            self.packages_installed = False
            self.files_downloaded = False

        async def install_packages(self):
            for pkg in self.packages:
                print(f"Installing {pkg}...")
                await micropip.install(pkg)
            print("✅ All packages installed.")
            self.packages_installed = True

        def download_files(self):
            os.makedirs(self.dest_folder, exist_ok=True)
            init_file = os.path.join(self.dest_folder, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    f.write("# Init for utils package\n")

            for fname, url in self.files_map.items():
                dest_path = os.path.join(self.dest_folder, fname)
                urllib.request.urlretrieve(url, dest_path)
                print(f"📥 Downloaded {fname} to {dest_path}")

            self.files_downloaded = True

    utils_manager = UtilsManager(
        files_map=UtilsURLs.FILES,
        packages=UtilsURLs.PACKAGES,
    )

    await utils_manager.install_packages()
    utils_manager.download_files()

    return (utils_manager,)

@app.cell(hide_code=True)
def _():
    import warnings
    warnings.filterwarnings("ignore")
    return


@app.cell(hide_code=True)
def _(utils_manager):
    print("Packages installed:", utils_manager.packages_installed)
    print("Files downloaded:", utils_manager.files_downloaded)
    import marimo as mo
    import numpy as np
    import pandas as pd
    from sklearn.utils import Bunch
    from utils.data import DataLoader, DataSplitter
    from utils.forecast import (ForecastLoader, Evaluator, ForecastPlotter,
                               HoltDoubleExpPlotter, HoltWintersPlotter,
                               TimeSeriesDecompositionPlotter)
    from utils.slides import SlideCreator


    return (SlideCreator, DataLoader, DataSplitter, ForecastLoader, Evaluator, ForecastPlotter, HoltDoubleExpPlotter, HoltWintersPlotter, TimeSeriesDecompositionPlotter, np, pd, Bunch, mo)



@app.cell(hide_code=True)
def _(mo):
    public_dir = (
        str(mo.notebook_location) + "/public"
        if str(mo.notebook_location).startswith("https://")
        else "public"
    )
    return (public_dir,)


@app.cell
def _():

    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Operations Management"
    presenter = "Richard Pibernik, Moritz Beck"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return (sc,)


@app.cell
def _(sc):
    titleSlide = sc.create_slide(
        "Demand Planning Basics",
        layout_type="title-slide",
        newSection="Demand Planning Basics",
    )
    return (titleSlide,)


@app.cell(hide_code=True)
def _(titleSlide):
    titleSlide.render_slide()
    return


@app.cell
def _(mo, sc, ImageURLs):  # <-- accept ImageURLs and use it
    introduction = sc.create_slide(
        "Let’s start with a very basic Forecasting task...", layout_type="2-row"
    )
    introduction.content1 = mo.image(
        ImageURLs.DISTRIBUTION_CENTER,
        width=1000,
        style={"margin-right": "auto", "margin-left": "auto"},
    )
    introduction.content2 = mo.md(
    """One of the many Demand Planning Tasks of Phoenix is to predict the demand of Amoxicillin of a  
    specific manufacturer and a specific dosage form for a single distribution center (here: Fürth) for the  
    4 weeks. This forecast will be used to determine the target inventory quantities  
    and order quantities from a central warehouse. """
    )
    return (introduction,)


@app.cell(hide_code=True)
def _(introduction):
    introduction.render_slide()
    return


@app.cell(hide_code=True)
def _(DataLoader, DataURLs):
    loader = DataLoader()
    data_daily = loader.load(file_path=DataURLs.DEMAND)
    return (data_daily,)


@app.cell
def _(data_daily, mo, sc):
    history_slide = sc.create_slide("Historical Data for Amoxicillin", layout_type="3-row")
    history_slide.content1 = mo.md(
        """
        Assume that we have 5 years of historical demand for Amoxicillin  
        at the Phoenix distribution center in Fürth.  
        Let's read the data into python with the pandas library and have a look at it.  
        The data contains the date and the demand for each day."""
    )
    history_slide.content2 = mo.md(
        """
    ```python
    import pandas as pd
    history_daily = pd.read_csv(path_to_history_csv)
    ```
    """
    )

    history_slide.content3 = mo.ui.table(data_daily)
    return (history_slide,)


@app.cell(hide_code=True)
def _(history_slide):
    history_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(data_daily):
    data = (
        data_daily
        .set_index('date')  # Set 'ds' as index
        .groupby('unique_id')  # Group by time series
        .resample('W-MON')  # Resample now that 'ds' is the index
        .agg({'demand': 'sum'})  # Aggregation method
        .reset_index()  # Return to flat format
    )
    return (data,)


@app.cell
def _(data, mo, sc):
    history_slide2 = sc.create_slide("Historical Data for Amoxicillin", layout_type="3-row")
    history_slide2.content1 = mo.md(
        """As we are interested in a weekly demand forecast,  
        we aggregate the daily data to weekly data."""
    )
    history_slide2.content2 = mo.md(
        """
    ```python
        history_weekly = (
            history_daily
            .set_index('date')  # Set 'ds' as index
            .groupby('unique_id')  # Group by time series
            .resample('W-MON')  # Resample now that 'ds' is the index
            .agg({'demand': 'sum'})  # Aggregation method
            .reset_index()  # Return to flat format
    ```
    """
    )


    history_slide2.content3 = mo.ui.table(data)
    return (history_slide2,)


@app.cell(hide_code=True)
def _(history_slide2):
    history_slide2.render_slide()
    return


@app.cell(hide_code=True)
def _(DataSplitter, data):
    splitter = DataSplitter(cutoff_date="2024-08-01")
    history, actuals = splitter.split(data)
    return actuals, history


@app.cell(hide_code=True)
def _(ForecastPlotter, actuals, history):
    fc_plotter = ForecastPlotter(history=history, actuals=actuals)
    return (fc_plotter,)


@app.cell
def _(fc_plotter, mo, sc):

    basic_forecasting1 = sc.create_slide("Historical Data", layout_type="2-row")
    plot = fc_plotter.plot(
        title="Weekly Demand of Amoxicilin (Fürth Region)",
        vertical_line=False,
        shade=False,
    )

    basic_forecasting1.content1 =  mo.md("""

    Let's start with a simple plot of the historical data. 
    We can see that the demand is not constant, but has a clear trend and seasonality.

    """)

    basic_forecasting1.content2 = mo.ui.altair_chart(plot)
    return (basic_forecasting1,)


@app.cell(hide_code=True)
def _(basic_forecasting1):
    basic_forecasting1.render_slide()
    return


@app.cell
def _(mo, sc):
    basic_forecasting2 = sc.create_slide(
        "Basic Forecasting", layout_type="1-column"
    )
    basic_forecasting2.content1 = mo.md(
        """

        Now we want to decide how to forecast the demand for the next 4 weeks. 
        The easiest way is to use the last week of data as a forecast.  
        But is this a good idea?  
        To answer this question, we need to find a way to evaluate different forecasting methods.
        """
    )
    return (basic_forecasting2,)


@app.cell(hide_code=True)
def _(basic_forecasting2):
    basic_forecasting2.render_slide()
    return


@app.cell(hide_code=True)
def _(Bunch):

    MA_Q_MIN = 1
    MA_Q_MAX = 16
    MA_Q_STEP = 1

    MA_CONFIG = Bunch(
        q_min=MA_Q_MIN,
        q_max=MA_Q_MAX,
        q_step=MA_Q_STEP,
        q_default=MA_Q_MIN,
    )

    SES_CONFIG = Bunch(
        alpha_min=0.1,
        alpha_max=1,
        alpha_step=0.1,
        alpha_default=0.1,
    )
    return MA_CONFIG, SES_CONFIG


@app.cell(hide_code=True)
def _(
    ForecastLoader,
    MA_CONFIG,
    SES_CONFIG,
    data,
    fc_plotter,
    history,
    mo,
    np,
    public_dir,
    DataURLs,
):

    ma_qs = [q for q in range(MA_CONFIG.q_min, MA_CONFIG.q_max + 1, MA_CONFIG.q_step)]
    ma_names = [f"MA_{q}" for q in ma_qs]

    ses_alphas = np.arange(
        SES_CONFIG.alpha_min,
        SES_CONFIG.alpha_max + 0.1,
        SES_CONFIG.alpha_step,
    )
    ses_names = [f"SES_{int(10*(alpha))}" for alpha in ses_alphas]


    params = {
        "naive": [{"alias": "Naive"}],
        "ma": [{"q": q, "alias": ma_alias} for q, ma_alias in zip(ma_qs, ma_names)],
        "ses": [
            {"alpha": alpha, "alias": ses_alias}
            for ses_alias, alpha in zip(ses_names, ses_alphas)
        ]
        + [{"alias": "SES"}],
        "holt": [{"alias": "Holt"}],
        "holt_winters": [{"alias": "Holt‑Winters"}],
    }

    fc_loader = ForecastLoader()
    forecast, historic_forecast = fc_loader.load_data(DataURLs.FORECAST, DataURLs.HISTORIC_FORECAST)

    mo.ui.dataframe(
        forecast,
    )
    mo.ui.dataframe(
        historic_forecast,
    )

    fc_plotter.add_forecast(forecast)
    fc_plotter.add_historic_forecast(historic_forecast)
    return forecast, historic_forecast


@app.cell
def _(fc_plotter, mo, sc):
    basic_forecasting3 = sc.create_slide("Forecasting Evaluation", layout_type="2-row")
    plot_shaded = fc_plotter.plot(
        title="Weekly Demand of Amoxicilin (Fürth Region)",
        vertical_line=True,
        shade=True,
    )
    basic_forecasting3.content1 = mo.md(
    """
    For evaluating our model, we take the last year consisting of 13 windows of 4 weeks.  
    That means at the beginning of each window, we have to forecast the next 4 weeks."""
    )
    basic_forecasting3.content2 = mo.ui.altair_chart(plot_shaded)
    return (basic_forecasting3,)


@app.cell(hide_code=True)
def _(basic_forecasting3):
    basic_forecasting3.render_slide()
    return


@app.cell
def _(mo, sc):
    # Create a slide that intuitively formalizes the forecasting evaluation process
    basic_forecasting4 = sc.create_slide(
        "Formal Introduction to Forecasting", layout_type="2-row"
    )

    basic_forecasting4.content1 = mo.md(
        r"""
        In order to evaluate our forecasting method, we need to define the forecasting problem more formally.
    """
    )
    basic_forecasting4.content2 = mo.md(
        r"""
        - **Forecasting Problem:**  
        Given past demands \(d_{1}, d_{2}, \dots,  d_{t-1}, d_t\),  
        produce forecasts for the next 4 weeks: \(f_{t+1}, f_{t+2}, f_{t+3}, f_{t+4}\).
        - **Naive Forecasting Method:**  
        The simple naive forecasting method uses the last observed demand as the forecast  
        for the next periods: \(f_{t+1} = d_t\, f_{t+2} = d_t, \dots, f_{t+4} = d_t\).
    """
    )


    return (basic_forecasting4,)


@app.cell(hide_code=True)
def _(basic_forecasting4):
    basic_forecasting4.render_slide()
    return


@app.cell
def _(mo, sc):
    # Create a slide that intuitively formalizes the forecasting evaluation process
    basic_forecasting_code = sc.create_slide(
        "Implementation of Naive Forecasting", layout_type="2-row"
    )

    # Use clear bullet points and mathematical notation for readability
    basic_forecasting_code.content1 = mo.md(
        """
        Lets implement the naive forecasting method in Python using the NumPy library.  
        The naive forecast method takes a NumPy array (a list of numbers)  
        of past observations and a horizon  
        (number of future steps to forecast) as input, and returns a NumPy array  
        of the same length as the horizon with the last observed value repeated.
        """
    )

    basic_forecasting_code.content2 = mo.md(
        """
        ```python
        import numpy as np

        def naive_forecast(history: np.ndarray, horizon: int = 4) -> np.ndarray:
            \"\"\"
            Generate a naive forecast by repeating the last observed value.

            :param history: 1D NumPy array of past observations.
            :param horizon: Number of future steps to forecast.
            :return: 1D NumPy array of length `horizon` with repeated last value.
            \"\"\"
            last_value = history[-1]
            return np.full(shape=horizon, fill_value=last_value)
        ``` 
        """
    )
    return (basic_forecasting_code,)


@app.cell(hide_code=True)
def _(basic_forecasting_code):
    basic_forecasting_code.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    basic_forecasting_plot = sc.create_slide("Naive Forecasting", layout_type="2-row")
    plot_naive = fc_plotter.plot(
        model_col="Naive",
        title="Forecast of the Weekly Demand using the Naive Method",
        vertical_line=True,
        shade=True,
    )
    basic_forecasting_plot.content1 = mo.md(
        """As we can see, the naive forecasting method results in 13 constant forecasts of the last observed demand.  
        To evaluate the forecasting method, we need to compare the forecast (orange) with the actual demand (blue)."""
    )
    basic_forecasting_plot.content2 = mo.ui.altair_chart(plot_naive)
    return (basic_forecasting_plot,)


@app.cell(hide_code=True)
def _(basic_forecasting_plot):
    basic_forecasting_plot.render_slide()
    return


@app.cell
def _(mo, sc):
    # Create a slide that intuitively formalizes the forecasting evaluation process
    evaluation_metrics = sc.create_slide(
        "Formal Introduction to Evaluation", layout_type="2-row"
    )

    evaluation_metrics.content1 = mo.md(
        """To assess the quality of predictions from the naive forecasting method, we compare them to actual demand. Forecast errors are the differences between each predicted value and the observed demand. To summarize these errors into one measure of overall accuracy, we use error measures. Two popular ones are:""")

    evaluation_metrics.content2 = mo.md(
        r"""
        - **Mean Absolute Error (MAE):**  
        The MAE is the average of the absolute errors over all individual periods in our evaluation period (in our case, \(n=52\) weeks): 

        \[
            \mathrm{MAE}
            = \frac{1}{n} \sum_{i=1}^{n} \bigl|d_{t+i} - f_{t+i}\bigr|
        \]

        - **Mean Absolute Percentage Error (MAPE):**  
        The MAPE is the average of the absolute percentage errors over all individual periods in our evaluation period (in our case, \(n=52\) weeks):

        \[
            \mathrm{MAPE}
            = \frac{1}{n} \sum_{i=1}^{n}
            \frac{\bigl|d_{t+i} - f_{t+i}\bigr|}{d_{t+i}}
            \times 100\%
        \]

        """
    )
    return (evaluation_metrics,)


@app.cell(hide_code=True)
def _(evaluation_metrics):
    evaluation_metrics.render_slide()
    return


@app.cell
def _(mo, sc):
    # Create a slide with Python-based implementations of MAE and MAPE
    eval_metrics_code = sc.create_slide(
        "Implementation of Evaluation Metrics", layout_type="2-row"
    )
    eval_metrics_code.content1 = mo.md(
        """
        Here we implement MAE and MAPE using the NumPy library. These functions take two NumPy arrays as input:  
        The actual demand and the forecasted values, and return the MAE and MAPE as floats (decimal numbers).  
        The MAPE is only calculated for non-zero actual values to avoid division by zero errors.
        """
    )

    eval_metrics_code.content2 = mo.md(
        """
        ```python
        import numpy as np

        def mae(actuals: np.ndarray, forecasts: np.ndarray) -> float:
            \"\"\"
            Compute MAE between actuals and forecasts using NumPy.

            :param actuals: array of true values
            :param forecasts: array of forecasted values
            :return: MAE as a float
            \"\"\"
            errors = np.abs(actuals - forecasts)
            return errors.mean()

        def mape(actuals: np.ndarray, forecasts: np.ndarray) -> float:
            \"\"\"
            Compute MAPE between actuals and forecasts using NumPy.

            :param actuals: array of true values
            :param forecasts: array of forecasted values
            :return: MAPE as a percentage float
            \"\"\"
            # Avoid division by zero by masking zero actuals
            nonzero = actuals != 0
            errors = actuals[nonzero] - forecasts[nonzero]
            pct_errors = np.abs(errors / actuals[nonzero])
            return pct_errors.mean() * 100
        ```
        """
    )
    return (eval_metrics_code,)


@app.cell(hide_code=True)
def _(eval_metrics_code):
    eval_metrics_code.render_slide()
    return


@app.cell(hide_code=True)
def _(Evaluator, fc_plotter, forecast, historic_forecast):
    evaluator = Evaluator(forecast=forecast, historic_forecast=historic_forecast)
    evaluations = evaluator.evaluate()
    fc_plotter.add_metrics(evaluations)
    return (evaluations,)


@app.cell
def _(fc_plotter, mo, sc):
    evaluation_naive = sc.create_slide(
        "Forecasting with the Naive Method", layout_type="2-row"
    )
    plot_naive_with_metric = fc_plotter.plot(
        model_col="Naive",
        title="Forecast of the Weekly Demand using the Naive Method",
        vertical_line=True,
        shade=True,
    )
    evaluation_naive.content2 = mo.ui.altair_chart(plot_naive_with_metric)
    return (evaluation_naive,)


@app.cell(hide_code=True)
def _(evaluation_naive):
    evaluation_naive.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide 1: Introduction to Moving Average Forecasting
    ma_intro = sc.create_slide("Moving Average", layout_type="2-row")
    ma_intro.content1 = mo.md(
    """
    Limitations of Naive Forecasting and Introduction to Moving Average

    - **Drawback of Naive Method:**  
    Using only the last observed demand \(d_{t}\) ignores trends and seasonality,  
    and can be overly sensitive to random fluctuations in weekly demand.
    - **Moving Average Idea:**  
    Instead of relying on a single most recent observation,  
    we average the last \(q\) observations to smooth out noise:""")


    ma_intro.content2 = mo.md(r"""
    \[
    f_{t+4} = f_{t+3} = f_{t+2} = f_{t+1} = \frac{1}{q} \bigl(d_{t-q+1} + \dots + d_{t} \bigr)
    \]

    """)

    ma_intro.content3 = mo.md(                         
    """
    - **Where:**  
    - \(q\) is the window size (number of past periods to average).
    - ) are historical demands.  
    This method reduces the impact of random spikes or dips by incorporating multiple past points into each forecast.
    """
    )
    return (ma_intro,)


@app.cell(hide_code=True)
def _(ma_intro):
    ma_intro.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide 2: Python Implementation of Moving Average Forecasting
    ma_code_slide = sc.create_slide(
        "Implementation of Moving Average", layout_type="2-row"
    )

    ma_code_slide.content1 = mo.md(
        """
    Below we implement a simple moving average forecaster in Python using NumPy.  
    The function takes three parameters: the historical demand,   
    the window size \(q\) (number of past periods to average),  
    and the forecast horizon. 
    """
    )

    ma_code_slide.content2 = mo.md(
        """
        ```python
        import numpy as np


        def moving_average_forecast(
            actuals: np.ndarray,
            q: int,
            horizon: int = 4
        ) -> np.ndarray:
             \"\"\"
            Compute an h-step–ahead moving average forecast.

            :param actuals: array of historical values
            :param q: number of past periods to average
            :param horizon: number of future points to forecast 
            :return: array of forecasts
             \"\"\"
            avg = np.mean(actuals[-q:])
            return np.full(horizon, avg, dtype=float)

        ```
        """
    )
    return (ma_code_slide,)


@app.cell(hide_code=True)
def _(ma_code_slide):
    ma_code_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    evaluation_ma4 = sc.create_slide(
        "Forecasting with Moving Average", layout_type="2-row"
    )
    evaluation_ma4.content1 = mo.md("""
        The moving average method with uses the last 6 weeks of data (q=6) to forecast the next 4 weeks (h=4).  
        But what is the best value of q?
    """)
    plot_ma4 = fc_plotter.plot(
        model_col="MA_6",
        title="Forecast of the Weekly Demand using the Moving Average Method [MA(6)]",
        vertical_line=True,
        shade=True,
    )
    evaluation_ma4.content2 = mo.ui.altair_chart(plot_ma4)
    return (evaluation_ma4,)


@app.cell(hide_code=True)
def _(evaluation_ma4):
    evaluation_ma4.render_slide()
    return


@app.cell(hide_code=True)
def _(MA_CONFIG, mo):
    q_slider = mo.ui.slider(
        MA_CONFIG.q_min,
        MA_CONFIG.q_max,
        value=MA_CONFIG.q_default,
        label="###Window Size (q)",
        step=MA_CONFIG.q_step,
    )
    return (q_slider,)


@app.cell
def _(fc_plotter, mo, q_slider, sc):
    evaluation_ma_q = sc.create_slide("Moving Average Forecasting", layout_type="3-row")
    evaluation_ma_q.content1 = mo.md(""" 
    The parameter $q$ sets how many past data points to average.  
    A larger $q$ makes forecast smoother but slower to react;  
    a smaller $q$ more responsive but noisier.
    For $q=1$ the Moving Average is the same as the Naive forecast.
    To pick the best $q$, compare the forecast errors (MAE or MAPE)  
    for different $q$ values on the historical data and choose the one with the lowest error.
    """)

    evaluation_ma_q.content2 = q_slider
    q = q_slider.value
    plot_ma_q = fc_plotter.plot(
        model_col=f"MA_{q}",
        title=f"Forecast of the Weekly Demand using the Moving Average Method [MA({q})]",
        vertical_line=True,
        shade=True,
        plot_mode="history",
    )
    evaluation_ma_q.content3 = mo.ui.altair_chart(plot_ma_q)
    return (evaluation_ma_q,)


@app.cell(hide_code=True)
def _(evaluation_ma_q):
    evaluation_ma_q.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    evaluation_ma1 = sc.create_slide(
        "Forecasting with Moving Average", layout_type="2-row"
    )
    evaluation_ma1.content1 = mo.md(
        """
        The best value of q for the historical data turned out to be 3. Our hope is that this will also be the best value for the future.  
        """
    )
    plot_ma16 = fc_plotter.plot(
        model_col="MA_3",
        title="Forecast of the Weekly Demand using the Moving Average Method [MA(3)]",
        vertical_line=True,
        shade=True,
    )
    evaluation_ma1.content2 = mo.ui.altair_chart(plot_ma16)
    return (evaluation_ma1,)


@app.cell(hide_code=True)
def _(evaluation_ma1):
    evaluation_ma1.render_slide()
    return


@app.cell
def _(mo, sc):
    ma_drawbacks = sc.create_slide("Moving Average Forecasting", layout_type="1-row")
    ma_drawbacks.content1 = mo.md(
    """
     **Limitations of Moving Average Forecasting**

    Increasing the window size \(q\) does make the forecast smoother and lowers the MAE,   
    but it also means the forecast reacts more slowly to actual changes.

    Therefore, we need a method that smooths the data like a moving average   
    but can also respond more quickly to changes.  
    This is where Single Exponential Smoothing (SES) comes in.

    """
    )
    return (ma_drawbacks,)


@app.cell(hide_code=True)
def _(ma_drawbacks):
    ma_drawbacks.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Introduction to Exponential Smoothing
    exp_intro = sc.create_slide(
        "Introduction to Exponential Smoothing", layout_type="1-column"
    )
    exp_intro.content1 = mo.md(
        r"""
    **Why Exponential Smoothing?**

    - **Moving average:**  
    smoothes noise but lags behind trends and can’t adapt to changing levels or seasonality.
    - **Exponential smoothing:**  
    assigns exponentially decreasing weights to older observations, allowing the forecast to adapt more quickly.  
    - Different extensions of the basic idea handle **level**, **trend**, and **seasonality** in increasing sophistication.
    """
    )
    return (exp_intro,)


@app.cell(hide_code=True)
def _(exp_intro):
    exp_intro.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Single Exponential Smoothing (SES)
    ses_slide = sc.create_slide("Single Exponential Smoothing", layout_type="1-column")
    ses_slide.content1 = mo.md(
        r"""
    **Model:**  

    \[
       f_{t+1}
      = \alpha\,d_t + (1-\alpha)\, f_t 
      \\
      = \alpha\,d_t + f_t - \alpha\,f_t
      \\
      =  \underbrace{f_t}_{\text{Old forecast}}+ \alpha \,\underbrace{(d_t - f_t)}_{\text{Error term}}
    \]


    - where  
    - \(\alpha\in(0,1)\) is the smoothing parameter.  
    - Smaller \(\alpha\) → smoother, slower updates.
    - Larger \(\alpha\) → more reactive to recent changes; 
    - If \(\alpha = 1\), then \(f_{t+1} = d_t\), which is the naive forecast (just using the most recent observation).
    - \( f_t\) is the forecast for period \(t\).
    - \(d_t\) is the actual demand for period \(t\)."""
    )
    return (ses_slide,)


@app.cell(hide_code=True)
def _(ses_slide):
    ses_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Python Implementation of Single Exponential Smoothing (SES)
    ses_code_slide = sc.create_slide(
        "Implementation of Single Exponential Smoothing", layout_type="2-row"
    )

    ses_code_slide.content1 = mo.md(
        """
        - The following function implements Single Exponential Smoothing (SES):
        - The function takes three parameters: 
        The historical demand, the smoothing parameter α (between 0 and 1),  
        and an optional initial forecast value.
        - The function returns a NumPy array of SES forecasts,  
        where each forecast is computed based on the previous actual value and the previous forecast.
        """
    )

    ses_code_slide.content2 = mo.md(
        """
        ```python
        import numpy as np

        def simple_exponential_smoothing(
            actuals: np.ndarray,
            alpha: float,
            initial_forecast: float = None
        ) -> np.ndarray:
            \"\"\"
            Compute SES forecasts for a sequence of observations.

            :param actuals: array of observed values, shape
            :param alpha: smoothing coefficient between 0 and 1
            :param initial_forecast: optional initial forecast value
            :return: array of SES forecasts, shape 
            \"\"\"
            n = len(actuals)
            forecasts = np.zeros(n)

            # Set initial forecast
            forecasts[0] = actuals[0] if initial_forecast is None else initial_forecast

            for t in range(1, n):
                forecasts[t] = alpha * actuals[t - 1] + (1 - alpha) * forecasts[t - 1]

            return forecasts
        ```
        """
    )
    return (ses_code_slide,)


@app.cell(hide_code=True)
def _(ses_code_slide):
    ses_code_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(SES_CONFIG, mo):
    # Slider to explore α
    alpha_slider_ses = mo.ui.slider(
        SES_CONFIG.alpha_min,
        SES_CONFIG.alpha_max,
        value=SES_CONFIG.alpha_default,
        step=SES_CONFIG.alpha_step,
        label="Smoothing Parameter α"
    )
    return (alpha_slider_ses,)


@app.cell
def _(alpha_slider_ses, fc_plotter, mo, sc):
    # Slide: Single Exponential Smoothing (SES)
    ses_slide_plot = sc.create_slide(
        "Forecasting with Single Exponential Smoothing", layout_type="3-row"
    )
    ses_slide_plot.content1 = mo.md(""""
        Let's see how the SES method works with different values of α.  
        The best value of α is the one that minimizes the MAE on the historical data. (like q for MA)"""
    )
    ses_slide_plot.content2 = alpha_slider_ses
    # plot all windows for SES
    alpha = alpha_slider_ses.value

    ses_name = f"SES_{int(10*(alpha))}"

    plot_ses = fc_plotter.plot(
        model_col=ses_name,
        title=f"SES Forecast (α={alpha})",
        vertical_line=True,
        shade=True,
        plot_mode="history",
    )
    ses_slide_plot.content3 = mo.ui.altair_chart(plot_ses)
    return (ses_slide_plot,)


@app.cell(hide_code=True)
def _(ses_slide_plot):
    ses_slide_plot.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: SES Using StatsForecast Library
    ses_statsforecast_slide = sc.create_slide(
        "Single Exponential Smoothing with StatsForecast", layout_type="2-row"
    )

    ses_statsforecast_slide.content1 = mo.md(
        """
        Instead of implementing SES and tuning α manually, we can use the `StatsForecast` package.  
        This packages provides a simple interface for time series forecasting with:

        - Automatic parameter tuning
        - Scales to large datasets
        - Compatible with Pandas DataFrames
        """
    )

    ses_statsforecast_slide.content2 = mo.md(
        """
        ```python
        from statsforecast import StatsForecast
        from statsforecast.models import SimpleExpSmoothing

        # Assume `historic` is a DataFrame with columns: unique_id, date, demand

        sf = StatsForecast(models=[SimpleExponentialSmoothingOptimized()], freq='W')
        forecasts_df = sf.forecast(
            df=historic,
            h=4,
            id_col="unique_id",
            time_col="date",
            target_col="demand"
        )
        ```
        """
    )
    return (ses_statsforecast_slide,)


@app.cell(hide_code=True)
def _(ses_statsforecast_slide):
    ses_statsforecast_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Single Exponential Smoothing (SES)
    ses_optimized_slide_plot = sc.create_slide(
        "Forecasting with Single Exponential Smoothing", layout_type="2-row"
    )
    ses_optimized_slide_plot.content1 = mo.md("""
        The SES method with the best α performed similarly to the MA method.
        However, it gives a constant forecast within each 4-week window — that’s a point we can improve."""
    )
    plot_ses_opt = fc_plotter.plot(
        model_col="SES",
        title=f"SES Forecast",
        vertical_line=True,
        shade=True,
        plot_mode="forecast",
    )
    ses_optimized_slide_plot.content2 = mo.ui.altair_chart(plot_ses_opt)
    return (ses_optimized_slide_plot,)


@app.cell(hide_code=True)
def _(ses_optimized_slide_plot):
    ses_optimized_slide_plot.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown quiz
    user_answer_mape_mae = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (user_answer_mape_mae,)


@app.cell
def _(mo, sc, user_answer_mape_mae):
    # Question 2: MAPE vs MAE
    slide_mape_mae = sc.create_slide(
        "Quiz: Forecasting Error Metrics",
        layout_type="3-row"
    )

    slide_mape_mae.content1 = mo.md(
        '''
    **Which of the following statements correctly describes the advantage of Mean Absolute Error (MAE) over Mean Absolute Percentage Error (MAPE)?**

    <ol type="a">
      <li>MAPE is easier to interpret because it’s scale-dependent, whereas MAE can be infinite if actuals are zero.</li>
      <li>MAE expresses error as a percentage, making it unitless and comparable across series, while MAPE stays in original units.</li>
      <li>MAE is in the same units as the data and remains defined when actual values are zero, whereas MAPE can be undefined or extreme.</li>
      <li>MAPE assigns exponentially decreasing weights to larger errors, while MAE treats all errors equally.</li>
    </ol>
        '''
    )

    slide_mape_mae.content2 = user_answer_mape_mae

    # Conditional feedback for Q2
    feedback_mape_mae = (
        "✅ Correct!"
        if user_answer_mape_mae.value == "C"
        else "❌ Wrong. Try again!"
    )
    slide_mape_mae.content3 = mo.md(f"**Feedback:** {feedback_mape_mae}" if user_answer_mape_mae.value else "")
    return (slide_mape_mae,)


@app.cell
def _(slide_mape_mae):
    slide_mape_mae.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown quiz
    answer1 = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer1,)


@app.cell
def _(answer1, mo, sc):
    # Question 1: Moving Average vs Single Exponential Smoothing
    slide_ma_vs_ses = sc.create_slide(
        "Quiz: Moving Average vs Single Exponential Smoothing",
        layout_type="3-row"
    )

    slide_ma_vs_ses.content1 = mo.md(
        '''
    **Which of the following statements correctly contrasts the Moving Average (MA) method and Single Exponential Smoothing (SES)?**

    <ol type="a">
      <li>Both MA and SES assign the same weight to each of the last q observations.</li>
      <li>MA averages the last q observations with equal weights; SES uses a smoothing parameter α to assign exponentially decreasing weights to past data.</li>
      <li>SES forecasts are simply the average of the last q residuals, whereas MA updates the forecast by blending the previous forecast with the last observation.</li>
      <li>MA relies on a smoothing coefficient α ∈ (0,1), while SES uses a fixed window q of past observations.</li>
    </ol>
        '''
    )

    slide_ma_vs_ses.content2 = answer1

    # Conditional feedback for Q1
    feedback_ma_vs_ses = (
        "✅ Correct!"
        if answer1.value == "B"
        else "❌ Wrong. Try again!"
    )
    slide_ma_vs_ses.content3 = mo.md(f"**Feedback:** {feedback_ma_vs_ses}" if answer1.value else "")
    return (slide_ma_vs_ses,)


@app.cell(hide_code=True)
def _(slide_ma_vs_ses):
    slide_ma_vs_ses.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown quiz
    user_answer_ses_alpha = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (user_answer_ses_alpha,)


@app.cell
def _(mo, sc, user_answer_ses_alpha):



    # Question 3: Effect of α in SES
    slide_ses_alpha = sc.create_slide(
        "Quiz: Single Exponential Smoothing",
        layout_type="3-row"
    )

    slide_ses_alpha.content1 = mo.md(
        '''
    **What is the effect of increasing the smoothing parameter α in Single Exponential Smoothing?**

    <ol type="a">
      <li>The forecast becomes more responsive to recent changes and less smooth.</li>
      <li>The model relies more on older observations, making forecasts more stable.</li>
      <li>The weights on past observations decay more slowly, emphasizing long-term trends.</li>
      <li>The forecast update formula blends the previous forecast and last observation equally regardless of α.</li>
    </ol>
        '''
    )

    slide_ses_alpha.content2 = user_answer_ses_alpha

    # Conditional feedback for Q3
    feedback_ses_alpha = (
        "✅ Correct!"
        if user_answer_ses_alpha.value == "A"
        else "❌ Wrong. Try again!"
    )
    slide_ses_alpha.content3 = mo.md(f"**Feedback:** {feedback_ses_alpha}" if user_answer_ses_alpha.value else "")
    return (slide_ses_alpha,)


@app.cell
def _(slide_ses_alpha):
    slide_ses_alpha.render_slide()
    return


@app.cell
def _(sc):
    titleSlide2 = sc.create_slide(
        "Demand Planning Advanced",
        layout_type="title-slide",
        newSection="Demand Planning Advanced",
    )
    return (titleSlide2,)


@app.cell(hide_code=True)
def _(titleSlide2):
    titleSlide2.render_slide()
    return


@app.cell
def _(mo, sc):
    ses_drawbacks = sc.create_slide("Forecasting with Single Exponential Smoothing", layout_type="1-row")
    ses_drawbacks.content1 = mo.md(
    """
     **Limitations of Single Exponential Smoothing**

    - **Drawbacks of Single Exponential Smoothing:** Our Amoxicillin demand isn’t constant—it shows trends and clear seasonal swings.  
    A plain moving average can’t capture these effects. 
    - **Therefore we want to decompose the time series:**  
    By decomposing the series into **trend**, **seasonality**, and **noise**,  
    we can model each pattern separately,  extrapolate them into the future, and (hopefully) produce more accurate forecasts.
    - **Trend:** The overall long-term direction (rising, falling, or flat). 
    - **Seasonality:** Regular cycles or patterns (e.g., weekly, monthly, yearly).
    - **Noise:** Random fluctuations that aren’t explained by trend or seasonality.
    """
    )
    return (ses_drawbacks,)


@app.cell(hide_code=True)
def _(ses_drawbacks):
    ses_drawbacks.render_slide()
    return


@app.cell
def _(TimeSeriesDecompositionPlotter, history, mo, sc):
    # Slide: Introduction to Holt's Double Exponential Smoothing
    ts_decomposition = sc.create_slide(
        "Time Series Decomposition", layout_type="2-row"
    )

    plot_decomp = TimeSeriesDecompositionPlotter().fit(history).plot()

    ts_decomposition.content1 = mo.md(
        r"""
    - Our Amoxicillin demand shows a slight upward trend during the first 2 years, which flattens out in the last years.
    - There is also a clear yearly seasonality, with peaks in the winter months and troughs in the summer.
    - To capture these patterns, we will learn about **Double Exponential Smoothing** and **Triple Exponential Smoothing**.
    """
    )

    ts_decomposition.content2 = mo.ui.altair_chart(plot_decomp)
    return (ts_decomposition,)


@app.cell(hide_code=True)
def _(ts_decomposition):
    ts_decomposition.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt’s Linear Trend Method
    holt_intro1 = sc.create_slide(
        "Double Exponential Smoothing (Holt’s Method)", layout_type="3-row"
    )
    holt_intro1.content1 = mo.md(
        r"""
    - **Adds a trend component.**  
        - The main idea is to decompose the forecast \(f_t\) into two parts: an estimated level \(\ell_t\) and an estimated trend \(b_t\).
        - Both \(\ell_t\) and \(b_t\) are updated recursively using the smoothing parameters \(\alpha\) and \(\beta\), similar to the single exponential smoothing method.
    """
    )
    return (holt_intro1,)


@app.cell(hide_code=True)
def _(holt_intro1):
    holt_intro1.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt’s Linear Trend Method
    holt_intro2 = sc.create_slide(
        "Double Exponential Smoothing (Holt’s Method)", layout_type="1-column"
    )
    holt_intro2.content1 = mo.md(
        r"""
    **Model:**  

    - Smooth the estimated level:

    \[
    \ell_t = \alpha\,d_t + (1-\alpha)\, \underbrace{(\ell_{t-1} + b_{t-1})}_{\text{Forecast at t-1}}
    \]

    - Smooth the estimated trend:

    \[
    b_t = \beta\, \underbrace{(\ell_t - \ell_{t-1})}_{\text{Trend update}} + (1-\beta)\,b_{t-1}
    \]

    - Forecast based on level and trend

    \[
     f_{t+h} = \ell_t + h\,b_t \quad (h=1,2,3,4)
    \]

    - \(\alpha, \beta \in [0,1]\): smoothing weights (level vs. trend)
    - Larger \(\beta\) → more reactive to recent changes in the trend; 
    - Smaller \(\beta\) → smoother, slower updates of the trend.
    """
    )
    return (holt_intro2,)


@app.cell(hide_code=True)
def _(holt_intro2):
    holt_intro2.render_slide()
    return


@app.cell(hide_code=True)
def _(HoltDoubleExpPlotter):
    holt_plotter = HoltDoubleExpPlotter()
    return (holt_plotter,)


@app.cell(hide_code=True)
def _(mo):
    # Slider for alpha and beta parameters in Holt's method
    alpha_slider = mo.ui.slider(
        0.1, 1.0, value=0.1, step=0.1, label="Smoothing Parameter α (Level)"
    )
    beta_slider = mo.ui.slider(
        0.1, 1.0, value=0.1, step=0.1, label="Smoothing Parameter β (Trend)"
    )
    return alpha_slider, beta_slider


@app.cell
def _(alpha_slider, beta_slider, historic_forecast, holt_plotter, mo, sc):
    holt_visualization = sc.create_slide(
        "Double Exponential Smoothing (Holt’s Method)", layout_type="2-row"
    )

    # Add sliders for alpha and beta
    holt_visualization.content1 = mo.vstack([alpha_slider, beta_slider])

    holt_plotter.fit(df=historic_forecast, alpha=alpha_slider.value, beta=beta_slider.value)

    holt_plot = holt_plotter.plot()

    holt_visualization.content2 = mo.ui.altair_chart(holt_plot)
    return (holt_visualization,)


@app.cell(hide_code=True)
def _(holt_visualization):
    holt_visualization.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt’s Linear Trend Method with StatsForecast Library
    holt_statsforecast_slide = sc.create_slide(
        "Implementing Double Exponential Smoothing", layout_type="2-row"
    )

    holt_statsforecast_slide.content1 = mo.md(
        """
        - Use the `StatsForecast` package to apply Holt’s Linear Trend Method at scale:
        - Automatically optimizes both level (α) and trend (β) smoothing parameters.
        """
    )

    holt_statsforecast_slide.content2 = mo.md(
        """
        ```python
        from statsforecast import StatsForecast
        from statsforecast.models import Holt

        # Assume `historic` is a DataFrame with columns: unique_id, date, demand

        sf = StatsForecast(models=[Holt()], freq='W')
        forecasts_df = sf.forecast(
            df=historic,
            h=4,
            id_col="unique_id",
            time_col="date",
            target_col="demand"
        )
        ```
        """
    )
    return (holt_statsforecast_slide,)


@app.cell(hide_code=True)
def _(holt_statsforecast_slide):
    holt_statsforecast_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Holt Forecast Plot
    holt_slide = sc.create_slide(
        "Forecasting with Double Exponential Smoothing", layout_type="2-row"
    )
    holt_slide.content1 = mo.md("""
        Forecast using Holt’s method—captures both level and trend.  
        The smoothing parameters α and β are automatically optimized.  
        Unlike SES, which maintains a constant forecast over 4-week windows, Holt’s method increases the forecast over time.
    """
    )
    plot_holt = fc_plotter.plot(
        model_col="Holt",
        title="Holt’s Method",
        vertical_line=True,
        shade=True,
    )
    holt_slide.content2 = mo.ui.altair_chart(plot_holt)
    return (holt_slide,)


@app.cell(hide_code=True)
def _(holt_slide):
    holt_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt’s Linear Trend Method
    holt_winters_intro1 = sc.create_slide(
        "Triple Exponential Smoothing (Holt–Winters' Method)", layout_type="3-row"
    )
    holt_winters_intro1.content1 = mo.md(
        r"""
    - **Adds a seasonality component.**  
        - The main idea is to decompose the forecast \(f_t\) into three parts: an estimated level \(\ell_t\), an estimated trend \(b_t\), and an estimated seasonal component \(s_t\).
        - All three components are updated recursively using the smoothing parameters \(\alpha\), \(\beta\), and \(\gamma\).
    """
    )

    return (holt_winters_intro1,)


@app.cell(hide_code=True)
def _(holt_winters_intro1):
    holt_winters_intro1.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt–Winters Seasonal Method
    hw_theory1 = sc.create_slide(
        "Triple Exponential Smoothing (Holt–Winters' Method)", layout_type="1-column"
    )
    hw_theory1.content1 = mo.md(
        r"""
    - **Adds a seasonality component.**  
        - By including trend, Holt’s method can adapt to longer-term increases and decreases in the Amoxicillin demand.
        - Holt-Winters' method also accounts for seasonality. The forecast is then decomposed into three parts: an estimated level \(\ell_t\) an estimated trend \(b_t\) and an estimated seasonal component \(s_t\).
        - The method depends on the season length. In our case the season length is $m = 52$, which corresponds to the number of weeks in a year.
        - The forecast \(f_{t+1}\) is now given by 

        \[
    f_{t+1} =  \ell_t + \,b_t + \underbrace{s_{t-m+1}}_{\text{same week last year}}
    \]

    """
    )
    return (hw_theory1,)


@app.cell(hide_code=True)
def _(hw_theory1):
    hw_theory1.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt–Winters Seasonal Method
    hw_theory2 = sc.create_slide(
        "Triple Exponential Smoothing (Holt–Winters' Method)", layout_type="1-column"
    )
    hw_theory2.content1 = mo.md(
        r"""
     **Model:**  

    - Smooth the estimated level:

    \[
       \ell_t = \alpha \cdot \underbrace{(d_t - s_{t-m})}_{\text{de-seasonalized demand}} + (1 - \alpha)(\ell_{t-1} + b_{t-1})
    \]

    - Smooth the estimated trend:

    \[
       b_t = \beta(\ell_t - \ell_{t-1}) + (1 - \beta)\,b_{t-1}
    \]

    - Update estimated seasonality


    \[
       s_t = \gamma \cdot \underbrace{(d_t - \ell_t)}_{\text{seasonal effect}} + (1 - \gamma)\,s_{t-m}
    \]

    - Forecast based on level, trend and seasonality


    \[
       f_{t+h} = (\ell_t + h\,b_t) + s_{t-m+h} \quad (h=1,2,3,4)
    \]

    - \(\alpha, \beta, \gamma \in [0,1]\): smoothing weights for level, trend, seasonality
    - Larger \(\gamma\) → more reactive to recent changes in seasonality  
    - Smaller \(\gamma\) → smoother, slower updates of the seasonal component  
    """
    )
    return (hw_theory2,)


@app.cell(hide_code=True)
def _(hw_theory2):
    hw_theory2.render_slide()
    return


@app.cell(hide_code=True)
def _(HoltWintersPlotter):
    holt_winters_plotter = HoltWintersPlotter()
    return (holt_winters_plotter,)


@app.cell(hide_code=True)
def _(mo):
    # Slider for alpha and beta parameters in Holt's method
    alpha_slider_triple = mo.ui.slider(
        0.1, 1.0, value=0.1, step=0.1, label="Smoothing Parameter α (Level)"
    )
    beta_slider_triple = mo.ui.slider(
        0.1, 1.0, value=0.1, step=0.1, label="Smoothing Parameter β (Trend)"
    )
    gamma_slider_triple = mo.ui.slider(
        0.1, 1.0, value=0.1, step=0.1, label="Smoothing Parameter γ (Seasonality)"
    )
    return alpha_slider_triple, beta_slider_triple, gamma_slider_triple


@app.cell
def _(
    alpha_slider_triple,
    beta_slider_triple,
    gamma_slider_triple,
    historic_forecast,
    holt_winters_plotter,
    mo,
    sc,
):
    holt_winters_visualization = sc.create_slide(
        "Triple Exponential Smoothing (Holt–Winters Method)", layout_type="2-row"
    )

    # Add sliders for alpha and beta
    holt_winters_visualization.content1 = mo.vstack([alpha_slider_triple, beta_slider_triple, gamma_slider_triple])

    holt_winters_plotter.fit(df=historic_forecast, alpha=alpha_slider_triple.value, beta=beta_slider_triple.value, gamma=gamma_slider_triple.value, seasonal_periods=52)

    holt_winters_plot = holt_winters_plotter.plot()

    holt_winters_visualization.content2 = mo.ui.altair_chart(holt_winters_plot)
    return (holt_winters_visualization,)


@app.cell
def _(holt_winters_visualization):
    holt_winters_visualization.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide: Holt–Winters Seasonal Method with StatsForecast Library
    hw_statsforecast_slide = sc.create_slide(
        "Implementation of Triple Exponential Smoothing", layout_type="2-row"
    )

    hw_statsforecast_slide.content1 = mo.md(
        """
        - Use the `StatsForecast` package to apply Holt–Winters (triple exponential smoothing) at scale.  
        - Specify both trend and seasonality components with your desired seasonal period (e.g., 52 weeks for yearly seasonality).  
        - The package will automatically fit α, β and γ.
        """
    )

    hw_statsforecast_slide.content2 = mo.md(
        """
        ```python
        from statsforecast import StatsForecast
        from statsforecast.models import HoltWinters

        # Assume `historic` is a DataFrame with columns: unique_id, date, demand

        sf = StatsForecast(
            models=[HoltWinters(season_length=52,)],
            freq='W'
        )

        forecasts_df = sf.forecast(
            df=historic,
            h=4,
            id_col="unique_id",
            time_col="date",
            target_col="demand"
        )
        ```
        """
    )
    return (hw_statsforecast_slide,)


@app.cell(hide_code=True)
def _(hw_statsforecast_slide):
    hw_statsforecast_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Holt–Winters Plot
    hw_slide = sc.create_slide(
        "Forecasting with Triple Exponential Smoothing", layout_type="2-row"
    )
    hw_slide.content1 = mo.md(
        """Forecast using the Holt–Winters method to capture trend and seasonality simultaneously. """
    )
    plot_hw = fc_plotter.plot(
        model_col="Holt‑Winters",
        title="Holt–Winters Seasonal Forecast",
        vertical_line=True,
        shade=True,
    )
    hw_slide.content2 = mo.ui.altair_chart(plot_hw)
    return (hw_slide,)


@app.cell(hide_code=True)
def _(hw_slide):
    hw_slide.render_slide()
    return


@app.cell
def _(evaluations, mo, pd, sc):

    metrics_dict = evaluations.get("forecast", {}) or {}

    # Convert nested dict to DataFrame: index=model, columns=mae,mape
    df = pd.DataFrame.from_dict(metrics_dict, orient="index").reset_index().rename(
        columns={"index": "model"}
    )

    # If empty, create an empty table slide
    performance_slide = sc.create_slide(
        "Overall Model Performance",
        layout_type="2-row"
    )

    performance_slide.content1 = mo.md(
        """
        **Model Performance Comparison**

        The table below compares the forecasting accuracy of each method we've explored. 
        Notice how each increase in model complexity—from naive to moving average, 
        from single to double to triple exponential smoothing—progressively reduces 
        forecasting errors (MAE and MAPE), demonstrating the value of capturing 
        trend and seasonality patterns.
        """
    )

    # Format numeric columns
    df["MAE"] = df["mae"].astype(float).round(2)
    # Present MAPE as percentage with 2 decimals
    df["MAPE (%)"] = (df["mape"].astype(float) * 100).round(2)
    df["Model"] = df["model"].astype(str)
    # Keep only the columns we want to show and sort by MAE ascending
    df_display = df[["Model", "MAE", "MAPE (%)"]].sort_values("MAE").reset_index(drop=True)
    # Only keep rows that do not end with _<number>
    mask = ~df_display["Model"].str.contains(r"_\d+$", regex=True) | (df_display["Model"] == "MA_3")
    df_display = df_display[mask].reset_index(drop=True)

    performance_slide.content2 = mo.ui.table(df_display)
    return (performance_slide,)


@app.cell(hide_code=True)
def _(performance_slide):
    performance_slide.render_slide()
    return


@app.cell
def _(mo):
    user_answer_double = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (user_answer_double,)


@app.cell
def _(mo, sc, user_answer_double):
    # Question 3: Double Exponential Smoothing
    slide_double_exp = sc.create_slide(
        "Quiz: Double Exponential Smoothing",
        layout_type="3-row"
    )

    slide_double_exp.content1 = mo.md(
        '''
    **Which components are modeled by Holt’s Linear Trend method (double exponential smoothing)?**

    <ol type="a">
      <li>Level only, ignoring trend and seasonality.</li>
      <li>Level and seasonality, ignoring trend.</li>
      <li>Level and trend, without seasonality.</li>
      <li>Trend and seasonality, ignoring level.</li>
    </ol>
        '''
    )
    slide_double_exp.content2 = user_answer_double
    feedback_double = (
        "✅ Correct!" if user_answer_double.value == "C" else "❌ Wrong. Try again!"
    )
    slide_double_exp.content3 = mo.md(f"**Feedback:** {feedback_double}" if user_answer_double.value else "")
    return (slide_double_exp,)


@app.cell
def _(slide_double_exp):
    slide_double_exp.render_slide()
    return


@app.cell
def _(mo):
    user_answer_triple = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (user_answer_triple,)


@app.cell
def _(mo, sc, user_answer_triple):
    # Question 4: Triple Exponential Smoothing
    slide_triple_exp = sc.create_slide(
        "Quiz: Triple Exponential Smoothing",
        layout_type="3-row"
    )

    slide_triple_exp.content1 = mo.md(
        '''
    **What does the gamma (γ) parameter control in the Holt–Winters additive method (triple exponential smoothing)?**

    <ol type="a">
      <li>The smoothing of the level component.</li>
      <li>The smoothing of the trend component.</li>
      <li>The smoothing of the seasonal component.</li>
      <li>The blending between forecast and actual values.</li>
    </ol>
        '''
    )
    slide_triple_exp.content2 = user_answer_triple
    feedback_triple = (
        "✅ Correct!" if user_answer_triple.value == "C" else "❌ Wrong. Try again!"
    )
    slide_triple_exp.content3 = mo.md(f"**Feedback:** {feedback_triple}" if user_answer_triple.value else "")
    return (slide_triple_exp,)


@app.cell
def _(slide_triple_exp):
    slide_triple_exp.render_slide()
    return


if __name__ == "__main__":
    app.run()
