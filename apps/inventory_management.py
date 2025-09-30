import marimo

__generated_with = "0.15.5"
app = marimo.App(
    width="medium",
    app_title="Demand Management",
    layout_file="layouts/inventory_management.slides.json",
    css_file="d3.css",
)



@app.cell(hide_code=True)
def _():
    class DataURLs:
        BASE = "https://raw.githubusercontent.com/moobeck/OM-lecture/refs/heads/main/apps/public/data"
        DEMAND = f"{BASE}/daily_demand_data_fuerth.csv"
        FORECAST = f"{BASE}/forecast_fuerth.csv"
        HISTORIC_FORECAST = f"{BASE}/historic_forecast_fuerth.csv"

    class ImageURLs:
        BASE = "https://raw.githubusercontent.com/moobeck/OM-lecture/refs/heads/preprocess/apps/public/images"
        DISTRIBUTION_CENTER = f"{BASE}/distribution_center_fuerth.png"



    return (DataURLs, ImageURLs)



@app.cell(hide_code=True)
async def _():
    import micropip
    import urllib.request
    import os

    class UtilsManager:
        def __init__(self, dest_folder="utils"):
            self.dest_folder = dest_folder
            self.files = ["data.py", "forecast.py", "slides.py", "inventory.py"]
            self.base_url = "https://raw.githubusercontent.com/moobeck/OM-lecture/preprocess/apps/utils/"
            self.packages = [
                "pandas",
                "altair",
                "scikit-learn",
                "numpy",
                "statsmodels",
                "scipy",
                "typing_extensions",
                "utilsforecast"
            ]
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

            for f in self.files:
                url = self.base_url + f
                dest_path = os.path.join(self.dest_folder, f)
                urllib.request.urlretrieve(url, dest_path)
                print(f"📥 Downloaded {f} to {dest_path}")

            self.files_downloaded = True

    utils_manager = UtilsManager()

    await utils_manager.install_packages()
    utils_manager.download_files()

    return (utils_manager,)


@app.cell(hide_code=True)
def _():
    from utils.slides import SlideCreator
    from utils.data import DataLoader
    from utils.inventory import SimpleForecastPlotter, SafetyStockPlotter
    from sklearn.utils import Bunch
    import marimo as mo
    return (
        Bunch,
        DataLoader,
        SafetyStockPlotter,
        SimpleForecastPlotter,
        SlideCreator,
        mo,
    )


@app.cell(hide_code=True)
def _(mo):
    public_dir = (
        str(mo.notebook_location) + "/public"
        if str(mo.notebook_location).startswith("https://")
        else "public"
    )
    return


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
        "Inventory Management - Basics and Intuition",
        layout_type="title-slide",
        newSection="Inventory Management - Basics and Intuition",
    )
    return (titleSlide,)


@app.cell(hide_code=True)
def _(titleSlide):
    titleSlide.render_slide()
    return


@app.cell
def _(mo, sc, ImageURLs):
    introduction = sc.create_slide(
        "From Demand Management to Inventory Management",
        layout_type="2-row",
    )
    introduction.content1 = mo.image(
        ImageURLs.DISTRIBUTION_CENTER,
        width=1000,
        style={"margin-right": "auto", "margin-left": "auto"},
    )
    introduction.content2 = mo.md(
    """Another Planning Tasks of Phoenix is to manage the inventory levels at their distribution centers. 
     In this example, we will again focus on the distribution center in Fürth, Germany,
     which is responsible for the supply of the region around Fürth."""
    )
    return (introduction,)


@app.cell(hide_code=True)
def _(introduction):
    introduction.render_slide()
    return


@app.cell(hide_code=True)
def _(DataLoader, DataURLs):
    loader = DataLoader()
    data = loader.load(file_path=DataURLs.DEMAND)
    # Filter for date 2025-07-01
    data = data[data.date >= "2025-07-01"].reset_index(drop=True)
    return (data,)


