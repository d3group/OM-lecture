import marimo

__generated_with = "0.18.0"
app = marimo.App(
    width="medium",
    app_title="Supply Planning and Purchasing",
    layout_file="layouts/supply_planning.slides.json",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    GH_USER = "d3group"
    GH_REPO = "OM-lecture"
    BRANCH = "purchasing"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    class DataURLs:
        BASE = raw_url("apps", "public", "data", "supply_planning")
        QR_PARAMS = f"{BASE}/qr_policy_parameters.csv"
        # Use local path for the generated file
        SUPPLY_PLAN = "apps/public/data/supply_planning/supply_plan_simulation_v2.csv"



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
    return DataURLs, UtilsURLs


@app.cell(hide_code=True)
async def _(UtilsURLs):
    import micropip
    import urllib.request
    import os
    import sys
    import subprocess

    # Avoid pandas importing a mismatched numexpr binary on some systems
    os.environ.setdefault("PANDAS_USE_NUMEXPR", "0")

    class UtilsManager:
        def __init__(self, dest_folder="utils", files_map=None, packages=None):
            self.dest_folder = dest_folder
            self.files_map = files_map or {}
            self.files = list(self.files_map.keys())
            self.packages = packages or []
            self.packages_installed = False
            self.files_downloaded = False

        async def install_packages(self):
            """Install required packages in both wasm and local Python runtimes."""
            # Prefer micropip only when running in Pyodide; otherwise fall back to pip
            use_micropip = sys.platform == "emscripten"
            missing = []
            for pkg in self.packages:
                try:
                    __import__(pkg)
                    print(f"✅ Package {pkg} is already installed.")
                except Exception as exc:
                    # Catch broader exceptions (e.g., binary mismatches) and reinstall
                    print(f"⚠️ Import for {pkg} failed ({exc}). Will attempt to install.")
                    missing.append(pkg)

            if not missing:
                print("✅ All packages installed.")
                self.packages_installed = True
                return

            if use_micropip:
                for pkg in missing:
                    print(f"Installing {pkg} with micropip...")
                    await micropip.install(pkg)
            else:
                # Pin numpy to <2 to avoid binary mismatches with many precompiled wheels
                pin_overrides = {
                    "numpy": "numpy<2",
                    "numexpr": "numexpr>=2.10",
                }
                specs = [pin_overrides.get(pkg, pkg) for pkg in missing]
                print(f"Installing {', '.join(specs)} with pip...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", *specs],
                    check=True,
                )
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
    from utils.slides import SlideCreator
    from utils.data import DataLoader
    from utils.inventory import SimpleForecastPlotter, SafetyStockPlotter
    from utils.mrp import MRPLogic
    from sklearn.utils import Bunch
    import marimo as mo
    return SlideCreator, mo


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
    presenter = "Richard Pibernik, Moritz Beck, Anh-Duy Pham"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return (sc,)


@app.cell
def _(sc):
    titleSlide = sc.create_slide(
        "Supply Planning: From Inventory Planning to Purchase Requisitions (MRP)",
        layout_type="title-slide",
        newSection="Supply Planning: From Inventory Planning to Purchase Requisitions (MRP)",
    )
    return (titleSlide,)


@app.cell(hide_code=True)
def _(titleSlide):
    titleSlide.render_slide()
    return


@app.cell
def _(mo, sc):
    basic_supply_mng = sc.create_slide("Step 1: From Inventory Planning in one DC to Gross Requirements for Phoenix", layout_type="1-column", newSection=" ")
    basic_supply_mng.content1 = mo.md(
        """
        - In Chapter 3 you learned how Phoenix’s DC in Fürth plans its inventory using a **(Q, R) policy**. The same planning logic runs in all other **16 Phoenix DCs**.
        - By knowing each DC’s (Q, R) parameters, and forecasted daily demand, we can **anticipate how much each DC will order** from the central warehouse. We now want to aggregate these demands to know how much of the product we have to ship from our central warehouse to the DCs. 
        - We typically look ahead over a horizon greater than the supplier lead time (e.g., the lead time of Ratiopharm for Amoxicillin 500). Let’s assume that the supplier lead time is rather short (3 days) and that we look at the next two weeks (10 days).

    **Gross requirements over the horizon:**

    \[
    GR_t = \sum_{i=1}^{17} Q_{i,t} \quad   t = 1,\ldots,10  
    \]

    where $Q_{i,t}$ is the planned order of $DC_i$ on day $t$

    """
    )
    return (basic_supply_mng,)


