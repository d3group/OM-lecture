import marimo

__generated_with = "0.13.15"
app = marimo.App(
    width="medium",
    app_title="Demand Management",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    from utils.slides import SlideCreator
    from utils.data import DataLoader, DataSplitter
    from utils.forecast import ForecastLoader, Evaluator, ForecastPlotter, HoltDoubleExpPlotter, HoltWintersPlotter
    from sklearn.utils import Bunch
    import marimo as mo
    import numpy as np

    return (
        Bunch,
        DataLoader,
        DataSplitter,
        Evaluator,
        ForecastLoader,
        ForecastPlotter,
        SlideCreator,
        mo,
        np,
    )


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
        "Demand Management - Live Session",
        layout_type="title-slide",
        newSection="Demand Management - Live Session",
    )

    return (titleSlide,)


@app.cell(hide_code=True)
def _(titleSlide):
    titleSlide.render_slide()
    return


@app.cell
def _(mo, sc):
    introduction = sc.create_slide(
        "Let’s start with a very basic Forecasting task...", layout_type="2-row"
    )
    introduction.content1 = mo.image(
        "public/Demand_Management/images/distribution_center_fuerth.png",
        width=1000,
        style={"margin-right": "auto", "margin-left": "auto"},
    )
    introduction.content2 = mo.md(
    """In this live session, we’ll again work on a time series prediction task — this time,  
    the goal is to forecast the demand for Acetaminophen.  
    Unlike Amoxicillin, which is an antibiotic, Acetaminophen is a common pain reliever and fever reducer.  
    It's widely used to treat headaches, muscle aches, arthritis, backaches, toothaches, colds, and fevers.

    As before, we’ll start by importing the data. """
    )
    return (introduction,)


@app.cell
def _(introduction):
    introduction.render_slide()

    return


@app.cell(hide_code=True)
def _(DataLoader):
    loader = DataLoader()
    data = loader.load(file_path="public/data/demand_acetaminophen_500mg.csv")
    return (data,)


@app.cell
def _(data, mo, sc):
    history_slide = sc.create_slide("Historical Data for Acetaminophen", layout_type="3-row")
    history_slide.content1 = mo.md(
        """
        For this product, we have about 2 years of weekly historical data.
        """
    )
    history_slide.content2 = mo.md(
        """
    ```python
    import pandas as pd
    data_weekly = pd.read_csv(path_to_file)
    ```
    """
    )

    history_slide.content3 = mo.ui.table(data)
    return (history_slide,)


@app.cell(hide_code=True)
def _(history_slide):
    history_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(DataSplitter, data):
    splitter = DataSplitter(cutoff_date="2024-12-01")
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
        title="Weekly Demand of Acetaminophen 500mg",
        vertical_line=False,
        shade=False,
    )

    basic_forecasting1.content1 =  mo.md("""
    Let’s plot the historical data of weekly demand for Acetaminophen 500mg
    """)

    basic_forecasting1.content2 = mo.ui.altair_chart(plot)

    return (basic_forecasting1,)


@app.cell(hide_code=True)
def _(basic_forecasting1):
    basic_forecasting1.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown quiz
    answer_quiz_data = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_data,)


@app.cell
def _(answer_quiz_data, mo, sc):
    quiz_data_slide = sc.create_slide(
        "Quiz: Weekly Demand Characteristics",
        layout_type="3-row"
    )

    quiz_data_slide.content1 = mo.md(
        '''
    **Which of the following best describes the characteristics observed in the  
    historical weekly demand plot for Acetaminophen 500mg?**

    <ol type="a">
    <li>The demand shows a stable trend with consistent seasonality and no significant outliers.</li>
    <li>The demand exhibits random fluctuations around a constant mean, with occasional drops likely due to holidays.</li>
    <li>The demand displays a clear upward trend with volatility and occasional spikes, possibly due to external events like competitor stockouts.</li>
    <li>The demand is entirely predictable, showing regular periodic cycles without any irregular variation.</li>
    </ol>

        '''
    )

    quiz_data_slide.content2 = answer_quiz_data

    # Conditional feedback
    feedback_data_slide = (
        "✅ Correct!"
        if answer_quiz_data.value == "C"
        else "❌ Wrong. Try again!"
    )
    quiz_data_slide.content3 = mo.md(f"**Feedback:** {feedback_data_slide}" if answer_quiz_data.value else "")
    return (quiz_data_slide,)