@app.cell
def _(data, mo, sc):
    history_slide = sc.create_slide("Historical Data for Amoxicillin", layout_type="3-row")
    history_slide.content1 = mo.md(
        """
        For the inventory management task, we will again use the historical demand data of the drug Amoxicillin. 
        Here we do not aggregate the data to weekly demand, but focus on the daily demand data of the last month.
       """
    )
    history_slide.content2 = mo.md(
        """
    ```python
    import pandas as pd
    history = pd.read_csv(path_to_history_csv)
    history = history[history.date >= "2025-07-01"].reset_index(drop=True)
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
def _(SimpleForecastPlotter, data):
    fc_plotter = SimpleForecastPlotter(history=data)
    return (fc_plotter,)


@app.cell
def _(fc_plotter, mo, sc):
    basic_inventory1 = sc.create_slide("Historical Data", layout_type="2-row")
    plot = fc_plotter.plot(
        title="Daily Demand of Amoxicilin (Fürth Region)",
    )

    basic_inventory1.content1 =  mo.md("""

    We now have to decide how the company Phoenix should manage the inventory levels at their distribution center in Fürth.
    For this the company needs to decide how often to order the drug Amoxicillin and how much to order each time.

    """)

    basic_inventory1.content2 = mo.ui.altair_chart(plot)
    return (basic_inventory1,)


@app.cell(hide_code=True)
def _(basic_inventory1):
    basic_inventory1.render_slide()
    return


@app.cell
def _(mo, sc):
    basic_inventory2 = sc.create_slide(
        "Basic Inventory Management", layout_type="1-column"
    )
    basic_inventory2.content1 = mo.md(
        """
        For this inventory management task, we assume that Phoenix can place orders every day  
        and that the lead time is two days (i.e., an order placed today arrives in two days).  
        The company needs to balance three objectives:

        - **Minimize Stockouts:**  
          Ensure the distribution center always has enough stock to meet demand.
        - **Minimize Inventory Costs:**  
          Avoid holding excess inventory to reduce storage and capital expenses.
        - **Minimize Order Costs:**  
          Limit the frequency of orders to lower administrative and processing costs.
        """
    )

    return (basic_inventory2,)


@app.cell(hide_code=True)
def _(basic_inventory2):
    basic_inventory2.render_slide()
    return


@app.cell
def _(mo, sc):
    basic_inventory3 = sc.create_slide(
        "Basic Inventory Management", layout_type="1-column"
    )
    basic_inventory3.content1 = mo.md(
        """
        But how do we balance these objectives?  
        To do this we formalize the cost trade-off between holding inventory, stockouts, and ordering costs.   
        Then we can choose the order policy based on the cost measured on the historical data  
        (like we did with the forecasting metrics).

        """
    )

    return (basic_inventory3,)


@app.cell(hide_code=True)
def _(basic_inventory3):
    basic_inventory3.render_slide()
    return


@app.cell
def _(mo, sc):
    tradeoff_slide = sc.create_slide(
        "Formalizing the Cost Trade-off",
        layout_type="1-column"
    )

    tradeoff_slide.content1 = mo.md(r"""
        To formalize the  inventory management problem, we define the following:

        - **Decision Variables:** 
            - \(Q_t\): Quantity ordered at the beginning of day \(t\)  
            - \(I_t\): Inventory level at the end of day \(t\)

        - **Inventory Dynamics:**
            - Inventory at the end of day \(t\) is given by:

            \[
                I_t = I_{t-1} + Q_{t-L} - D_t
            \]

            - where \(D_t\) is the demand on day \(t\) and \(L\) is the lead time (2 days in this case).
            - If \(I_t < 0\), it indicates a stockout, meaning demand exceeds available inventory.  
            - In this case, we cannot fulfill the demand and the demand is backordered.
    """)
    return (tradeoff_slide,)


@app.cell
def _(tradeoff_slide):
    tradeoff_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    tradeoff_slide2 = sc.create_slide(
        "Formalizing the Cost Trade-off",
        layout_type="1-column"
    )

    tradeoff_slide2.content1 = mo.md(r"""
        Now we formalize the trade-off between holding inventory, stockouts, and ordering costs:

        - **Cost Parameters:**  
            - \(h\): Unit holding cost per day  
            - \(p\): Unit shortage penalty cost per day  
            - \(K\): Fixed cost per order (incurred if \(Q_t > 0\))  
            - \(c\): Variable cost per unit ordered  

        - **Objective Function**:

             If we cannot fulfill the demand \(I_{t} < 0\), then we incur a shortage penalty cost:

            \[ 
            p \cdot (-I_{t})
            \]

             If \(I_t \geq 0\), then we incur holding costs:

            \[
            h \cdot I_{t}
            \]

             If we place an order \(Q_t > 0\), then we incur ordering costs:

            \[
            K + c\cdot  Q_{t} 
            \]

        - **Total Cost per Period:**  
             The total cost in period \(t\) is:

            \[
            C_t(Q_t, I_t) = 
            \begin{cases}
                p \cdot (-I_t) +  y_t(K + c Q_t), & \text{if } I_t < 0 \\
                h \cdot I_t + y_t(K + c Q_t), & \text{if } I_t \geq 0
            \end{cases}
            \]

                      where \(y_t = 1\) if we order in period t, and \(y_t = 0\) if we do not order.

    """)
    return (tradeoff_slide2,)


@app.cell
def _(tradeoff_slide2):
    tradeoff_slide2.render_slide()
    return


@app.cell(hide_code=True)
def _(Bunch, data, mo):
    from utils.inventory import InventoryPlotter, InventoryConfig, QRPolicy, QRForecasting



    inv_cfg = InventoryConfig(
        order_cost=500, 
        holding_cost=3,
        stockout_cost=5,
        lead_time=2
    )

    qr_optimal = QRPolicy(config=inv_cfg)
    qr_optimal.fit(data['demand'], parallel=True)
    print("Optimal parameters for (Q, R) policy:")
    print(qr_optimal.params)
    print(f"average demand {int(data.demand.mean())}")

    QR_CONFIG = Bunch(
        min=0,
        max=300,
        step=10,
        q_default=250,
        r_default=0
    )

    q_slider = mo.ui.slider(
        QR_CONFIG.min,
        QR_CONFIG.max,
        value=QR_CONFIG.q_default,
        label="###Order Quantity (Q)",
        step=QR_CONFIG.step,
    )

    r_slider = mo.ui.slider(
        QR_CONFIG.min,
        QR_CONFIG.max,
        value=QR_CONFIG.r_default,
        label="###Reorder Point (R)",
        step=QR_CONFIG.step,
    )





    plotter = InventoryPlotter(data, date_col='date', demand_col='demand', config=inv_cfg)
    return (
        InventoryConfig,
        QRForecasting,
        QRPolicy,
        inv_cfg,
        plotter,
        q_slider,
        qr_optimal,
        r_slider,
    )


@app.cell
def _(mo, sc):

    qr_first_slide1 = sc.create_slide("A First Order Policy ", layout_type="1-row")


    qr_first_slide1.content1 = mo.md(r"""
            Let's assume the following cost parameters for our inventory management problem:

            - **Order cost:** 500  
            - **Holding cost:** 3  
            - **Stock-out cost:** 5  
            - **Lead time:** 2 days

            Now, let's start with a simple order policy:

            - **Reorder Point Strategy:**  
                - We place an order of size 250 units  
                - **Trigger:** Whenever the inventory position drops to zero  

            - **Ordering Rule:**  

                \[
                \text{If inventory position } I_t \leq 0, \text{ then order } Q_t = 250
                \]  

                \[
                \text{Else, } Q_t = 0
                \]
    """)


    return (qr_first_slide1,)


@app.cell
def _(qr_first_slide1):
    qr_first_slide1.render_slide()
    return


@app.cell
def _(QRPolicy, data, inv_cfg, mo, plotter, sc):
    qr_first_slide= sc.create_slide("First Shot Policy Evaluated on Historical Data", layout_type="3-row")



    q_first = 250
    r_first = 0 


    qr_first_slide.content1 = mo.md("""
    Let’s evaluate our policy using historical demand data. We notice that it leads to frequent stockouts.
    """)


    qr_first = QRPolicy(config=inv_cfg).set_params(data['demand'], Q=q_first, R=r_first)

    qr_first_plot = plotter.plot(policy=qr_first)
    qr_first_slide.content2 = mo.ui.altair_chart(qr_first_plot)
    return (qr_first_slide,)


@app.cell(hide_code=True)
def _(qr_first_slide):
    qr_first_slide.render_slide()
    return


@app.cell
def _(mo, sc):

    qr_motivation_slide =  sc.create_slide("The QR Order Policy", layout_type="1-row")


    qr_motivation_slide.content1 = mo.md(r"""
        To reduce stockouts, we introduce a reorder point \(R\) and order quantity \(Q\):

        - **Reorder Point \(R\):**  
          Inventory level at which we place a new order  

        - **Order Quantity \(Q\):**  
          Fixed number of units ordered each time we hit \(R\)  

        - **Ordering Rule:**  

            \[
            \text{If inventory position } I_t \leq R, \text{ then order } Q
            \]  

            \[
            \text{Else, } Q_t = 0
            \]

        - **Optimal Parameters:**  
          We can determine \(R\) and \(Q\) using historical demand data, i.e., we look for the \(R\) and \(Q\) that would have minimized our costs in the past.   
          (remember: we did something very similar in demand forecasting) 

    """)
    return (qr_motivation_slide,)


@app.cell(hide_code=True)
def _(qr_motivation_slide):
    qr_motivation_slide.render_slide()
    return


@app.cell
def _(QRPolicy, data, inv_cfg, mo, plotter, q_slider, r_slider, sc):
    qr_manual_slide = sc.create_slide("Finding QR Policy Parameters Based on Historical Data", layout_type="3-row")



    qr_manual_slide.content1 = q_slider
    qr_manual_slide.content2 = r_slider

    qr_manual = QRPolicy(config=inv_cfg).set_params(data['demand'], Q=q_slider.value, R=r_slider.value)

    qr_manual_plot = plotter.plot(policy=qr_manual)
    qr_manual_slide.content3 = mo.ui.altair_chart(qr_manual_plot)
    return (qr_manual_slide,)


@app.cell(hide_code=True)
def _(qr_manual_slide):
    qr_manual_slide.render_slide()
    return


@app.cell
def _(mo, plotter, qr_optimal, sc):
    qr_optimal_slide = sc.create_slide("Optimized Policy Parameters Based on Historical Data", layout_type="2-row")


    q = qr_optimal.params.get("Q")
    r = qr_optimal.params.get("R")

    qr_optimal_slide.content1 = mo.md(f"""
    By tuning the simulation, we found that the best parameters are Q = {q} and R = {r}. This policy strikes a good balance between the different costs based on historical data.
    """)
    inventory_plot = plotter.plot(policy=qr_optimal)
    qr_optimal_slide.content2 = mo.ui.altair_chart(inventory_plot)
    return (qr_optimal_slide,)


@app.cell(hide_code=True)
def _(qr_optimal_slide):
    qr_optimal_slide.render_slide()
    return


@app.cell
def _(mo):
    order_cost = mo.ui.number(step=50, value=500, start=50, stop=1000, label="Order cost")
    holding_cost = mo.ui.number(step=1, value=3, start=1, stop=10, label="Holding cost")
    stockout_cost = mo.ui.number(step=1, value=5, start=1, stop=10, label="Stock‑out cost")
    lead_time = mo.ui.number(step=1, value=2, start=1, stop=5, label="Lead time")
    return holding_cost, lead_time, order_cost, stockout_cost


@app.cell
def _(
    InventoryConfig,
    QRPolicy,
    data,
    holding_cost,
    lead_time,
    mo,
    order_cost,
    plotter,
    sc,
    stockout_cost,
):
    slide_user_opt = sc.create_slide("Experiment with Cost Settings", layout_type="3-row")

    slide_user_opt.content1 = mo.vstack([
        mo.md("Let's try different combinations and see how changing the costs affects the optimal **Q** and **R**."),
        order_cost,
        holding_cost,
        stockout_cost,
        lead_time
    ])

    user_inv_cfg = InventoryConfig(
        order_cost=order_cost.value,
        holding_cost=holding_cost.value,
        stockout_cost=stockout_cost.value,
        lead_time=lead_time.value
    )

    user_policy = QRPolicy(config=user_inv_cfg)
    user_policy.fit(data["demand"], parallel=True)
    Q_user = user_policy.params["Q"]
    R_user = user_policy.params["R"]

    slide_user_opt.content2 = mo.md(
        f"**Optimized Q** = {Q_user}, **R** = {R_user}  \n"
        f"with Order Cost = {order_cost.value}, Holding Cost = {holding_cost.value}, "
        f"Stock-out Cost = {stockout_cost.value}, Lead Time = {lead_time.value}"
    )

    user_inventory_chart = plotter.plot(policy=user_policy)
    slide_user_opt.content3 = mo.ui.altair_chart(user_inventory_chart)
    return (slide_user_opt,)


@app.cell(hide_code=True)
def _(slide_user_opt):
    slide_user_opt.render_slide()
    return


@app.cell
def _(mo):
    answer_quiz_holding = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_holding,)


@app.cell
def _(answer_quiz_holding, mo, sc):

    quiz_holding_slide = sc.create_slide(
        "Quiz: Holding Cost Effect",
        layout_type="3-row"
    )

    quiz_holding_slide.content1 = mo.md(
        '''
    **If the holding cost is increased while keeping other costs constant, how is the optimal inventory policy likely to change?**

    <ol type="a">
    <li>Q will increase and R will decrease.</li>
    <li>Both Q and R will decrease.</li>
    <li>Both Q and R will increase.</li>
    <li>Both Q and R will stay the same.</li>
    </ol>
    '''
    )

    quiz_holding_slide.content2 = answer_quiz_holding

    feedback_holding = (
        "✅ Correct!"
        if answer_quiz_holding.value == "B"
        else "❌ Not quite. Try adjusting the holding cost and observing the effect."
    )
    quiz_holding_slide.content3 = mo.md(f"**Feedback:** {feedback_holding}" if answer_quiz_holding.value else "")
    return (quiz_holding_slide,)


@app.cell(hide_code=True)
def _(quiz_holding_slide):
    quiz_holding_slide.render_slide()
    return


@app.cell
def _(mo):
    answer_quiz_stockout = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_stockout,)


@app.cell
def _(answer_quiz_stockout, mo, sc):

    quiz_stockout_slide = sc.create_slide(
        "Quiz: Stock-out Cost Effect",
        layout_type="3-row"
    )

    quiz_stockout_slide.content1 = mo.md(
        '''
    **When stock-out cost is very high, what behavior should we expect from the optimized policy?**

    <ol type="a">
    <li>It will reduce both Q and R to avoid overstocking.</li>
    <li>It will set Q to zero, as safety stock is unnecessary.</li>
    <li>It will increase R to reduce the chance of stockouts.</li>
    <li>It will ignore the stock-out cost completely.</li>
    </ol>
    '''
    )

    quiz_stockout_slide.content2 = answer_quiz_stockout

    feedback_stockout = (
        "✅ Correct!"
        if answer_quiz_stockout.value == "C"
        else "❌ Nope. Think about how we balance the risk of running out."
    )
    quiz_stockout_slide.content3 = mo.md(f"**Feedback:** {feedback_stockout}" if answer_quiz_stockout.value else "")
    return (quiz_stockout_slide,)


@app.cell(hide_code=True)
def _(quiz_stockout_slide):
    quiz_stockout_slide.render_slide()
    return


@app.cell
def _(mo):
    answer_quiz_leadtime = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_quiz_leadtime,)


@app.cell
def _(answer_quiz_leadtime, mo, sc):

    quiz_leadtime_slide = sc.create_slide(
        "Quiz: Lead Time Effect",
        layout_type="3-row"
    )

    quiz_leadtime_slide.content1 = mo.md(
        '''
    **How does increasing the lead time (while keeping costs constant) affect the reorder point (R)?**

    <ol type="a">
    <li>R increases to account for longer wait time before replenishment.</li>
    <li>R decreases because we need less safety stock.</li>
    <li>R stays the same since demand isn’t changing.</li>
    <li>Q increases instead of R.</li>
    </ol>
    '''
    )

    quiz_leadtime_slide.content2 = answer_quiz_leadtime

    feedback_leadtime = (
        "✅ Correct!"
        if answer_quiz_leadtime.value == "A"
        else "❌ Try again. Consider the effect of delayed replenishment."
    )
    quiz_leadtime_slide.content3 = mo.md(f"**Feedback:** {feedback_leadtime}" if answer_quiz_leadtime.value else "")
    return (quiz_leadtime_slide,)


@app.cell(hide_code=True)
def _(quiz_leadtime_slide):
    quiz_leadtime_slide.render_slide()
    return


@app.cell
def _(sc):
    titleSlide2 = sc.create_slide(
        "Inventory Management – Forecast-Driven Inventory Management",
        layout_type="title-slide",
        newSection="Inventory Management – Forecast-Driven Inventory Management",
    )
    return (titleSlide2,)


@app.cell(hide_code=True)
def _(titleSlide2):
    titleSlide2.render_slide()
    return


@app.cell
def _(mo, sc):
    forecast_policy_slide = sc.create_slide(
        "Limitations of Simulation-Driven Policies",
        layout_type="1-column"
    )
    forecast_policy_slide.content1 = mo.md(
        """
        In the previous chapter, our inventory policies were **simulation-driven** —   
        they relied solely on historical demand data to determine order quantities and reorder points.

        **Disadvantages of this approach:**  
        - These policies are **backward-looking**: they optimize decisions based on past demand, not on what is likely to happen in the future.   
        - They may not adapt well to changes in demand patterns, seasonality, or trends.  
        - They do not leverage available information or forecasts about upcoming demand.   

        **To improve inventory management, we need to move to a forward-looking, forecast-driven policy** that uses demand forecasts to make better ordering decisions.
        """
    )
    return (forecast_policy_slide,)


@app.cell(hide_code=True)
def _(forecast_policy_slide):
    forecast_policy_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(SimpleForecastPlotter, data):

    forecast = data.copy()
    forecast["forecast"] = forecast["demand"].mean()
    forecast.drop(columns=["demand"], inplace=True)
    fc_plotter_forecast = SimpleForecastPlotter(history=data, forecast=forecast)
    return (fc_plotter_forecast,)


@app.cell
def _(fc_plotter_forecast, mo, sc):
    forecast_slide = sc.create_slide("Assuming a Demand Forecast", layout_type="2-row")
    plot_forecast = fc_plotter_forecast.plot(
        title="Forecasted Daily Demand of Amoxicillin (Fürth Region)",
        model_col="forecast"
    )

    forecast_slide.content1 = mo.md("""
    Remember from the demand planning part of the lecture that we have information about future demand in the form of a forecast.  
    Let us now assume we have a single exponential smoothing forecast for the daily demand of July 2025 to make inventory management decisions.  
    This forward-looking information allows us to improve upon simulation-driven policies that only rely on historical data.
    """)

    forecast_slide.content2 = mo.ui.altair_chart(plot_forecast)
    return (forecast_slide,)


@app.cell(hide_code=True)
def _(forecast_slide):
    forecast_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    eoq_motivation_slide = sc.create_slide(
        "From Forecast to Policy",
        layout_type="1-column"
    )
    eoq_motivation_slide.content1 = mo.md(
        """
        **Let us now assume that our forecast is correct** and that we know the true demand for the upcoming period.

        With this perfect information about future demand, we can move beyond simulation-based policies and derive an **analytical solution** for the optimal inventory policy.

        **Key insight:** When demand is known and constant, we can use mathematical optimization to find the exact order quantity that minimizes total costs.

        This leads us to the **Economic Order Quantity (EOQ) model** - one of the foundational models in inventory management.
        """
    )
    return (eoq_motivation_slide,)


@app.cell(hide_code=True)
def _(eoq_motivation_slide):
    eoq_motivation_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    eoq_intro_slide = sc.create_slide(
        "The Economic Order Quantity (EOQ) Model",
        layout_type="1-column"
    )
    eoq_intro_slide.content1 = mo.md(r"""
    The **EOQ model** is a classic inventory management approach that determines the optimal order quantity to minimize total inventory costs when **demand is constant and known**.

    - **Key Idea:**  
        - Balance the trade-off between:
            - **Ordering costs:** Fixed costs incurred each time an order is placed  
            - **Holding costs:** Costs of storing inventory over time  

    - **What makes EOQ special:**  
        - Provides an **analytical solution** (exact formula)  
        - Foundation for more complex inventory models  
        - Helps understand fundamental inventory trade-offs  


    - **Objective:**  
        - Find the order quantity that minimizes total annual costs.
    """)
    return (eoq_intro_slide,)


@app.cell(hide_code=True)
def _(eoq_intro_slide):
    eoq_intro_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    eoq_formula_slide1 = sc.create_slide(
        "EOQ Formula: Cost Function and Optimization",
        layout_type="1-column"
    )
    eoq_formula_slide1.content1 = mo.md(r"""
        Let's formalize the EOQ model:

        - **Optimization Problem:**  
          We want to minimize the total cost function \(C(Q)\) with respect to the order quantity \(Q\) (units per order).  
          The total **daily** cost is given by:

            \[
            C(Q) = \frac{d}{Q} K + \frac{Q}{2} h
            \]

          where:  
          - \(d\): Daily demand (units per day)  
          - \(K\): Fixed cost per order  
          - \(h\): Holding cost per unit per day  
          - \(Q\): Order quantity

        - **How to find the optimal order quantity \(Q^*\):**  
          Take the first derivative of \(C(Q)\) with respect to \(Q\), set it to zero, and solve for \(Q\).
    """)
    return (eoq_formula_slide1,)


@app.cell(hide_code=True)
def _(eoq_formula_slide1):
    eoq_formula_slide1.render_slide()
    return


@app.cell
def _(mo, sc):
    eoq_formula_slide2 = sc.create_slide(
        "EOQ Formula: Solution and Assumptions",
        layout_type="1-column"
    )
    eoq_formula_slide2.content1 = mo.md(r"""
        - **EOQ Formula:**  
            - The optimal order quantity is:

                \[
                Q^* = \sqrt{\frac{2 d K}{h}}
                \]

            - The reorder point with lead time is:

                \[
                R = d \cdot L
                \]

                where \(L\) is the lead time (in days).

        - **Key Assumptions:**  
            - Demand rate is known and constant  
            - No stockouts: all demand is met from inventory  

        - **Result:**  
            - The EOQ gives the order quantity that minimizes the sum of daily ordering and holding costs.
            - The reorder point ensures orders are placed early enough to avoid stockouts during lead time.
    """)
    return (eoq_formula_slide2,)


@app.cell(hide_code=True)
def _(eoq_formula_slide2):
    eoq_formula_slide2.render_slide()
    return


@app.cell
def _(mo, sc):
    uncertain_demand_slide = sc.create_slide(
        "Extending EOQ to Uncertain Demand",
        layout_type="1-column"
    )
    uncertain_demand_slide.content1 = mo.md(
        """
        **Reality Check:** In practice, demand is never perfectly known or constant!

        **The Problem:**   
        - Our forecast gives us an expected demand, but actual demand will vary around this forecast  
        - We need to account for demand uncertainty when setting the reorder point  
        - Too low reorder point → stockouts when demand is higher than expected  
        - Too high reorder point → excess inventory costs  

        **The Solution:**  
        - Keep the EOQ formula for order quantity: $Q^* = \sqrt{\\frac{2DK}{h}}$  
        - Modify the reorder point to include **safety stock** for demand uncertainty  

        This extension allows us to balance service level (avoiding stockouts) with inventory costs.
        """
    )
    return (uncertain_demand_slide,)


@app.cell(hide_code=True)
def _(uncertain_demand_slide):
    uncertain_demand_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    alpha_service_slide = sc.create_slide(
        "Understanding Alpha Service Level",
        layout_type="1-column"
    )
    alpha_service_slide.content1 = mo.md(r"""
        **What is Alpha Service Level?**

        The **alpha service level** $(\alpha)$ measures the probability of **not experiencing a stockout** during a replenishment cycle.

        - **Definition:** $\alpha = P(\text{no stockout during lead time})$
        - **Interpretation:** If $\alpha = 0.95$, we expect to avoid stockouts 95% of the time
        - Simply speaking with $\alpha=0.95$, we will be able to fullfill all of our demand on 95 out of 100 days.

        **Key Properties:**  
        -  $\alpha$ is a **period-based** measure (focuses on cycles, not individual units)
        - Higher  $\alpha$ requires more safety stock but reduces stockout frequency

        **Optimal Service Level - Critical Ratio:**  

        The optimal service level can be determined using the **critical ratio** formula, which balances holding costs against stockout costs:

        $$\alpha = \frac{p}{h + p}$$

        **Intuition:**
        - When stockout costs are high relative to holding costs, optimal service level approaches 1
        - When holding costs are high relative to stockout costs, optimal service level is lower   
        - This formula provides the cost-optimal balance between service and inventory investment

    """)
    return (alpha_service_slide,)


@app.cell(hide_code=True)
def _(alpha_service_slide):
    alpha_service_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    ss_slide1 = sc.create_slide(
        "Reorder Point and Its Components",
        layout_type="1-column"
    )
    ss_slide1.content1 = mo.md(r"""
        - **Reorder Point Formula:**  
            - The reorder point is:

                \[
                R = L \cdot D + SS
                \]

                where:  
                - \(L\) = lead time (days until an order arrives)  
                - \(D\) = expected demand per day  
                - \(SS\) = safety stock (extra inventory to protect against variability)  

        - **Interpretation:**  
            - \(L \cdot D\) covers expected demand during lead time.  
            - Safety stock (\(SS\)) protects against demand variability and forecast errors.  

        - **Next:**  
            - We will derive how to compute \(SS\) from a desired service level.
    """)
    return (ss_slide1,)


@app.cell(hide_code=True)
def _(ss_slide1):
    ss_slide1.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide 2a: Service level and normal demand distribution
    ss_slide2a = sc.create_slide(
        "Service Level and Demand Distribution",
        layout_type="1-column"
    )
    ss_slide2a.content1 = mo.md(r"""
        - **Goal:**  
            - Set safety stock so that the probability of a stockout during lead time is at most \(1 - \alpha\), i.e., we achieve a target service level \(\alpha = P(\text{no stockout during lead time})\).

        - **Assumptions:**  
            - Let \(D_L\) be the total demand during lead time \(L\).  
            - Assume \(D_L\) is normally distributed: \(D_L \sim \mathcal{N}(L D, \sigma_{D_L}^2)\),  
              where \(D\) is average daily demand and \(\sigma_{D_L}\) is the standard deviation of demand during lead time.

        - **How to set the reorder point:**  
            - To achieve service level \(\alpha\), set the reorder point so that inventory covers expected demand plus a buffer for uncertainty:

                \[
                R = \mathbb{E}[D_L] + z_\alpha \cdot \sigma_{D_L}
                \]

                where \(z_\alpha\) is the z-score such that the probability of not exceeding \(R\) is \(\alpha\).
    """)
    return (ss_slide2a,)


@app.cell(hide_code=True)
def _(ss_slide2a):
    ss_slide2a.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide 2b: Safety stock formula and interpretation
    ss_slide2b = sc.create_slide(
        "Safety Stock Formula and Interpretation",
        layout_type="1-column"
    )
    ss_slide2b.content1 = mo.md(r"""
        - **Safety stock formula:**  
            - The extra inventory above expected demand is called safety stock:

                \[
                SS = z_\alpha \cdot \sigma_{D_L}
                \]

        - **Relating to daily demand variability:**  
            - If daily demand has standard deviation \(\sigma_D\), then demand during lead time has:

                \[
                \sigma_{D_L} = \sigma_D \sqrt{L}
                \]

            - So, safety stock becomes:

                \[
                SS = z_\alpha \cdot \sigma_D \sqrt{L}
                \]

        - **Key takeaways:**  
            - Higher demand variability (\(\sigma_D\)) or longer lead time (\(L\)) both increase safety stock.  
            - Higher service level (\(\alpha\)) requires a larger \(z_\alpha\), and thus more safety stock.
    """)
    return (ss_slide2b,)


@app.cell(hide_code=True)
def _(ss_slide2b):
    ss_slide2b.render_slide()
    return


@app.cell
def _(mo):
    # UI controls for safety stock visualization
    alpha_slider = mo.ui.slider(0.5, 0.99, value=0.95, step=0.01, label="Service level (α)")
    lead_time_num = mo.ui.number(step=1, value=2, start=1, stop=14, label="Lead time (days)")
    return alpha_slider, lead_time_num


@app.cell
def _(SafetyStockPlotter, alpha_slider, data, lead_time_num, mo, sc):
    """
    Interactive slide that uses SafetyStockPlotter (if available) to visualize safety stock
    as a function of service level and lead time. Falls back to a numeric estimate if
    the plotter cannot produce a chart.
    """
    import math
    from scipy.stats import norm

    # Estimate MAE from historical demand as a default accuracy metric
    mae = float(abs(data["demand"] - data["demand"].mean()).mean())

    # Compute z-score for selected alpha
    z_alpha = float(norm.ppf(alpha_slider.value))

    # Practical heuristic from slides: use 1.25 * MAE to approximate sigma_D
    ss_estimate = z_alpha * 1.25 * mae * math.sqrt(lead_time_num.value)

    # Try to produce a chart with SafetyStockPlotter if available
    chart_component = None
    ss_plotter = SafetyStockPlotter(history=data)
    chart = ss_plotter.plot(alpha=alpha_slider.value, lead_time=lead_time_num.value, mean_daily=data["demand"].mean(), std_daily= 1.25* mae)
    chart_component = mo.ui.altair_chart(chart)

    ss_vis_slide = sc.create_slide(
        "Lead Time Uncertainty & Safety Stock Visualization",
        layout_type="2-row"
    )

    ss_vis_slide.content1 = mo.vstack(
        [
            mo.md(
                f"""
                Use the controls to explore how the safety stock changes with service level and lead time.

                - Estimated MAE: **{mae:.2f}**
                - Z-score for α={alpha_slider.value:.2f}: **{z_alpha:.2f}**
                - Safety stock: **{ss_estimate:.1f} units**
                """
            ),
            alpha_slider,
            lead_time_num,
        ]
    )

    if chart_component:
        ss_vis_slide.content2 = chart_component
    else:
        # Fallback: show numeric estimate if no chart is produced
        ss_vis_slide.content2 = mo.md(
            f"Safety Stock: **{ss_estimate:.1f} units**  \n"
            f"(zₐ={z_alpha:.2f}, MAE={mae:.2f}, L={lead_time_num.value})"
        )
    return (ss_vis_slide,)


@app.cell(hide_code=True)
def _(ss_vis_slide):
    ss_vis_slide.render_slide()
    return


@app.cell
def _(mo, sc):
    # Slide 3: Lead time uncertainty and forecast error (MAE)
    ss_slide3 = sc.create_slide(
        "Lead Time Uncertainty & Forecast Error — Practical SS",
        layout_type="1-column"
    )
    ss_slide3.content1 = mo.md(r"""
        - **Estimating Variability from Forecast Error:**  
            - Approximate standard deviation from MAE using a common heuristic (\(1.25 \times \text{MAE}\)):

                \[
                SS \approx z_\alpha \cdot 1.25 \cdot \text{MAE} \cdot \sqrt{L}
                \]

            - Where:
                - \(SS\) = safety stock
                - \(z_\alpha\) = z-score for desired service level \(\alpha\)
                - \(\text{MAE}\) = mean absolute error of the forecast
                - \(L\) = lead time (in days)

        - **Summary of Relationships:**  
            - Higher service level \(\alpha\) → higher \(z_\alpha\) → more SS  
            - Worse forecast accuracy (higher MAE) → more SS  
            - Longer or more uncertain lead times → larger SS (through \(\sqrt{L}\) or added lead time variability)

        - **Usage:**  
            - Use this formula to tune safety stock given a desired service level, forecast error estimate, and lead time.
    """)
    return (ss_slide3,)


@app.cell(hide_code=True)
def _(ss_slide3):
    ss_slide3.render_slide()
    return


@app.cell(hide_code=True)
def _(data, mo):
    forecast_order_cost = mo.ui.number(step=50, value=500, start=50, stop=1000, label="Order cost")
    forecast_holding_cost = mo.ui.number(step=1, value=3, start=1, stop=10, label="Holding cost")
    forecast_stockout_cost = mo.ui.number(step=1, value=5, start=1, stop=10, label="Stock‑out cost")
    forecast_lead_time = mo.ui.number(step=1, value=2, start=1, stop=5, label="Lead time")
    forecast_mean = data["demand"].mean()
    forecast_mae = abs(data["demand"] - data["demand"].mean()).mean()
    return (
        forecast_holding_cost,
        forecast_lead_time,
        forecast_mae,
        forecast_mean,
        forecast_order_cost,
        forecast_stockout_cost,
    )


@app.cell
def _(
    InventoryConfig,
    QRForecasting,
    data,
    forecast_holding_cost,
    forecast_lead_time,
    forecast_mae,
    forecast_mean,
    forecast_order_cost,
    forecast_stockout_cost,
    mo,
    plotter,
    sc,
):
    slide_forecast_opt = sc.create_slide("Experiment with Forecast-Driven Policy", layout_type="3-row")

    slide_forecast_opt.content1 = mo.vstack([
        mo.md("Now let's experiment with the **forecast-driven (Q,R) policy** and see how changing the costs affects the optimal **Q** and **R**."),
        forecast_order_cost,
        forecast_holding_cost,
        forecast_stockout_cost,
        forecast_lead_time
    ])

    forecast_inv_cfg = InventoryConfig(
        order_cost=forecast_order_cost.value,
        holding_cost=forecast_holding_cost.value,
        stockout_cost=forecast_stockout_cost.value,
        lead_time=forecast_lead_time.value
    )

    forecast_policy = QRForecasting(config=forecast_inv_cfg)
    forecast_policy.fit(forecast_mean, forecast_mae, data)
    Q_forecast = forecast_policy.params["Q"]
    R_forecast = forecast_policy.params["R"]

    slide_forecast_opt.content2 = mo.md(
        f"**Forecast-driven Q** = {Q_forecast}, **R** = {R_forecast}  \n"
        f"with Order Cost = {forecast_order_cost.value}, Holding Cost = {forecast_holding_cost.value}, "
        f"Stock-out Cost = {forecast_stockout_cost.value}, Lead Time = {forecast_lead_time.value}"
    )

    forecast_inventory_chart = plotter.plot(policy=forecast_policy)
    slide_forecast_opt.content3 = mo.ui.altair_chart(forecast_inventory_chart)
    return (slide_forecast_opt,)


@app.cell(hide_code=True)
def _(slide_forecast_opt):
    slide_forecast_opt.render_slide()
    return


@app.cell(hide_code=True)
def _(mo):
    answer_summary_1 = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_summary_1,)


@app.cell
def _(answer_summary_1, mo, sc):
    summary_q1_slide = sc.create_slide(
        "Summary Question 1: Alpha Service Level",
        layout_type="3-row"
    )

    summary_q1_slide.content1 = mo.md(
        '''
    **What does the alpha-type service level (α) represent in inventory management?**

    <ol type="a">
    <li>The probability of not experiencing a stockout during the lead time.</li>
    <li>The average number of units ordered per cycle.</li>
    <li>The total inventory cost per period.</li>
    <li>The percentage of demand fulfilled immediately from stock.</li>
    </ol>
    '''
    )

    summary_q1_slide.content2 = answer_summary_1

    feedback_summary_1 = (
        "✅ Correct! Alpha-type service level is the probability of no stockout during lead time."
        if answer_summary_1.value == "A"
        else "❌ Not quite. Review the definition of alpha-type service level."
    )
    summary_q1_slide.content3 = mo.md(f"**Feedback:** {feedback_summary_1}" if answer_summary_1.value else "")
    return (summary_q1_slide,)


@app.cell(hide_code=True)
def _(summary_q1_slide):
    summary_q1_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(mo):
    answer_summary_2 = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_summary_2,)


@app.cell
def _(answer_summary_2, mo, sc):
    summary_q2_slide = sc.create_slide(
        "Summary Question 2: Simulation vs. Forecast-Driven Policies",
        layout_type="3-row"
    )

    summary_q2_slide.content1 = mo.md(
        '''
    **What is the main advantage of forecast-driven inventory policies compared to simulation-driven policies?**

    <ol type="a">
    <li>They are always more accurate because they use mathematical formulas.</li>
    <li>They are forward-looking and can adapt to expected changes in demand patterns.</li>
    <li>They do not require any historical data to make decisions.</li>
    <li>They completely eliminate the need for safety stock.</li>
    </ol>
    '''
    )

    summary_q2_slide.content2 = answer_summary_2

    feedback_summary_2 = (
        "✅ Correct! Forecast-driven policies use forward-looking information to make better decisions about future demand."
        if answer_summary_2.value == "B"
        else "❌ Consider what information each approach uses to make decisions."
    )
    summary_q2_slide.content3 = mo.md(f"**Feedback:** {feedback_summary_2}" if answer_summary_2.value else "")
    return (summary_q2_slide,)


@app.cell(hide_code=True)
def _(summary_q2_slide):
    summary_q2_slide.render_slide()
    return


@app.cell(hide_code=True)
def _(mo):
    answer_summary_3 = mo.ui.dropdown(
        options=["A", "B", "C", "D"],
        label="Your answer"
    )
    return (answer_summary_3,)


@app.cell
def _(answer_summary_3, mo, sc):
    summary_q3_slide = sc.create_slide(
        "Summary Question 3: EOQ and Safety Stock",
        layout_type="3-row"
    )

    summary_q3_slide.content1 = mo.md(
        '''
    **In the EOQ model with uncertain demand, which statement is correct about the relationship between order quantity (Q) and reorder point (R)?**

    <ol type="a">
    <li>Both Q and R are determined solely by the forecast accuracy (MAE).</li>
    <li>Q should always equal R for optimal performance.</li>
    <li>Q is determined by balancing ordering and holding costs, while R includes safety stock to handle demand uncertainty.</li>
    <li>R is always set to zero in the EOQ model to minimize costs.</li>
    </ol>
    '''
    )

    summary_q3_slide.content2 = answer_summary_3

    feedback_summary_3 = (
        "✅ Correct! Q optimizes the ordering/holding cost trade-off, while R addresses demand uncertainty through safety stock."
        if answer_summary_3.value == "C"
        else "❌ Think about what each parameter optimizes for in the EOQ framework."
    )
    summary_q3_slide.content3 = mo.md(f"**Feedback:** {feedback_summary_3}" if answer_summary_3.value else "")
    return (summary_q3_slide,)


@app.cell(hide_code=True)
def _(summary_q3_slide):
    summary_q3_slide.render_slide()
    return


if __name__ == "__main__":
    app.run()