@app.cell(hide_code=True)
def _(basic_supply_mng):
    basic_supply_mng.render_slide()
    return


@app.cell
def _(DataURLs, mo, sc):
    basic_supply_mng2 = sc.create_slide("Step 1: From Inventory Planning in one DC to Gross Requirements for Phoenix", layout_type="1-column")

    import pandas as pd 
    import math
    import altair as alt

    df_supply = pd.read_csv(DataURLs.SUPPLY_PLAN)

    # Individual Data (Pivoted for better view)
    df_pivot = df_supply.pivot(index="Date", columns="DC", values="Order_Placed_Qty").fillna(0)

    # Sort columns naturally (DC1, DC2, ..., DC10, ...)
    sorted_cols = sorted(df_pivot.columns, key=lambda x: int(x.replace("DC", "")))
    df_pivot = df_pivot[sorted_cols].reset_index()

    individual_table = mo.ui.table(
        df_pivot,
        label="Individual DC Orders",
        selection=None
    )

    # Aggregate Data
    aggregate_df = df_supply.groupby("Date")["Order_Placed_Qty"].sum().reset_index()
    aggregate_table = mo.ui.table(
        aggregate_df,
        label="Then we aggregate the order quantities of the 16 DCs to get the total GR at the central warebouse.",
        selection=None
    )

    # Stack them vertically as the matrix is wide
    basic_supply_mng2.content1 = mo.vstack([individual_table, aggregate_table])
    return alt, basic_supply_mng2, df_supply, math, pd


@app.cell(hide_code=True)
def _(basic_supply_mng2):
    basic_supply_mng2.render_slide()
    return