@app.cell(hide_code=True)
def _(quiz_data_slide):
    quiz_data_slide.render_slide()
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
    ForecastManager,
    MA_CONFIG,
    SES_CONFIG,
    data,
    fc_plotter,
    history,
    mo,
    np,
    public_dir,
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

    fc_manager = ForecastManager(
        freq="W",
        model_params=params,
        forecast_path=f"{public_dir}/data/forecast_live_session.csv",
        historic_path=f"{public_dir}/data/historic_forecast_live_session.csv",
        overwrite=False,
    )
    forecast, historic_forecast = fc_manager.run(
        data=data,
        history=history,
        n_windows=6,
        historic_n_windows=1,
        step_size=4,
        h=4,
    )

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
def _(mo):
    # Create dropdown for the Naive Forecast question
    answer_quiz_naive = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_naive,)


@app.cell
def _(answer_quiz_naive, mo, sc):


    # Create a new slide for the Naive method quiz
    quiz_naive_slide = sc.create_slide(
        "Quiz: Naive Forecast Method",
        layout_type="3-row"
    )

    # Intro and question text
    quiz_naive_slide.content1 = mo.md(
        '''
    Like in the last online session, the first method we will apply is the Naive Forecast.

    **Which statement best describes the Naive forecast for the next four weeks?**

    <ol type="a">
    <li>The forecast remains constant at the last observed weekly demand value for all four weeks.</li>
    <li>The forecast shows a linear upward trend based on the average increase over the last season.</li>
    <li>The forecast alternates between the two most recent observations.</li>
    <li>The forecast equals the mean of the last four weeks for each of the next four weeks.</li>
    </ol>
        '''
    )

    # Attach the answer dropdown
    quiz_naive_slide.content2 = answer_quiz_naive

    # Conditional feedback based on selected answer
    feedback_naive = (
        "✅ Correct!" 
        if answer_quiz_naive.value == "A" 
        else "❌ Wrong. Try again!"
    )
    quiz_naive_slide.content3 = mo.md(f"**Feedback:** {feedback_naive}" if answer_quiz_naive.value else "")

    return (quiz_naive_slide,)


@app.cell(hide_code=True)
def _(quiz_naive_slide):
    quiz_naive_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(Evaluator, fc_plotter, forecast, historic_forecast):
    evaluator = Evaluator(forecast=forecast, historic_forecast=historic_forecast)
    evaluations = evaluator.evaluate()
    fc_plotter.add_metrics(evaluations)
    return


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

    evaluation_naive.content1 = mo.md("""
    We can see that the naive forecast clearly struggles to capture the fluctuations in future demand.
    """)
    evaluation_naive.content2 = mo.ui.altair_chart(plot_naive_with_metric)
    return (evaluation_naive,)


@app.cell(hide_code=True)
def _(evaluation_naive):
    evaluation_naive.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown for the Moving Average Forecast question
    answer_quiz1_ma = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )

    return (answer_quiz1_ma,)


@app.cell
def _(answer_quiz1_ma, mo, sc):

    # Create a new slide for the Moving Average method quiz
    quiz1_ma_slide = sc.create_slide(
        "Quiz: Moving Average Forecast Method",
        layout_type="3-row"
    )

    # Intro and question text
    quiz1_ma_slide.content1 = mo.md(
        '''
    Having applied the Naive Forecast, we now turn to the Moving Average method.

    **Which statement best describes a 4‑week Moving Average forecast for the next four weeks?**

    <ol type="a">
    <li>The forecast repeats the last observed demand value for all forecasted weeks.</li>
    <li>The forecast equals the average demand of the most recent four weeks for each of the next four weeks.</li>
    <li>The forecast uses a weighted average that assigns greater importance to more recent weeks.</li>
    <li>The forecast calculates the difference between the highest and lowest demand in the last four weeks.</li>
    </ol>
        '''
    )

    # Attach the answer dropdown
    quiz1_ma_slide.content2 = answer_quiz1_ma

    # Conditional feedback based on selected answer
    feedback1_ma = (
        "✅ Correct!" 
        if answer_quiz1_ma.value == "B" 
        else "❌ Wrong. Try again!"
    )
    quiz1_ma_slide.content3 = mo.md(f"**Feedback:** {feedback1_ma}" if answer_quiz1_ma.value else "")

    return (quiz1_ma_slide,)


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