@app.cell
def _(alt, df_supply, mo, sc):
    step1_slide = sc.create_slide("Step 1: From Inventory Planning in one DC to Gross Requirements for Phoenix", layout_type="2-row")

    step1_slide.content1 = mo.md(
        r"""
        **Gross Requirements ($GR_t$)** represent the total demand for an item in each period.

        In our case, this is the aggregated order quantity from all distribution centers.

        $$GR_t = \sum_{i=1}^{17} Q_{i,t}$$

        The chart below shows demand patterns over time, with peak periods highlighted.
        """
    )

    gross_req = df_supply.groupby("Date")["Order_Placed_Qty"].sum().sort_index().head(10)

    # Create a beautiful bar chart
    chart_data_s1 = gross_req.reset_index()
    chart_data_s1.columns = ["Date", "Demand"]

    # Calculate peak demand for highlighting
    max_demand = chart_data_s1["Demand"].max()
    chart_data_s1["Is_Peak"] = chart_data_s1["Demand"] >= max_demand * 0.8

    bar_chart_s1 = (
        alt.Chart(chart_data_s1)
        .mark_bar()
        .encode(
            x=alt.X("Date:T", title="Date", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("Demand:Q", title="Gross Requirements (Units)"),
            color=alt.condition(
                alt.datum.Is_Peak,
                alt.value("#e74c3c"),  # Red for peak
                alt.value("#3498db")   # Blue for normal
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("Demand:Q", title="Demand", format=",")
            ]
        )
        .properties(
            title="Demand Over Time (Peak Periods in Red)",
            width=600,
            height=300
        )
    )

    # Add text labels on bars
    text_s1 = (
        alt.Chart(chart_data_s1)
        .mark_text(dy=-5, fontSize=10)
        .encode(
            x=alt.X("Date:T"),
            y=alt.Y("Demand:Q"),
            text=alt.Text("Demand:Q", format=",")
        )
    )

    combined_chart_s1 = (bar_chart_s1 + text_s1).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    step1_slide.content2 = mo.ui.altair_chart(combined_chart_s1)
    return (step1_slide,)


@app.cell(hide_code=True)
def _(step1_slide):
    step1_slide.render_slide()
    return


@app.cell
def _(alt, df_supply, mo, pd, sc):
    step2_slide = sc.create_slide("Step 2: Inventory Netting (Projected On-Hand Inventory)", layout_type="2-row")

    step2_slide.content1 = mo.md(
        r"""
        Today (at time **t = 1**) we have inventory in our central warehouse.
        This is the **on-hand inventory**, denoted
        $$I_0^{central}$$

        We also have **purchase orders to suppliers** that were placed in earlier days.
        These orders will **arrive in future periods** (e.g., at $t+1, t+2, ...$).
        We call these **planned receipts**:
        $$PR_t$$

        Using the **gross requirements** from Step 1 (the DC demand), and the **planned receipts**,

        we can compute the **projected on-hand inventory** for each future period.

        The projection follows the standard MRP netting equation:
        $$I_t^{central} = I_{t-1}^{central} + PR_t - GR_t \quad \text{for } t = 1, ..., 20$$
        """
    )

    # Visualization of depleting inventory with enhanced styling
    dates_s2 = df_supply["Date"].unique()
    dates_s2.sort()
    dates_s2 = dates_s2[:20]  # Show 20 days as per formula

    gross_req_s2 = df_supply.groupby("Date")["Order_Placed_Qty"].sum().reindex(dates_s2, fill_value=0)

    # Planned receipts from supplier (orders placed in earlier periods that arrive now)
    # For this example, assume some receipts arrive on specific days
    planned_receipts_s2 = pd.Series(0, index=dates_s2)
    # Example: receipts arriving on days 5, 10, 15
    if len(dates_s2) > 5:
        planned_receipts_s2.iloc[5] = 2000
    if len(dates_s2) > 10:
        planned_receipts_s2.iloc[10] = 2000
    if len(dates_s2) > 14:
        planned_receipts_s2.iloc[14] = 2000

    initial_inv_s2 = 5000
    safety_stock_s2 = 200

    inv_levels_s2 = []
    current_inv_s2 = initial_inv_s2
    for date_s2 in dates_s2:
        demand_s2 = gross_req_s2.get(date_s2, 0)
        receipt_s2 = planned_receipts_s2.get(date_s2, 0)
        # Apply the MRP netting equation: I_t = I_{t-1} + PR_t - GR_t
        current_inv_s2 = current_inv_s2 + receipt_s2 - demand_s2
        inv_levels_s2.append({
            "Date": date_s2, 
            "Inventory": current_inv_s2,
            "Safety_Stock": safety_stock_s2,
            "Danger_Zone": safety_stock_s2 if current_inv_s2 < safety_stock_s2 else 0
        })

    inv_df_s2 = pd.DataFrame(inv_levels_s2)

    # Create layered chart with improved aesthetics
    base_s2 = alt.Chart(inv_df_s2).encode(x=alt.X("Date:T", title="Date"))

    # Zero baseline (dashed black line)
    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="black", 
        strokeDash=[5, 5],
        size=2,
        opacity=0.8
    ).encode(y=alt.Y("y:Q", scale=alt.Scale(zero=True)))

    # Safety stock reference line (removed to keep only zero line)
    # safety_line_s2 = alt.Chart(pd.DataFrame({"y": [safety_stock_s2]})).mark_rule(
    #     strokeDash=[5, 5],
    #     color="orange",
    #     size=2
    # ).encode(y="y:Q")

    # Area fills
    # Green area for positive inventory (Safe)
    area_safe = base_s2.transform_filter(
        alt.datum.Inventory > 0
    ).mark_area(opacity=0.2, color="#27ae60").encode(
        y=alt.Y("Inventory:Q", title="Inventory Level"),
        y2=alt.value(0)
    )

    # Red area for negative inventory (Shortage)
    area_danger = base_s2.transform_filter(
        alt.datum.Inventory < 0
    ).mark_area(opacity=0.2, color="#e74c3c").encode(
        y=alt.Y("Inventory:Q"),
        y2=alt.value(0)
    )

    # Continuous line (Gray)
    line_s2 = base_s2.mark_line(
        color="gray", 
        size=2,
        opacity=0.8
    ).encode(
        y=alt.Y("Inventory:Q")
    )

    # Colored points to indicate status
    points_s2 = base_s2.mark_circle(size=60, opacity=1).encode(
        y=alt.Y("Inventory:Q"),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(domain=["Safe", "Danger"], range=["#27ae60", "#e74c3c"]),
            legend=alt.Legend(title="Inventory Status")
        ),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Inventory:Q", title="Inventory", format=","),
            alt.Tooltip("Safety_Stock:Q", title="Safety Stock", format=","),
            alt.Tooltip("Status:N", title="Status")
        ]
    )

    # Combine all layers
    chart_s2 = (area_safe + area_danger + zero_line + line_s2 + points_s2).properties(
        title="Inventory Depletion (Green = On Hand, Red = Shortage)",
        width=600,
        height=300
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    ).configure_axisY(
        domain=True,
        domainWidth=1
    )

    step2_slide.content2 = mo.ui.altair_chart(chart_s2)
    return (step2_slide,)