@app.cell(hide_code=True)
def _(quiz1_ma_slide):
    quiz1_ma_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(fc_plotter, mo, q_slider, sc):
    evaluation_ma_q = sc.create_slide("Moving Average Forecasting", layout_type="3-row")
    evaluation_ma_q.content1 = mo.md(""" 
    The parameter q sets how many past data points to average.  
    A larger q makes forecast smoother but slower to react;  
    a smaller q more responsive but noisier.  
    To pick the best q, compare the forecast errors (MAE or MAPE)  
    for different q values on the historical data and choose the one with the lowest error.
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
    return


@app.cell
def _(fc_plotter, mo, sc):
    evaluation_ma1 = sc.create_slide(
        "Forecasting with Moving Average", layout_type="2-row"
    )
    evaluation_ma1.content1 = mo.md(
        """
        We can see that the moving‐average model produces noticeably smoother forecasts than the naive approach,  
        yielding lower MAE and MAPE. The window size $q=5$ was tuned on the training set.
    """
    )
    plot_ma16 = fc_plotter.plot(
        model_col="MA_5",
        title="Forecast of the Weekly Demand using the Moving Average Method [MA(5)]",
        vertical_line=True,
        shade=True,
    )
    evaluation_ma1.content2 = mo.ui.altair_chart(plot_ma16)
    return (evaluation_ma1,)


@app.cell(hide_code=True)
def _():
    # evaluation_ma_q.render_slide()
    return


@app.cell(hide_code=True)
def _(evaluation_ma1):
    evaluation_ma1.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown quiz
    answer_ma = mo.ui.dropdown(
        options=["A", "B", "C"],
        label="Your answer"
    )
    return (answer_ma,)


@app.cell
def _(answer_ma, mo, sc):
    quiz_ma_slide = sc.create_slide(
        "Quiz: Naive Forecasting and Moving Average",
        layout_type="3-row"
    )

    quiz_ma_slide.content1 = mo.md(
        '''
    **Why is the Moving Average method performing better than the Naive method?**

    <ol type="a">
      <li>The Naive method overreacts to the latest data point, while the Moving Average smooths out fluctuations by averaging over multiple periods.</li>
      <li>The moving average method can better capture the positive trend in the data, while the Naive method assumes no change.</li>
      <li>The Naive method does not account for seasonality, while the Moving Average method does.</li>
    </ol>
    '''
    )

    quiz_ma_slide.content2 = answer_ma

    # Conditional feedback based on the selected answer
    feedback_ma = (
        "✅ Correct!"
        if answer_ma.value == "A"
        else "❌ Wrong. Try again!"
    )
    quiz_ma_slide.content3 = mo.md(f"**Feedback:** {feedback_ma}" if answer_ma.value else "")

    return (quiz_ma_slide,)


@app.cell
def _(quiz_ma_slide):
    quiz_ma_slide.render_slide()
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


@app.cell(hide_code=True)
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
    return


@app.cell(hide_code=True)
def _():
    # ses_slide_plot.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown for the Exponential Smoothing question
    answer_quiz_es = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_es,)


@app.cell
def _(answer_quiz_es, mo, sc):
    # Create a new slide for the Exponential Smoothing quiz
    quiz_es_slide = sc.create_slide(
        "Quiz: Exponential Smoothing Method",
        layout_type="3-row"
    )
    # Intro and question text for Exponential Smoothing
    quiz_es_slide.content1 = mo.md(
        '''
    We evaluate the Simple Exponential Smoothing model’s accuracy next.

    **Which statement best describes a Simple Exponential Smoothing forecast?**

    <ol type="a">
    <li>The forecast equals the simple average of all past observations up to the present.</li>
    <li>The forecast applies exponential smoothing separately to level and seasonal components.</li>
    <li>The forecast uses a moving window with exponentially decaying weights.</li>
    <li>The forecast equals the previous forecast adjusted by a smoothing factor times the last forecast error.</li>

    </ol>
        '''
    )

    # Attach the answer dropdown for Exponential Smoothing
    quiz_es_slide.content2 = answer_quiz_es

    # Conditional feedback for Exponential Smoothing
    feedback_es = (
        "✅ Correct!"  
        if answer_quiz_es.value == "D" 
        else "❌ Wrong. Try again!"
    )
    quiz_es_slide.content3 = mo.md(f"**Feedback:** {feedback_es}" if answer_quiz_es.value else "")

    return


@app.cell
def _():
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Single Exponential Smoothing (SES)
    ses_optimized_slide_plot = sc.create_slide(
        "Forecasting with Single Exponential Smoothing", layout_type="2-row"
    )
    ses_optimized_slide_plot.content1 = mo.md("""
        The SES model with the tuned α produces forecasts much like the moving average  
        but achieves slightly better accuracy."""
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
    answer_ses = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_ses,)


@app.cell
def _(answer_ses, mo, sc):
    # Create the quiz slide for SES
    quiz_ses_slide = sc.create_slide(
        "Quiz: Single Exponential Smoothing",
        layout_type="3-row"
    )

    # Question and options
    quiz_ses_slide.content1 = mo.md(
        '''
    **What is the main advantage of using Single Exponential Smoothing (SES) over  
    the Simple Moving Average method?**

    <ol type="a">
      <li>SES responds more quickly to recent changes in demand by assigning higher weight to recent observations.</li>
      <li>SES automatically detects trends and seasonality in the data without any tuning.</li>
      <li>SES gives equal weight to all past observations, making it more stable during demand shifts.</li>
      <li>SES requires no parameters, making it easier to implement than the Moving Average method.</li>
    </ol>
        '''
    )

    # Answer widget
    quiz_ses_slide.content2 = answer_ses

    # Conditional feedback based on the selected answer
    feedback_ses = (
        "✅ Correct!"
        if answer_ses.value == "A"
        else "❌ Wrong. Try again!"
    )
    quiz_ses_slide.content3 = mo.md(f"**Feedback:** {feedback_ses}" if answer_ses.value else "")

    return (quiz_ses_slide,)


@app.cell(hide_code=True)
def _(quiz_ses_slide):
    quiz_ses_slide.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown for Holt’s Method question
    answer_quiz_holt = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )

    return (answer_quiz_holt,)


@app.cell
def _(answer_quiz_holt, mo, sc):

    # Create a new slide for Holt’s Method quiz
    quiz_holt_slide = sc.create_slide(
        "Quiz: Holt’s Method",
        layout_type="3-row"
    )

    # Intro and question text for Holt’s Method
    quiz_holt_slide.content1 = mo.md(
        '''
    Let’s now assess Holt’s method, which extends SES by adding trend smoothing.

    **Which statement best describes Holt’s forecasting method?**

    <ol type="a">
    <li>It adds a trend component to exponential smoothing, allowing forecasts to follow upward or downward trends.</li>
    <li>It uses a seasonal index updated weekly based on the last year’s data.</li>
    <li>It averages the forecasts from SES and the Moving Average method.</li>
    <li>It relies on differencing to remove non-stationarity before forecasting.</li>
    </ol>
        '''
    )

    # Attach the answer dropdown for Holt’s Method
    quiz_holt_slide.content2 = answer_quiz_holt

    # Conditional feedback for Holt’s Method
    feedback_holt = (
        "✅ Correct!" 
        if answer_quiz_holt.value == "A" 
        else "❌ Wrong. Try again!"
    )
    quiz_holt_slide.content3 = mo.md(f"**Feedback:** {feedback_holt}" if answer_quiz_holt.value else "")
    return (quiz_holt_slide,)


@app.cell(hide_code=True)
def _(quiz_holt_slide):
    quiz_holt_slide.render_slide()
    return


@app.cell
def _(mo):
    # Create dropdown for trend evaluation question
    answer_quiz_trend = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_trend,)


@app.cell
def _(answer_quiz_trend, fc_plotter, mo, sc):



    # Create a new slide for evaluating trend smoothing
    quiz_trend_slide = sc.create_slide(
        "Quiz: Smoothing the Trend",
        layout_type="3-row"
    )

    # Plot showing trend behavior
    plot_trend = fc_plotter.plot(
        title="Weekly Demand of Acetaminophen 500mg",
        vertical_line=True,
        shade=True,
    )

    # Intro and question text for trend
    quiz_trend_slide.content1 = mo.md(
        '''
    Now let’s think about the trend observed in the data.

    **How does the trend behave across training and test sets, and how should we treat it?**

    <ol type="a">
    <li>The trend is strong in both training and test sets, so it should be heavily smoothed.</li>
    <li>The trend is flat in both training and test sets, so trend smoothing can be ignored.</li>
    <li>The trend is strong in training but flattens in the test set, so trend smoothing should be adjusted to improve test performance.</li>
    <li>The trend is erratic, and therefore cannot be smoothed effectively.</li>
    </ol>
        '''
    )

    # Attach the answer dropdown and plot
    quiz_trend_slide.content2 = mo.ui.altair_chart(plot_trend)

    # Conditional feedback for trend
    feedback_trend = (
        "✅ Correct!" 
        if answer_quiz_trend.value == "C" 
        else "❌ Wrong. Try again!"
    )
    quiz_trend_slide.content3 = mo.vstack([
        answer_quiz_trend,
        mo.md(f"**Feedback:** {feedback_trend}" if answer_quiz_trend.value else "")
    ])
    return (quiz_trend_slide,)


@app.cell
def _(quiz_trend_slide):
    quiz_trend_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Holt Forecast Plot
    holt_slide = sc.create_slide(
        "Forecasting with Double Exponential Smoothing", layout_type="2-row"
    )
    holt_slide.content1 = mo.md(
    """
    In the training period, the trend is consistently upward, so it can be smoothed more heavily.    
    However, in the test set, the trend flattens, and stronger updates (i.e. a larger β) are needed.   
    Since beta is tuned on the training set, the model adapts too slowly in the test period,  
    which can make DES perform worse than SES.
    """
    )
    plot_holt = fc_plotter.plot(
        model_col="Holt",
        title="Holt’s Linear Trend Forecast",
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
def _(mo):
    # Create dropdown for Triple Exponential Smoothing question
    answer_quiz_tes = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_tes,)


@app.cell
def _(answer_quiz_tes, mo, sc):
    # Create a new slide for Triple Exponential Smoothing quiz
    quiz_tes_slide = sc.create_slide(
        "Quiz: Triple Exponential Smoothing",
        layout_type="3-row"
    )

    quiz_tes_slide.content1 = mo.md(
        '''
    Now let’s evaluate Triple Exponential Smoothing (Holt-Winters).

    **Which statement best describes Triple Exponential Smoothing?**

    <ol type="a">
    <li>It smooths level, trend, and seasonality components to forecast series with trend and seasonality.</li>
    <li>It only smooths the trend component and ignores seasonality.</li>
    <li>It fits a linear regression and adds random noise to simulate seasonal variation.</li>
    <li>It assumes no trend and no seasonality, like simple exponential smoothing.</li>
    </ol>
        '''
    )

    quiz_tes_slide.content2 = answer_quiz_tes

    feedback_tes = (
        "✅ Correct!" 
        if answer_quiz_tes.value == "A" 
        else "❌ Wrong. Try again!"
    )
    quiz_tes_slide.content3 = mo.md(f"**Feedback:** {feedback_tes}" if answer_quiz_tes.value else "")


    return (quiz_tes_slide,)


@app.cell(hide_code=True)
def _(quiz_tes_slide):
    quiz_tes_slide.render_slide()
    return


@app.cell
def _(mo):

    # Create dropdown for seasonality question
    answer_quiz_seasonality = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_seasonality,)


@app.cell
def _(answer_quiz_seasonality, fc_plotter, mo, sc):


    # Plot showing trend behavior
    plot_seasonality = fc_plotter.plot(
        title="Weekly Demand of Acetaminophen 500mg",
        vertical_line=True,
        shade=True,
    )

    # Create a new slide for evaluating seasonality
    quiz_seasonality_slide = sc.create_slide(
        "Quiz: Seasonality in the Data",
        layout_type="3-row"
    )



    quiz_seasonality_slide.content1 = mo.md(
        '''
    Now let’s consider seasonality in the data.

    **How should we interpret the observed pattern in the first weeks of the year?**

    <ol type="a">
    <li>The series shows clear yearly seasonality with a strong peak every January.</li>
    <li>There is no seasonality at all, and the January peak is just noise.</li>
    <li>The peak in January is a one-time effect, not recurring seasonality.</li>
    <li>The pattern is due to calendar misalignment and should be removed.</li>
    </ol>
        '''
    )

    quiz_seasonality_slide.content2 =  mo.ui.altair_chart(plot_seasonality)


    feedback_seasonality = (
        "✅ Correct!" 
        if answer_quiz_seasonality.value == "C" 
        else "❌ Wrong. Try again!"
    )

    quiz_seasonality_slide.content3 = mo.vstack([
        answer_quiz_seasonality,
    mo.md(f"**Feedback:** {feedback_seasonality}" if answer_quiz_seasonality.value else "")
    ])




    return (quiz_seasonality_slide,)


@app.cell(hide_code=True)
def _(quiz_seasonality_slide):
    quiz_seasonality_slide.render_slide()
    return


@app.cell
def _(fc_plotter, mo, sc):
    # Slide: Holt–Winters Plot
    hw_slide = sc.create_slide(
        "Forecasting with Triple Exponential Smoothing", layout_type="2-row"
    )
    hw_slide.content1 = mo.md(
        """The Triple Exponential Smoothing model misinterprets a one-time spike in January 2024 as a seasonal effect.  
        As a result, it repeats the spike in future forecasts, which leads to overfitting and reduced predictive performance."""
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
def _(mo):
    # Create dropdown for recommended model question
    answer_quiz_recommend = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )

    return (answer_quiz_recommend,)


@app.cell
def _(answer_quiz_recommend, mo, sc):

    # Create slide for model recommendation
    quiz_recommend_slide = sc.create_slide(
        "Quiz: Recommended Forecasting Model",
        layout_type="3-row"
    )

    quiz_recommend_slide.content1 = mo.md(
        '''
    Based on forecast accuracy and model behavior:

    **Which model is most appropriate for this demand forecasting task?**

    <ol type="a">
    <li>Naive Forecast</li>
    <li>Triple Exponential Smoothing</li>
    <li>Single Exponential Smoothing or Double Exponential Smoothing with high α</li>
    <li>Moving Average with a large window size</li>
    </ol>
        '''
    )

    quiz_recommend_slide.content2 = answer_quiz_recommend

    feedback_recommend = (
        "✅ Correct!" 
        if answer_quiz_recommend.value == "C" 
        else "❌ Wrong. Try again!"
    )
    quiz_recommend_slide.content3 = mo.md(f"**Feedback:** {feedback_recommend}" if answer_quiz_recommend.value else "")

    return (quiz_recommend_slide,)


@app.cell
def _(quiz_recommend_slide):
    quiz_recommend_slide.render_slide()
    return


if __name__ == "__main__":
    app.run()