@app.cell(hide_code=True)
def _(step2_slide):
    step2_slide.render_slide()
    return


@app.cell
def _(alt, df_supply, mo, pd, sc):
    step3_slide = sc.create_slide("Step 3: Net Requirements", layout_type="2-row")

    step3_slide.content1 = mo.md(
        r"""
        After computing the projected on-hand inventory $I_t^{central}$, we check whether inventory will **fall below the central warehouse's safety stock level**.

        Let $SS^{central}$ be the safety stock of the central warehouse.

        The safety stock calculation is the same as in inventory planning for the individual DCs.

        If projected inventory stays **above** this level, no replenishment is required.

        If projected inventory falls **below** the safety stock, a **net requirement** is created in that period.

        **Net Requirements Formula:**
        $$NR_t = \max(0, SS^{central} - I_t^{central}) \quad \text{for } t = 1, ..., 20$$
        """
    )

    # Enhanced visualization of shortages
    dates_s3 = df_supply["Date"].unique()
    dates_s3.sort()
    dates_s3 = dates_s3[:20]  # Show 20 days as per formula
    gross_req_s3 = df_supply.groupby("Date")["Order_Placed_Qty"].sum().reindex(dates_s3, fill_value=0)

    # Planned receipts (same as Step 2)
    planned_receipts_s3 = pd.Series(0, index=dates_s3)
    if len(dates_s3) > 5:
        planned_receipts_s3.iloc[5] = 2000
    if len(dates_s3) > 10:
        planned_receipts_s3.iloc[10] = 2000
    if len(dates_s3) > 14:
        planned_receipts_s3.iloc[14] = 2000

    initial_inv_s3 = 5000
    safety_stock_s3 = 200

    inv_levels_s3 = []
    current_inv_s3 = initial_inv_s3
    for date_s3 in dates_s3:
        demand_s3 = gross_req_s3.get(date_s3, 0)
        receipt_s3 = planned_receipts_s3.get(date_s3, 0)
        available_s3 = current_inv_s3 + receipt_s3
        projected_after_demand = available_s3 - demand_s3
        # If projected inventory falls below safety stock, plan a receipt (L4L) to lift it back
        net_req_s3 = max(0, safety_stock_s3 - projected_after_demand)
        planned_receipt_s3 = net_req_s3
        projected_on_hand = projected_after_demand + planned_receipt_s3
        inv_levels_s3.append({
            "Date": date_s3, 
            "Gross_Requirements": demand_s3,
            "Scheduled_Receipts": receipt_s3,
            "Inventory": projected_on_hand,
            "Net_Requirements": net_req_s3,
            "Has_Shortage": net_req_s3 > 0
        })
        current_inv_s3 = projected_on_hand

    inv_df_s3 = pd.DataFrame(inv_levels_s3)

    base_s3 = alt.Chart(inv_df_s3).encode(x=alt.X("Date:T", title="Date"))

    # Inventory line
    line_s3 = base_s3.mark_line(point=True, size=3, color="#3498db").encode(
        y=alt.Y("Inventory:Q", title="Inventory Level"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Inventory:Q", title="Inventory", format=","),
            alt.Tooltip("Net_Requirements:Q", title="Net Requirements", format=",")
        ]
    )

    # Shortage bars (prominent)
    shortage_bars_s3 = base_s3.mark_bar(opacity=0.7, color="#e74c3c", size=20).encode(
        y=alt.Y("Net_Requirements:Q"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Net_Requirements:Q", title="Shortage Amount", format=",")
        ]
    )

    # Zero baseline (dashed black line)
    zero_line_s3 = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="black",
        strokeDash=[5, 5],
        size=2,
        opacity=0.8
    ).encode(y=alt.Y("y:Q", scale=alt.Scale(zero=True)))

    # Safety stock reference
    safety_line_s3 = alt.Chart(pd.DataFrame({"y": [safety_stock_s3]})).mark_rule(
        strokeDash=[5, 5],
        color="orange",
        size=2
    ).encode(y="y:Q")

    # Shortage area highlighting
    shortage_area_s3 = base_s3.transform_filter(
        alt.datum.Has_Shortage
    ).mark_area(opacity=0.2, color="#e74c3c").encode(
        y=alt.Y("Inventory:Q"),
        y2=alt.value(0)
    )

    chart_s3 = (shortage_area_s3 + zero_line_s3 + safety_line_s3 + line_s3 + shortage_bars_s3).properties(
        title="Net Requirements: Shortage Periods Highlighted",
        width=600,
        height=300
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    step3_slide.content2 = mo.ui.altair_chart(chart_s3)
    return inv_df_s3, step3_slide


@app.cell(hide_code=True)
def _(step3_slide):
    step3_slide.render_slide()
    return


@app.cell
def _(mo):
    eoq_slider = mo.ui.slider(start=0, stop=5000, value=1500, step=50, label="EOQ (central)")
    moq_slider = mo.ui.slider(start=0, stop=5000, value=1000, step=50, label="MOQ")
    mult_slider = mo.ui.slider(start=1, stop=1000, value=100, step=10, label="Order Multiple (m)")
    return eoq_slider, moq_slider, mult_slider


@app.cell
def _(mo):
    # Step 2 controls for the overview
    step2_initial_inv = mo.ui.slider(start=0, stop=10000, value=5000, step=100, label="Step 2 Initial Inventory")
    step2_safety_stock = mo.ui.slider(start=0, stop=2000, value=200, step=20, label="Step 2 Safety Stock")
    step2_receipt_qty = mo.ui.slider(start=0, stop=4000, value=2000, step=100, label="Step 2 Planned Receipt Qty")
    return step2_initial_inv, step2_receipt_qty, step2_safety_stock


@app.cell
def _(alt, eoq_slider, inv_df_s3, math, mo, moq_slider, mult_slider, pd, sc):
    step4_slide = sc.create_slide("Step 4: Planned Order Receipts (Lot Sizing)", layout_type="2-row")

    step4_slide.content1 = mo.vstack([
        mo.md(
            r"""
            When a net requirement occurs in period $t$, the central warehouse must create a Planned Order Receipt, denoted $POR_t$.

            We use a fixed-lot rule based on: the central EOQ, $EOQ^{central}$, the Minimum Order Quantity, $MOQ$, and the order multiple, $m$ (for example: orders must be in multiples of 100 packs)

            The rule is:

            If $NR_t > 0$:
            $$POR_t = \left\lceil \frac{\max(NR_t, EOQ^{central}, MOQ)}{m} \right\rceil \cdot m$$

            If $NR_t = 0$:
            $$POR_t = 0$$
            """
        ),
        eoq_slider,
        moq_slider,
        mult_slider
    ])

    # Use realistic example data (based on typical MRP scenarios)
    # Simulating what would happen with actual gross requirements and inventory depletion

    # Example: Initial inventory = 5000, Safety stock = 200
    # Gross requirements vary, causing inventory to drop below safety stock at certain periods
    # This creates Net Requirements that the fixed-lot rule must satisfy

    # Apply fixed-lot rule parameters
    eoq_central = eoq_slider.value
    moq = moq_slider.value
    m = max(1, mult_slider.value)

    # Use the net requirements calculated in Step 3
    net_requirements_list = [int(x) for x in inv_df_s3["Net_Requirements"].tolist()]

    # Apply fixed-lot rule to each Net Requirement
    planned_receipts_list = []
    for net_req_value in net_requirements_list:
        if net_req_value > 0:
            base_qty_s4 = max(eoq_central, moq, net_req_value)
            por_s4 = int(math.ceil(base_qty_s4 / m)) * m
        else:
            por_s4 = 0
        planned_receipts_list.append(por_s4)

    df_s4 = pd.DataFrame({
        "Period": list(range(1, len(net_requirements_list) + 1)),
        "Net Requirements": net_requirements_list,
        "Planned Order Receipts": planned_receipts_list
    })

    # Melt for grouped bar chart
    melted_s4 = df_s4.melt(
        id_vars=["Period"],
        value_vars=["Net Requirements", "Planned Order Receipts"],
        var_name="Type",
        value_name="Quantity"
    )

    # Create grouped bar chart
    bars_s4 = alt.Chart(melted_s4).mark_bar(opacity=0.8).encode(
        x=alt.X("Period:O", title="Period"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(domain=["Net Requirements", "Planned Order Receipts"], range=["#e74c3c", "#27ae60"]),
            legend=alt.Legend(title="Type")
        ),
        xOffset="Type:N",
        tooltip=[
            alt.Tooltip("Period:O", title="Period"),
            alt.Tooltip("Type:N", title="Type"),
            alt.Tooltip("Quantity:Q", title="Quantity", format=",")
        ]
    )

    chart_s4 = bars_s4.properties(
        title=f"Net Requirements → Planned Order Receipts (Fixed-Lot Rule: EOQ={int(eoq_central)}, MOQ={int(moq)}, m={int(m)})",
        width=600,
        height=300
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    step4_slide.content2 = mo.ui.altair_chart(chart_s4)
    return df_s4, step4_slide


@app.cell(hide_code=True)
def _(step4_slide):
    step4_slide.render_slide()
    return


@app.cell
def _(mo):
    lt_slider = mo.ui.slider(start=0, stop=5, value=2, step=1, label="Lead Time (periods)")
    return (lt_slider,)


@app.cell
def _(alt, df_s4, lt_slider, mo, pd, sc):
    step5_slide = sc.create_slide("Step 5: Planned Order Releases", layout_type="2-row")

    step5_slide.content1 = mo.vstack([
        mo.md(
            r"""
            **Planned Order Releases (Lead-Time Offset)**

            The **Planned Order Receipt ($POR_t$)** tells us *when* inventory must arrive at the central warehouse.

            To ensure this receipt arrives on time, we must **release** a purchase order **earlier**, shifted backward by the supplier **lead time ($L$)**.

            The **Planned Order Release ($OR_t$)** in period $t$ is simply the **Planned Order Receipt $L$ periods later**:

            $$OR_t = POR_{t+L} \quad\text{or}\quad POR_t = OR_{t-L}$$

            This means:
            - If we need material to **arrive** in week $t + L$, we must **release** in week $t$.
            - These releases become the **purchase requisitions** sent to suppliers.
            """
        ),
        lt_slider
    ])

    # Use the 20-day horizon from the computed planned receipts (Step 4)
    periods_s5 = list(range(1, len(df_s4) + 1))
    receipt_plan = pd.Series(df_s4["Planned Order Receipts"].values, index=periods_s5, dtype=int)

    lead_time = int(lt_slider.value)
    release_plan = receipt_plan.shift(-lead_time, fill_value=0).astype(int)

    timeline_df_s5 = pd.DataFrame({
        "Period": periods_s5,
        "Planned Receipts": receipt_plan.values,
        "Planned Releases": release_plan.values
    })

    melted_s5 = timeline_df_s5.melt(
        id_vars=["Period"],
        value_vars=["Planned Receipts", "Planned Releases"],
        var_name="Type",
        value_name="Quantity"
    )

    bars_s5 = alt.Chart(melted_s5).mark_bar(opacity=0.85).encode(
        x=alt.X("Period:O", title="Period"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(
                domain=["Planned Releases", "Planned Receipts"],
                range=["#e67e22", "#27ae60"]
            ),
            legend=alt.Legend(title="Type")
        ),
        xOffset="Type:N",
        tooltip=[
            alt.Tooltip("Period:O", title="Period"),
            alt.Tooltip("Type:N", title="Type"),
            alt.Tooltip("Quantity:Q", title="Quantity", format=",")
        ]
    )

    # Annotate lead-time offset between each receipt and its release
    max_qty = max(receipt_plan.max(), release_plan.max(), 1)
    arrow_y = max_qty * 1.1
    arrow_rows = []
    for period, qty in receipt_plan.items():
        if qty <= 0:
            continue
        release_period = period - lead_time
        if release_period < periods_s5[0]:
            continue
        arrow_rows.append({
            "Release": release_period,
            "Receipt": period,
            "y": arrow_y,
            "label": f"Release at t, receive at t+{lead_time}"
        })

    arrow_layer = alt.LayerChart()
    if arrow_rows:
        arrow_df = pd.DataFrame(arrow_rows)
        arrow_layer = alt.LayerChart(layer=[
            alt.Chart(arrow_df).mark_rule(
                color="#e74c3c",
                strokeDash=[4, 2],
                size=2
            ).encode(
                x=alt.X("Release:Q", scale=alt.Scale(domain=[periods_s5[0], periods_s5[-1]])),
                x2="Receipt:Q",
                y=alt.Y("y:Q")
            ),
            alt.Chart(arrow_df).mark_text(
                color="#e74c3c",
                fontWeight="bold",
                dy=-6
            ).encode(
                x=alt.X("Receipt:Q"),
                y=alt.Y("y:Q"),
                text="label:N"
            )
        ])

    chart_s5 = (bars_s5 + arrow_layer).properties(
        title=f"Lead-Time Offset: Order Releases (Orange) → Receipts (Green) | L = {lead_time}",
        width=700,
        height=320
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    step5_slide.content2 = mo.ui.altair_chart(chart_s5)
    return (step5_slide,)


@app.cell(hide_code=True)
def _(step5_slide):
    step5_slide.render_slide()
    return


@app.cell
def _(
    alt,
    df_s4,
    df_supply,
    eoq_slider,
    inv_df_s3,
    lt_slider,
    math,
    mo,
    moq_slider,
    mult_slider,
    pd,
    sc,
    step2_initial_inv,
    step2_receipt_qty,
    step2_safety_stock,
):
    overview_slide = sc.create_slide(
        "Steps 1–5: From Gross Requirements to Releases (Interactive)",
        layout_type="2-row"
    )

    overview_slide.content1 = mo.vstack([
        mo.md(
            """
            A single view of the full pipeline: gross requirements → projected on-hand → net requirements →
            planned receipts → planned releases. Adjust safety stock, receipts, lot sizing, and lead time to see the plan shift.
            """
        ),
        mo.hstack([
            mo.vstack([
                mo.md("**Step 2 Controls**"),
                step2_initial_inv,
                step2_safety_stock,
                step2_receipt_qty
            ], gap="0.35rem"),
            mo.vstack([
                mo.md("**Lot Sizing (Step 4)**"),
                eoq_slider,
                moq_slider,
                mult_slider,
                mo.md("**Lead Time (Step 5)**"),
                lt_slider
            ], gap="0.35rem")
        ], gap="2rem")
    ], gap="0.8rem")

    periods = list(range(1, len(df_s4) + 1))
    net_req_series = pd.Series(inv_df_s3["Net_Requirements"].values[: len(periods)], index=periods)
    receipts_series = pd.Series(df_s4["Planned Order Receipts"].values, index=periods)
    releases_series = receipts_series.shift(-int(lt_slider.value), fill_value=0).astype(int)

    combined_df = pd.DataFrame({
        "Period": periods,
        "Net Requirements": net_req_series.values,
        "Planned Receipts": receipts_series.values,
        "Planned Releases": releases_series.values
    })

    melted = combined_df.melt(
        id_vars=["Period"],
        value_vars=["Net Requirements", "Planned Receipts", "Planned Releases"],
        var_name="Type",
        value_name="Quantity"
    )

    color_domain = ["Net Requirements", "Planned Receipts", "Planned Releases"]
    color_range = ["#e74c3c", "#27ae60", "#e67e22"]

    overview_chart = alt.Chart(melted).mark_bar(opacity=0.85).encode(
        x=alt.X("Period:O", title="Period (days)"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color("Type:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=alt.Legend(title="Step Output")),
        xOffset="Type:N",
        tooltip=[
            alt.Tooltip("Period:O", title="Period"),
            alt.Tooltip("Type:N", title="Type"),
            alt.Tooltip("Quantity:Q", title="Quantity", format=",")
        ]
    ).properties(
        title=f"Lot Sizing and Lead-Time Shift | EOQ={int(eoq_slider.value)}, MOQ={int(moq_slider.value)}, m={int(mult_slider.value)}, L={int(lt_slider.value)}",
        width=760,
        height=340
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    # Step 1: Gross requirements chart (first 20 days)
    dates_s1 = df_supply["Date"].unique()
    dates_s1.sort()
    dates_s1 = dates_s1[:20]
    gross_req_s1 = df_supply.groupby("Date")["Order_Placed_Qty"].sum().reindex(dates_s1, fill_value=0).reset_index()
    gross_req_s1.columns = ["Date", "Demand"]
    step1_chart = alt.Chart(gross_req_s1).mark_bar().encode(
        x=alt.X("Date:T", title="Date", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Demand:Q", title="Gross Requirements"),
        color=alt.value("#3498db"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Demand:Q", title="Demand", format=",")
        ]
    ).properties(
        title="Step 1: Gross Requirements (Real DC Orders)",
        width=360,
        height=200
    ).configure_view(strokeWidth=0)

    # Step 2: Projected on-hand inventory (20 days) — recompute with unique names
    step2_dates = dates_s1
    step2_gross_req = df_supply.groupby("Date")["Order_Placed_Qty"].sum().reindex(step2_dates, fill_value=0)
    step2_planned_receipts = pd.Series(0, index=step2_dates)
    if len(step2_dates) > 5:
        step2_planned_receipts.iloc[5] = step2_receipt_qty.value
    if len(step2_dates) > 10:
        step2_planned_receipts.iloc[10] = step2_receipt_qty.value
    if len(step2_dates) > 14:
        step2_planned_receipts.iloc[14] = step2_receipt_qty.value
    step2_initial_inv_val = step2_initial_inv.value
    step2_safety_stock_val = step2_safety_stock.value
    step2_levels = []
    step2_current_inv = step2_initial_inv_val
    for step2_date in step2_dates:
        step2_demand = step2_gross_req.get(step2_date, 0)
        step2_receipt = step2_planned_receipts.get(step2_date, 0)
        step2_current_inv = step2_current_inv + step2_receipt - step2_demand
        step2_levels.append({
            "Date": step2_date,
            "Inventory": step2_current_inv,
            "Safety_Stock": step2_safety_stock_val
        })
    step2_df = pd.DataFrame(step2_levels)
    safety_line_overview = alt.Chart(pd.DataFrame({"y": [step2_safety_stock_val]})).mark_rule(
        strokeDash=[5, 5],
        color="orange",
        size=2
    ).encode(y="y:Q")
    step2_chart = (alt.Chart(step2_df).mark_line(point=True, color="#8e44ad").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Inventory:Q", title="Projected On Hand"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("Inventory:Q", title="Inventory", format=",")
        ]
    ) + safety_line_overview).properties(
        title="Step 2: Projected On-Hand vs. Demand",
        width=360,
        height=200
    ).configure_view(strokeWidth=0)

    # Dynamic net requirements based on projected inventory vs. safety stock
    dyn_net_req = pd.Series(
        [max(0, step2_safety_stock_val - inv) for inv in step2_df["Inventory"]],
        index=range(1, len(step2_df) + 1)
    )
    # Lot sizing for overview using sliders
    eoq_val = eoq_slider.value
    moq_val = moq_slider.value
    mult_val = max(1, mult_slider.value)
    dyn_receipts = []
    for nr in dyn_net_req:
        if nr > 0:
            base_qty_s5 = max(eoq_val, moq_val, nr)
            por_s5 = int(math.ceil(base_qty_s5 / mult_val)) * mult_val
        else:
            por_s5 = 0
        dyn_receipts.append(por_s5)
    dyn_receipts = pd.Series(dyn_receipts, index=dyn_net_req.index)
    dyn_releases = dyn_receipts.shift(-int(lt_slider.value), fill_value=0).astype(int)

    combined_df = pd.DataFrame({
        "Period": dyn_net_req.index,
        "Net Requirements": dyn_net_req.values,
        "Planned Receipts": dyn_receipts.values,
        "Planned Releases": dyn_releases.values
    })

    melted = combined_df.melt(
        id_vars=["Period"],
        value_vars=["Net Requirements", "Planned Receipts", "Planned Releases"],
        var_name="Type",
        value_name="Quantity"
    )

    color_domain = ["Net Requirements", "Planned Receipts", "Planned Releases"]
    color_range = ["#e74c3c", "#27ae60", "#e67e22"]

    overview_chart = alt.Chart(melted).mark_bar(opacity=0.85).encode(
        x=alt.X("Period:O", title="Period (days)"),
        y=alt.Y("Quantity:Q", title="Quantity"),
        color=alt.Color("Type:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=alt.Legend(title="Step Output")),
        xOffset="Type:N",
        tooltip=[
            alt.Tooltip("Period:O", title="Period"),
            alt.Tooltip("Type:N", title="Type"),
            alt.Tooltip("Quantity:Q", title="Quantity", format=",")
        ]
    ).properties(
        title=f"Lot Sizing and Lead-Time Shift | EOQ={int(eoq_val)}, MOQ={int(moq_val)}, m={int(mult_val)}, L={int(lt_slider.value)}",
        width=760,
        height=340
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

    overview_slide.content2 = mo.vstack([
        mo.hstack([mo.ui.altair_chart(step1_chart), mo.ui.altair_chart(step2_chart)], gap="1rem", justify="space-between"),
        mo.ui.altair_chart(overview_chart)
    ], gap="1.2rem")
    return (overview_slide,)


@app.cell(hide_code=True)
def _(overview_slide):
    overview_slide.render_slide()
    return


if __name__ == "__main__":
    app.run()
