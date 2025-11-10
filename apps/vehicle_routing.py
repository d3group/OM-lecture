import marimo

__generated_with = "0.16.5"
app = marimo.App(
    width="medium",
    app_title="Vehicle Routing",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    GH_USER = "d3group"
    GH_REPO = "OM-lecture"
    BRANCH = "main"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    # Check if running locally or in WASM export
    # In local mode: apps/public/data exists
    # In WASM export: public/data exists
    # Path.exists() doesn't work reliably in WASM, so we also check for micropip

    local_data_dir = Path("apps/public/data")
    wasm_data_dir = Path("public/data")

    # Detect WASM by checking if micropip is available
    try:
        import micropip as _micropip
        in_wasm = True
    except ImportError:
        in_wasm = False

    use_local = local_data_dir.exists() and not in_wasm
    use_wasm = (wasm_data_dir.exists() or in_wasm) and not use_local

    print(f"Detection: use_local={use_local}, use_wasm={use_wasm}, in_wasm={in_wasm}")

    class DataURLs:
        if use_local:
            # Local development mode
            BASE = "apps/public/vrptw/data"
            IMG_BASE = "apps/public/vrptw/images"
            SCENARIOS = f"{BASE}/scenarios.csv"
            PHARMACIES = f"{BASE}/pharmacies.parquet"
            METADATA = f"{BASE}/metadata.json"
        else:
            # WASM/deployed mode - use GitHub raw URLs for data files
            BASE = raw_url("apps", "public", "vrptw", "data")
            IMG_BASE = "public/vrptw/images"  # Images work with relative paths
            SCENARIOS = f"{BASE}/scenarios.csv"
            PHARMACIES = f"{BASE}/pharmacies.parquet"
            METADATA = f"{BASE}/metadata.json"

    print(f"Using BASE: {DataURLs.BASE}")
    return (DataURLs,)


@app.cell(hide_code=True)
async def _():
    # Only install packages in WebAssembly environment
    try:
        import micropip

        # Install required packages for VRPTW analysis
        packages = [
            "polars",
            "folium",
            "pyarrow",
            "requests"
        ]

        for pkg in packages:
            print(f"Installing {pkg}...")
            await micropip.install(pkg)

        print("✅ All packages installed.")
    except ImportError:
        # Running locally, packages should already be installed
        print("Running in local mode, skipping micropip installation")
    return


@app.cell(hide_code=True)
def _():
    # Import required libraries for VRPTW analysis
    import polars as pl
    import folium
    import json
    import marimo as mo
    import requests
    import math
    import altair as alt
    import pandas as pd
    import colorsys
    import numpy as np
    from typing import Iterable, Optional
    from folium import plugins
    return (
        Iterable,
        Optional,
        alt,
        colorsys,
        folium,
        json,
        math,
        mo,
        pd,
        pl,
        plugins,
        requests,
    )


@app.cell(hide_code=True)
def _(mo):
    # For WASM compatibility, we inline the slides classes here
    # (marimo doesn't bundle utils/ in WASM exports)
    from __future__ import annotations
    from dataclasses import dataclass
    from typing import Optional as _Optional
    import html as _html

    # Slide constants
    SLIDE_WIDTH = 1280
    SLIDE_HEIGHT = 720
    GAP = 24
    PADDING_X = 24
    PADDING_Y = 16
    TITLE_FONT_SIZE = 28
    FOOTER_FONT_SIZE = 12

    @dataclass
    class Slide:
        title: str
        chair: str
        course: str
        presenter: str
        logo_url: _Optional[str]
        page_number: int
        layout_type: str = "side-by-side"
        subtitle: _Optional[str] = None
        content1: _Optional[mo.core.MIME] = None
        content2: _Optional[mo.core.MIME] = None

        def _header(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            return mo.Html(
                f"""
                <div class="slide-header">
                  <div class="slide-title" style="font-size: {TITLE_FONT_SIZE}px; font-weight: 700; line-height: 1.2; margin: 0;">{safe_title}</div>
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                </div>
                """
            )

        def _footer(self) -> mo.core.MIME:
            safe_page = _html.escape(str(self.page_number))
            safe_chair = _html.escape(self.chair)
            left_html = f"Page {safe_page} &nbsp;&nbsp;|&nbsp;&nbsp; {safe_chair}"
            center_img = (
                f'<img class="slide-logo" src="{_html.escape(self.logo_url)}" alt="logo" style="display: block; max-height: 28px; max-width: 160px; margin: 0 auto; object-fit: contain;">'
                if self.logo_url else "&nbsp;"
            )
            return mo.Html(
                f"""
                <div class="slide-footer">
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                  <div class="slide-footer-row" style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;">
                    <div class="slide-footer-left" style="font-size: {FOOTER_FONT_SIZE}px; color: #6B7280; white-space: nowrap;">{left_html}</div>
                    <div class="slide-footer-center">{center_img}</div>
                    <div class="slide-footer-right">&nbsp;</div>
                  </div>
                </div>
                """
            )

        def _title_layout(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            sub = f'<div class="title-slide-sub" style="font-size: 40px; margin: 0 0 16px 0; color: #374151;">{_html.escape(self.subtitle)}</div>' if self.subtitle else ""
            body = mo.Html(
                f"""
                <div class="slide-body title-center" style="flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; height: 100%;">
                  <div class="title-stack" style="text-align: center;">
                    <div class="title-slide-title" style="font-size: 50px; font-weight: 800; margin: 0 0 8px 0;">{safe_title}</div>
                    {sub}
                    <div class="title-slide-meta" style="font-size: 30px; color: #6B7280;">{_html.escape(self.course)}</div>
                    <div class="title-slide-meta" style="font-size: 22px; color: #6B7280;">{_html.escape(self.presenter)}</div>
                  </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _one_column_layout(self) -> mo.core.MIME:
            content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            content_wrapped = mo.vstack([content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                        <style>
                            ul {{ margin-top: -0.2em !important; }}
                            .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            li {{ font-size: 19px !important; }}
                            li * {{ font-size: 19px !important; }}
                        </style>
                        {content_wrapped}
                    </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _side_by_side_layout(self) -> mo.core.MIME:
            left_content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            right_content = mo.md(self.content2) if isinstance(self.content2, str) else (self.content2 or mo.md(""))
            left = mo.vstack([left_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            right = mo.vstack([right_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <style>
                        ul {{ margin-top: -0.2em !important; }}
                        .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        li {{ font-size: 19px !important; }}
                        li * {{ font-size: 19px !important; }}
                    </style>
                    <div class="slide-cols" style="display: grid; grid-template-columns: 1fr 1fr; gap: {GAP}px; height: 100%; min-height: 0;">
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {left}
                        </div>
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {right}
                        </div>
                    </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def render(self) -> mo.core.MIME:
            if self.layout_type == "title":
                return self._title_layout()
            elif self.layout_type == "1-column":
                return self._one_column_layout()
            return self._side_by_side_layout()

    class SlideCreator:
        def __init__(self, chair: str, course: str, presenter: str, logo_url: _Optional[str] = None):
            self.chair = chair
            self.course = course
            self.presenter = presenter
            self.logo_url = logo_url
            self._page_counter = 0

        def styles(self) -> mo.core.MIME:
            return mo.Html(
                f"""
                <style>
                  :root {{
                    --slide-w: {SLIDE_WIDTH}px;
                    --slide-h: {SLIDE_HEIGHT}px;
                    --gap: {GAP}px;
                    --pad-x: {PADDING_X}px;
                    --pad-y: {PADDING_Y}px;
                    --title-size: {TITLE_FONT_SIZE}px;
                    --footer-size: {FOOTER_FONT_SIZE}px;
                    --border-color: #E5E7EB;
                    --text-muted: #6B7280;
                    --bg: #ffffff;
                  }}
                  div.slide, .slide {{
                    width: var(--slide-w) !important;
                    height: var(--slide-h) !important;
                    min-width: var(--slide-w) !important;
                    min-height: var(--slide-h) !important;
                    max-width: var(--slide-w) !important;
                    max-height: var(--slide-h) !important;
                    box-sizing: border-box !important;
                    background: var(--bg) !important;
                    padding: var(--pad-y) var(--pad-x) !important;
                    display: flex !important;
                    flex-direction: column !important;
                    border-radius: 6px;
                    box-shadow: 0 0 0 1px #f3f4f6;
                    overflow: hidden !important;
                  }}
                  div.slide-title, .slide-title {{
                    font-size: var(--title-size) !important;
                    font-weight: 700 !important;
                    line-height: 1.2 !important;
                    margin: 0 !important;
                  }}
                  div.slide-hr, .slide-hr {{
                    height: 1px !important;
                    background: var(--border-color) !important;
                    margin: 8px 0 !important;
                  }}
                  div.slide-body, .slide-body {{
                    flex: 1 1 auto !important;
                    min-height: 0 !important;
                    display: flex !important;
                    flex-direction: column !important;
                  }}
                  div.slide-cols, .slide-cols {{
                    display: grid !important;
                    grid-template-columns: 1fr 1fr !important;
                    gap: var(--gap) !important;
                    height: 100% !important;
                    min-height: 0 !important;
                  }}
                  div.slide-col, .slide-col {{
                    min-height: 0 !important;
                    overflow: auto !important;
                    padding-right: 2px !important;
                  }}
                  div.slide-footer div.slide-footer-row, .slide-footer .slide-footer-row {{
                    display: grid !important;
                    grid-template-columns: 1fr auto 1fr !important;
                    align-items: center !important;
                  }}
                  div.slide-footer-left, .slide-footer-left {{
                    font-size: var(--footer-size) !important;
                    color: var(--text-muted) !important;
                    white-space: nowrap !important;
                  }}
                  img.slide-logo, .slide-logo {{
                    display: block !important;
                    max-height: 28px !important;
                    max-width: 160px !important;
                    margin: 0 auto !important;
                    object-fit: contain !important;
                  }}
                  div.title-center, .title-center {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    height: 100% !important;
                  }}
                  div.title-stack, .title-stack {{
                    text-align: center !important;
                  }}
                  div.title-slide-title, .title-slide-title {{
                    font-size: 40px !important;
                    font-weight: 800 !important;
                    margin: 0 0 8px 0 !important;
                  }}
                  div.title-slide-sub, .title-slide-sub {{
                    font-size: 20px !important;
                    margin: 0 0 16px 0 !important;
                    color: #374151 !important;
                  }}
                  div.title-slide-meta, .title-slide-meta {{
                    font-size: 16px !important;
                    color: var(--text-muted) !important;
                  }}
                  .tight-md p {{ margin: 0 0 4px 0 !important; }}
                  .tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  .tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  ul {{ margin-top: -0.2em !important; margin-bottom: 6px !important; margin-left: 1.25em !important; margin-right: 0 !important; }}
                  .tight-md li {{ margin: 2px 0 !important; font-size: 19px !important; }}
                  li {{ font-size: 19px !important; }}
                  li * {{ font-size: 19px !important; }}
                  .tight-md h1, .tight-md h2, .tight-md h3, .tight-md h4 {{ margin: 0 0 6px 0 !important; }}
                </style>
                """
            )

        def create_slide(self, title: str, layout_type: str = "side-by-side", page_number: _Optional[int] = None) -> Slide:
            if page_number is None:
                self._page_counter += 1
                page_number = self._page_counter
            return Slide(
                title=title,
                chair=self.chair,
                course=self.course,
                presenter=self.presenter,
                logo_url=self.logo_url,
                page_number=page_number,
                layout_type=layout_type,
            )

        def create_title_slide(self, title: str, subtitle: _Optional[str] = None, page_number: _Optional[int] = None) -> Slide:
            slide = self.create_slide(title, layout_type="title", page_number=page_number)
            slide.subtitle = subtitle
            return slide

    return (SlideCreator,)


@app.cell(hide_code=True)
def _():
    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Operations Management"
    presenter = "Richard Pibernik, Nikolai Stein"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    DEPOT_LAT, DEPOT_LON = 49.504896, 11.015822

    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return DEPOT_LAT, DEPOT_LON, sc


@app.cell(hide_code=True)
def _(sc):
    titleSlide = sc.create_title_slide(
        "Vehicle Routing with Time Windows",
        subtitle="Optimizing Last-Mile Delivery"
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    motivationPart1Slide = sc.create_slide(
        'How to deliver the order to the customer?',
        layout_type='side-by-side',
        page_number=2
    )

    motivationPart1Slide.content1 = mo.md(
        """
        **Order delivery**
        - After an order has been confirmed it has to be delivered to the customer (pharmacy)
        - However, it is not financially viable to deliver each order for every single product individually
        - Instead, Phoenix operates multiple **warehouses**, each operating a fleet of delivery trucks, to serve customers across **Germany**

        We call this interconnected system of storage facilities and transportation methods a **distribution network**
        """
    )

    motivationPart1Slide.content2 = mo.image(f'{DataURLs.IMG_BASE}/planner_distribution_network.png')

    motivationPart1Slide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    motivationPart2Slide = sc.create_slide(
        'How to deliver the order to the customer?',
        layout_type='side-by-side',
        page_number=3
    )

    motivationPart2Slide.content1 = mo.md(
        """
        **Last mile**
        - In this example, focus on the distribution for customers in the **Fürth** region
        - Here, Phoenix operates a warehouse and a fleet of delivery trucks serving pharmacies in the region
        - Instead of delivering each order of Amoxicillin directly, planners have to decide which delivery tour is used to deliver an order to the customer in time at minimal cost
        - We call this final step of the delivery process where goods are moved from a transportation hub to their final destination **last-mile delivery**

        **Key Question:** How can we design stable and efficient tours for **last-mile delivery**?

        """
    )

    motivationPart2Slide.content2 = mo.image(f'{DataURLs.IMG_BASE}/planner_last_mile.png')

    motivationPart2Slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    problemDescriptionSlide = sc.create_slide(
        "The underlying decision problem",
        layout_type="2-column",
        page_number=4
    )
    problemDescriptionSlide.content1 = mo.md(
        """
        **Intuition**:
        - Designing the daily truck tours is a well-**studied** but **notoriously** hard problem known as **V**ehicle **R**outing **P**roblem with **T**ime **W**indows (VRPTW)
        - We must plan daily truck tours so that all pharmacies receive their orders **within promised time windows**, using **limited vehicle capacity**, while keeping **total cost low**.

        **What goes in (parameters)**:
        - **Customers**: locations, delivery time windows
        - **Network**: warehouse (depot), road travel times/distances.
        - **Fleet**: number of trucks, capacities, shift limits (max route duration), fixed/variable costs

        **What we decide (decisions)**:
        - **Sequencing (routing)**: visit order per truck
        - **Timing**: arrival times to hit each customer’s time window
        """
    )

    problemDescriptionSlide.content2 = mo.md(
        """
        **What must be respected (constraints)**:
        - **Capacity**: load on any truck ≤ capacity
        - **Time windows**: arrival within each customer’s window
        - **Service & travel times**: cumulative time including service at each stop
        - **Route rules**: each customer served exactly once; vehicle starts/ends at depot; max route duration/driver hours/breaks

        **What we optimize (objective)**:
        - Minimize **total cost** (distance)

        **How this maps to our example**
        - Depot: Phoenix warehouse (**Fürth** region)
        - Customers: pharmacies with daily orders and contracted delivery windows
        - Fleet: delivery vans with known capacity and shift length
        - Goal: cover all pharmacies on time with as few km as possible
        """
    )

    problemDescriptionSlide.render()
    return


@app.cell
def _(pl, requests):
    def get_customers_overpass(
        customer_type: str, center_lat: float, center_lon: float, radius_km: float, timeout: int = 30
    ) -> pl.DataFrame:
        OVERPASS_URLS = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",  # common CORS-friendly mirror
        ]
        """Fetch POIs within a radius using Overpass (browser-safe: HTTPS + GET with params)."""
        radius_m = int(radius_km * 1000)

        query = f"""
        [out:json][timeout:{timeout}];
        (
          node["amenity"="{customer_type}"](around:{radius_m},{center_lat},{center_lon});
        );
        out center;
        """

        last_err = None
        for url in OVERPASS_URLS:
            try:
                # In browsers, use GET with ?data=... to satisfy CORS rules
                r = requests.get(url, params={"data": query}, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                if "elements" not in data:
                    raise ValueError("Invalid response format from Overpass API")

                rows = []
                for el in data["elements"]:
                    if el["type"] == "node":
                        lat, lon = el["lat"], el["lon"]
                    elif el["type"] in ("way", "relation") and "center" in el:
                        lat, lon = el["center"]["lat"], el["center"]["lon"]
                    else:
                        continue
                    tags = el.get("tags", {})
                    name = tags.get("name", tags.get("brand", str(el["id"])))
                    rows.append({"name": name, "lat": lat, "lon": lon})

                return pl.DataFrame(rows)

            except Exception as e:
                last_err = e
                continue

        # If all endpoints failed, surface the last error with context
        raise requests.RequestException(f"Overpass request failed (HTTPS/GET). Last error: {last_err}")
    return (get_customers_overpass,)


@app.cell(hide_code=True)
def _(mo):
    category_selector = mo.ui.dropdown(options= {'Pharmacies': 'pharmacy', 'Doctors': 'doctors', 'Parcel lockers': 'parcel_locker', 'Bars': 'bar'}, value='Pharmacies', label='Category')

    center_lat_selector = mo.ui.text(label='Latitude', value='49.504896')
    center_lon_selector = mo.ui.text(label='Longitude', value='11.015822')
    run_button = mo.ui.run_button(label='Search')
    return (
        category_selector,
        center_lat_selector,
        center_lon_selector,
        run_button,
    )


@app.cell(hide_code=True)
def _(
    category_selector,
    center_lat_selector,
    center_lon_selector,
    get_customers_overpass,
    mo,
    pl,
    run_button,
    sc,
):
    findingCustomersSlide = sc.create_slide(
        "Estimating the model parameters (Customers)",
        layout_type='side-by-side',
        page_number=5
    )

    findingCustomersSlide.content1 = mo.md(
        """
        **Idea**:
        - In order to plan the tours we need to know all locations that have to be visited regularly
        - In the case of Phoenix, we have to identify all relevant customers (pharmacies) in each delivery region
        - In our example we use the Phoenix warehouse (depot) in **Fürth** (lat: 49.504896, lon: 11.015822)

        **Solution**:
        - To identify relevant locations we can use geocoding APIs
        - We can choose commercial options such as Google Places or open-source options such as Nominatim or Overpass
        - The function ```get_customers_overpass``` shows how to query such APIs (see the [documentation](https://wiki.openstreetmap.org/wiki/Key:amenity) for a full list of available categories)
        """
    )

    data = pl.DataFrame(data={'name':[], 'lat': [], 'lon': []})

    if run_button.value and center_lat_selector.value.replace('.','',1).isdigit() and center_lon_selector.value.replace('.','',1).isdigit():
        data = get_customers_overpass(customer_type=category_selector.value, 
                                      center_lat=float(center_lat_selector.value), 
                                      center_lon=float(center_lon_selector.value), 
                                      radius_km=10)

    findingCustomersSlide.content2 = mo.vstack([
        mo.hstack([
            category_selector,
            center_lat_selector,
            center_lon_selector
        ], justify='center'),
        run_button,
        mo.ui.table(data, show_column_summaries=False, show_data_types=False, selection=None)
    ])

    findingCustomersSlide.render()
    return (data,)


@app.cell(hide_code=True)
def _(DataURLs, pd, pl):
    # Load main datasets
    df_scenarios = pl.read_csv(DataURLs.SCENARIOS)

    # Try parquet with polars, fallback to pandas if it fails (WASM compatibility)
    try:
        df_pharmacies = pl.read_parquet(DataURLs.PHARMACIES)
    except (AttributeError, Exception) as e:
        # WASM polars doesn't support parquet properly
        # Use pandas to read parquet, then convert to polars
        print(f"Polars parquet failed: {e}, using pandas fallback...")
        df_pharmacies_pd = pd.read_parquet(DataURLs.PHARMACIES)
        df_pharmacies = pl.from_pandas(df_pharmacies_pd)

    return df_pharmacies, df_scenarios


@app.cell(hide_code=True)
def _(DEPOT_LAT, DEPOT_LON, Iterable, Optional, df_scenarios, folium, mo, pl):
    def create_params_map(
        radius_km: float,
        pharmacies_df: pl.DataFrame,
        *,
        highlighted_ids: Optional[Iterable] = None,
        id_col: str = "id",
        highlight_color: str = "orange",
        highlight_radius: int = 7,
        normal_color: str = "green",
        normal_radius: int = 3,
        zoom_start = 8
    ):
        """
        Build a folium map around the depot with a radius overlay and pharmacy markers.
        Optionally highlight a subset of pharmacies by id (bigger marker + different color).
        Returns (map, count_of_displayed_pharmacies).
        """
        highlighted_ids = set(highlighted_ids or [])

        _params_map = folium.Map(
            location=[DEPOT_LAT, DEPOT_LON],
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
            width=500,
            height=300,
        )

        folium.Marker(
            [DEPOT_LAT, DEPOT_LON],
            popup="Distribution Depot",
            tooltip="Phoenix Warehouse Sportplatzstraße 30, 90765 Fuerth",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(_params_map)

        folium.Circle(
            location=[DEPOT_LAT, DEPOT_LON],
            radius=radius_km * 1000,
            color="blue",
            fillColor="lightblue",
            fillOpacity=0.2,
            weight=2,
        ).add_to(_params_map)

        # Decide which rows to display (respect radius if available)
        filtered_df = pharmacies_df
        if {"lat", "lon"}.issubset(set(pharmacies_df.columns)):
            if "distance_from_center_km" in pharmacies_df.columns:
                filtered_df = pharmacies_df.filter(
                    pl.col("distance_from_center_km") <= radius_km
                )
            # else: keep all rows (no radius filter available)

            # Add markers
            for row in filtered_df.iter_rows(named=True):
                is_highlight = row.get(id_col) in highlighted_ids if id_col in pharmacies_df.columns else False
                color = highlight_color if is_highlight else normal_color
                radius = highlight_radius if is_highlight else normal_radius

                folium.CircleMarker(
                    [row["lat"], row["lon"]],
                    radius=radius,
                    popup=f"{row.get('name', 'Unknown')}",
                    tooltip=f"{row.get('name', 'Unknown')}",
                    color="darkgreen" if not is_highlight else color,
                    fillColor=color,
                    fillOpacity=0.85 if is_highlight else 0.7,
                    weight=2 if is_highlight else 1,
                ).add_to(_params_map)

            count = filtered_df.height
        else:
            # No coordinates → nothing to plot
            count = 0

        return _params_map, count


    radius_vals_params = sorted(df_scenarios.select(pl.col("radius_km")).unique().to_series().to_list())
    map_radius_slider_params = mo.ui.slider(
        start=min(radius_vals_params),
        stop=max(radius_vals_params),
        step=5,
        value=25,
        label="Service Radius (km)"
    )
    return create_params_map, map_radius_slider_params


@app.cell(hide_code=True)
def _(create_params_map, df_pharmacies, map_radius_slider_params, mo, sc):
    customerViewSlide = sc.create_slide(
        "Finding the customers for the Fürth warehouse",
        layout_type='side-by-side',
        page_number=6
    )

    customerViewSlide.content1 = mo.md(
        """
        We can **formalize** the customer related parameters as follows:
        - Set of pharmacies: $\mathcal{C} = \{1, 2, \ldots, n\}$
        - Each pharmacy $i \in \mathcal{C}$ is located at coordinates $(x_i, y_i)$
        - Each pharmacy $i$ has a time window $[e_i, l_i]$ where it expects deliveries
        - $e_i$: earliest time delivery can start
        - $l_i$: latest time delivery must be completed
        - Vehicle must start service within this window

        To keep things fast in class, we’ll now switch from live queries to a **pre-downloaded set of real pharmacies** around the **Fürth** depot
        """
    )

    _params_map, _n_rows = create_params_map(
        radius_km=map_radius_slider_params.value, 
        pharmacies_df=df_pharmacies
    )

    customerViewSlide.content2 = mo.vstack([
        mo.hstack([
            map_radius_slider_params,
            mo.md("$|\\mathcal{C}|$ = " + str(_n_rows))
        ], justify="start", gap=3),
        _params_map
    ])

    customerViewSlide.render()
    return


@app.cell(hide_code=True)
def _(math):
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine great-circle distance between two WGS84 points in kilometers."""
        R_km = 6371.0088
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, (lat1, lon1, lat2, lon2))
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R_km * c


    def calculate_travel_time(distance_km: float, speed_kmh: float=40) -> float:
        """Return travel time for a given distance and constant speed in minutes."""
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be > 0")

        time_h = distance_km / speed_kmh
        return time_h * 60
    return calculate_distance, calculate_travel_time


@app.cell(hide_code=True)
def _(DEPOT_LAT, DEPOT_LON, calculate_distance, calculate_travel_time, pl):
    def _first_coords_by_name(df: pl.DataFrame, name: str) -> tuple[float, float] | None:
        rows = df.filter(pl.col("name") == name).select("lat", "lon").to_numpy()
        if rows.size == 0:
            return None
        return float(rows[0, 0]), float(rows[0, 1])

    def build_distance_matrix(df_pharmacies: pl.DataFrame, selected_names: list[str]) -> pl.DataFrame:
        """
        Distance matrix (km) for Depot + selected pharmacy names.
        - Uses the first occurrence of each name in df_pharmacies.
        - Skips None/empty or not-found names.
        - Calls the provided calculate_distance(lat1, lon1, lat2, lon2).
        """
        # Clean list: drop None/empty, preserve order, dedupe
        seen, clean = set(), []
        for n in selected_names:
            if n and n not in seen:
                clean.append(n); seen.add(n)

        nodes = ["Depot"] + clean
        coords: dict[str, tuple[float, float]] = {"Depot": (DEPOT_LAT, DEPOT_LON)}

        # Resolve coords for names; drop those not found
        missing = []
        for n in clean:
            c = _first_coords_by_name(df_pharmacies, n)
            if c is None:
                missing.append(n)
            else:
                coords[n] = c
        for n in missing:
            nodes.remove(n)

        # Build pairwise distances
        data = {"from": nodes}
        for j in nodes:
            latj, lonj = coords[j]
            col_vals = []
            for i in nodes:
                if i == j:
                    col_vals.append(0.0)
                else:
                    lati, loni = coords[i]
                    col_vals.append(calculate_distance(lati, loni, latj, lonj))
            data[j] = col_vals

        df = pl.DataFrame(data)
        # Round numeric columns (all except 'from') for display
        df = df.with_columns(pl.col([c for c in nodes]).round(2))
        return df


    def build_travel_time_matrix(
        df_pharmacies: pl.DataFrame,
        selected_names: list[str],
        *,
        speed_kmh: float = 40.0
    ) -> pl.DataFrame:
        """
        Travel-time matrix (minutes) for Depot + selected pharmacy names.
        Uses:
          - calculate_distance(lat1, lon1, lat2, lon2) -> km
          - calculate_travel_time(distance_km, speed_kmh) -> minutes
        Skips None/empty/not-found names; uses first occurrence per name.
        """
        # Clean list: drop None/empty, preserve order, dedupe
        seen, clean = set(), []
        for n in selected_names:
            if n and n not in seen:
                clean.append(n); seen.add(n)

        nodes = ["Depot"] + clean
        coords: dict[str, tuple[float, float]] = {"Depot": (DEPOT_LAT, DEPOT_LON)}

        # Resolve coords and drop missing
        missing = []
        for n in clean:
            c = _first_coords_by_name(df_pharmacies, n)
            if c is None:
                missing.append(n)
            else:
                coords[n] = c
        for n in missing:
            nodes.remove(n)

        # Build pairwise travel times
        data = {"from": nodes}
        for j in nodes:
            latj, lonj = coords[j]
            col_vals = []
            for i in nodes:
                if i == j:
                    col_vals.append(0.0)
                else:
                    lati, loni = coords[i]
                    d_km = calculate_distance(lati, loni, latj, lonj)
                    t_min = calculate_travel_time(d_km, speed_kmh=speed_kmh)
                    col_vals.append(t_min)
            data[j] = col_vals

        df = pl.DataFrame(data)
        # Round numeric columns (all except 'from') for display
        df = df.with_columns(pl.col([c for c in nodes]).round(1))
        return df
    return build_distance_matrix, build_travel_time_matrix


@app.cell(hide_code=True)
def _(data, mo):
    location1Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    location2Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    location3Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    choice = mo.ui.radio(
        options=["Distance (km)", "Time (min)"],
        value="Distance (km)",
        inline=True,        # puts options on one line
    )
    return choice, location1Selector, location2Selector, location3Selector


@app.cell(hide_code=True)
def _(
    build_distance_matrix,
    build_travel_time_matrix,
    choice,
    create_params_map,
    data,
    location1Selector,
    location2Selector,
    location3Selector,
    mo,
    sc,
):
    networkViewSlides = sc.create_slide(
        "Estimating the model parameters (Network)",
        layout_type='side-by-side',
        page_number=7
    )

    networkViewSlides.content1 = mo.md(
                """
                **Idea**:
                - To compare the length (and costs) of different tours we need to know the pairwise **distances** between all nodes (depot + customers) in the network
                - To ensure that every customer is served inside the time window we also need to know the pairwise **travel times**
                - We want to use clear units (km, minutes)

                **Simple solution**:
                - Compute the Haversine distance
                - Convert to time with a constant speed
                - See implementations in ```calculate_distance``` and ```calculate_travel_time```

                **More realistic option**
                - To identify realisitc times and distances we can use routing APIs
                - We can choose commercial options such as Google Maps or open source options such as OSRM
                """
            )

    selected_names = [
        location1Selector.value,
        location2Selector.value,
        location3Selector.value
    ]

    _params_map, _ = create_params_map(
        radius_km=10, 
        pharmacies_df=data,
        zoom_start=10,
        highlighted_ids=selected_names,
        id_col='name'
    )

    _distance_df = build_distance_matrix(data, selected_names)
    _traveltime_df = build_travel_time_matrix(data, selected_names, speed_kmh=40)  

    _table = (
        mo.ui.table(_distance_df, pagination=False, selection=None,
                    show_column_summaries=False, show_data_types=False, show_download=False)
        if choice.value == "Distance (km)"
        else
        mo.ui.table(_traveltime_df, pagination=False, selection=None,
                    show_column_summaries=False, show_data_types=False, show_download=False)
    )

    networkViewSlides.content2 = mo.vstack([
        mo.hstack([
            location1Selector,
            location2Selector,
            location3Selector
        ], justify="start", gap=2),
        _params_map,
        choice,
        _table
    ])

    networkViewSlides.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    distanceMatrixSlide = sc.create_slide(
        "Estimating the model parameters (Network)",
        layout_type='side-by-side',
        page_number=8
    )

    distanceMatrixSlide.content1 = mo.md(
        """
        We can **formalize** the network related parameters as follows:
        - Distance matrix $\mathcal{D}$:
            - $d_{ij}$ = distance (in km) from location $i$ to location $j$
            - $i, j \in N$ where $N = \{0\} \cup \mathcal{C}$ ($0$ is the depot)
        - Travel time matrix $\mathcal{T}$:
            - $t_{ij}$ = travel time (in minutes) from location $i$ to location $j$
            - Depends on distance, road types, traffic conditions
            - Used to ensure time window constraints are satisfied

        To keep things realistic and fast, we **precomputed** the real distance and travel time matrix using the **Open Source Routing Machine (OSRM)**
        """
    )

    distanceMatrixSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/osrm-backend.png')

    distanceMatrixSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    decisionVariablesSlide = sc.create_slide(
        'Modelling the decisions',
        layout_type='1-column',
        page_number=9
    )

    decisionVariablesSlide.content1 = mo.md(
        r'''
        To solve the routing problem we have to account for two types of decisions:
        - The order in which the vehicles visit the customers (**sequencing**)
        - The time when we start servicing a customer (**timing**)

        We can **formalize** these decision variables as follows:
        - For each arc (connection) $(i,j)$ and each vehicle $k$ we define $x_{ijk}$ as:

            $$
            x_{ijk} =
            \begin{cases}
            1, & \text{if vehicle } k \text{ drives directly from customer } i \text{ to customer } j,\\
            0, & \text{otherwise.}
            \end{cases}
            $$

        - Decision variable $s_{ik}$ is defined for each vertex $i$ and each vehicle $k$ and denotes the time vehicle $k$ starts to service customer $i$
        - In case vehicle $k$ does not service customer $i$, $s_{ik}$ has no meaning and its value is considered irrelevant
        '''
    )

    decisionVariablesSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    objectiveFunctionSlide = sc.create_slide(
        'Modelling the objective function',
        layout_type='side-by-side',
        page_number=10
    )

    objectiveFunctionSlide.content1 = mo.md(
        r'''
        To find optimal tours, we need to specify the goal of the routing problem. In the VRPTW, this goal is typically to **minimize total operational cost**.

        We can express this idea as follows:
        - **Objective**: Find a set of vehicle routes that:
            - serve all customers within their time windows,
            - respect vehicle capacity and time constraints
            - **minimize** the total cost of operation
        - **Typical cost measures include**:
            - Total travel distance (**we are using this one for our example**)
            - Number of vehicles used
            - Driver or fuel cost components
        - **Mathematically, the objective function can be written as**:

            $$
            \min \sum_{k\in K} \sum_{i\in N} \sum_{j\in N}d_{ij}x_{ijk}
            $$
        '''
    )

    objectiveFunctionSlide.content2 =  mo.image(f'{DataURLs.IMG_BASE}/objective.png')

    objectiveFunctionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    flowConservationSlide = sc.create_slide(
        'Modelling the constraints (Flow conservation)',
        layout_type='1-column',
        page_number=11
    )

    flowConservationSlide.content1 = mo.md(
        r'''
        To ensure **feasible** vehicle routes, we must control how vehicles enter and leave each customer location. These constraints guarantee that every customer is visited exactly once and that **vehicle flows are consistent**.

        We can express these constraints as follows:
        - **Each customer is visited exactly once**:

            $$
            \sum_{k\in K}\sum_{\substack{i\in\mathcal{N}\\ i\ne j}} x_{ijk} = 1 \quad \forall j\in \mathcal{C}
            $$

            → Every customer $j$ must have exactly one vehicle arriving
        - **Each vehicle leaves the depot at most once**:

            $$
            \sum_{j\in \mathcal{C}}x_{0jk} \le 1 \quad \forall k\in K
            $$

        - **Each vehicle returns to the depot at most once**:

            $$
            \sum_{i\in \mathcal{C}}x_{i0k} \le 1 \quad \forall k\in K
            $$

        These constraints ensure a **balanced flow** — vehicles start at the depot, visit a subset of customers, and return.
        '''
    )

    flowConservationSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    flowContinuitySlide = sc.create_slide(
        'Modelling the constraints (Flow continuity)',
        layout_type='1-column',
        page_number=12
    )

    flowContinuitySlide.content1 = mo.md(
        r'''
        After defining how vehicles start and end their routes, we now ensure **continuity** along each vehicle’s path.

        If a vehicle arrives at a customer, it must also leave again — this prevents disconnected or partial routes.

        We can express this logic as:
        - **Flow continuity constraint**:

            $$
            \sum_{i\in \mathcal{N}}x_{ijk} - \sum_{i\in \mathcal{N}}x_{jik} = 0 \quad \forall j\in \mathcal{C}, \forall k\in K
            $$

        - where:
            - The **first term** counts all arcs entering customer $j$ for vehicle $k$
            - The **second term** counts all arcs leaving the same customer
            - The equality enforces that every vehicle entering a customer must also depart once, ensuring a continuous path

        **Interpretation**:
        - Prevents "dead ends" or isolated visits
        - Keeps routes consistent for each vehicle from start to end
        - Ensures feasible and connected tours
        '''
    )

    flowContinuitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    vehicleCapacitySlide = sc.create_slide(
        'Modelling the constraints (Vehicle capacity)',
        layout_type='1-column',
        page_number=13
    )

    vehicleCapacitySlide.content1 = mo.md(
        r'''
        Each vehicle has a **limited load capacity**, and each customer requires a certain delivery amount. These constraints ensure that the total demand assigned to any vehicle never exceeds its available capacity.

        We can express this restriction as:
        - **Capacity constraint**:

            $$
            \sum_{i\in \mathcal{C}}q_i \sum_{j\in \mathcal{N}}x_{ijk} \leq Q_{k} \quad \forall k\in K
            $$

        - where:
            - $q_i$ is the demand of customer $i$
            - $Q_k$ is the maximum capacity of vehicle $k$

        **Interpretation**:
        - Each vehicle’s total delivered quantity must fit within its truck capacity
        - Prevents routes that would overload a vehicle
        - Links the assignment of customers to physical resource limits
        '''
    )

    vehicleCapacitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    timeWindowServiceStartSlide = sc.create_slide(
        'Modelling the constraints (Time windows & service start)',
        layout_type='1-column',
        page_number=14
    )

    timeWindowServiceStartSlide.content1 = mo.md(
        r'''
        Each customer has an allowed **time window** $[e_i,l_i]$. Service must **start within the window**, and vehicles may **wait** if they arrive early. We require $h_i$ minutes to service customer $i$.

        We can **formalize** this as follows:
        - **Time propagation (linearized with big-M):**

            $$
            s_{jk} \;\ge\; s_{ik} + h_i + t_{ij} \;-\; M(1-x_{ijk})
            \quad \forall i\ne j,\; i,j\in \mathcal{N},\; \forall k\in K
            $$

        - **Time window bounds:**

            $$
            e_i \;\le\; s_{ik} \;\le\; l_i
            \quad \forall i\in \mathcal{N},\; \forall k\in K
            $$

        **Interpretation**:
        - If vehicle $k$ travels $i\to j$ ($x_{ijk}=1$), service at $j$ can only start **after** finishing at $i$ and driving $t_{ij}$.
        - **Waiting** happens automatically: if arrival $< e_i$, $s_{ik}$ is **pushed** up to $e_i$.
        - $M$ relaxes the link when $x_{ijk} = 0$; choose any large number for $M$ to deactivate the constraint
        '''
    )

    timeWindowServiceStartSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    completeMIPSlide = sc.create_slide(
        "VRPTW — Complete optimization problem",
        layout_type="side-by-side",
        page_number=15
    )

    completeMIPSlide.content1 = mo.md(
        r'''
        - **Sets & nodes**:  $\mathcal{C}=\{1,\dots,n\}$ (customers), depot $0$, $\mathcal{N}=\{0\}\cup\mathcal{C}$; vehicles $K$  
        - **Data**:  demand $q_i$, service time $h_i$, distance $d_{ij}$ (km), travel time $t_{ij}$ (min), capacity $Q_k$, time windows $[e_i,l_i]$  
        - **Decision variables**:  $x_{ijk}\in\{0,1\}$ (arc $i\!\to\!j$ by vehicle $k$), $s_{ik}\ge 0$ (service start time of $i$ by $k$)

        - **Objective:**

            $$
            \min \sum_{k\in K}\sum_{i\in\mathcal{N}}\sum_{j\in\mathcal{N}} d_{ij}\,x_{ijk}
            $$


        - **Time windows & service start (big-M)**

            $$
            s_{jk} \;\ge\; s_{ik} + h_i + t_{ij} \;-\; M_{ij}\,(1 - x_{ijk})
            \quad \forall\, i\ne j,\; i,j\in\mathcal{N},\; \forall\,k\in K
            $$

            $$
            e_i \le s_{ik} \le l_i \quad \forall\, i\in\mathcal{N},\; \forall\,k\in K
            $$
        '''
    )

    completeMIPSlide.content2 = mo.md(
        r'''
        - **Flow & visit constraints**
            - Each customer visited exactly once:

                $$
                \sum_{k\in K}\sum_{\substack{i\in\mathcal{N}\\ i\ne j}} x_{ijk} = 1 \quad \forall\, j\in\mathcal{C}
                $$

            - Vehicle departures/returns:

                $$
                \sum_{j\in \mathcal{C}} x_{0jk} \le 1,\qquad
                \sum_{i\in \mathcal{C}} x_{i0k} \le 1 \quad \forall\,k\in K
                $$

            - Vehicle flow continuity:

                $$
                \sum_{i\in\mathcal{N}} x_{ijk} - \sum_{i\in\mathcal{N}} x_{jik} = 0
                \quad \forall\, j\in\mathcal{C},\; \forall\, k\in K
                $$

        - **Capacity constraint**

            $$
            \sum_{i\in\mathcal{C}} q_i \sum_{j\in\mathcal{N}} x_{ijk} \;\le\; Q_k
            \quad \forall\, k\in K
            $$
        '''
    )

    completeMIPSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    def vrptw_problem_complexity(n_customers: int, n_vehicles: int) -> dict:
        """
        Count variables and constraints for the VRPTW MIP used in class.
        Assumes a complete directed graph on N = {0} ∪ C (depot + customers),
        variables x_{ijk} (binary) for all i!=j and k, and s_{ik} (continuous).

        Returns a dict with a small breakdown and totals.
        """
        N = n_customers + 1           # |N| (customers + depot)
        arcs = N * (N - 1)            # all ordered pairs i!=j

        # Variables
        x_vars = n_vehicles * arcs
        s_vars = n_vehicles * N
        total_vars = x_vars + s_vars

        return {
            "total_vars": total_vars,
            'x_vars': x_vars,
            's_vars': s_vars
        }


    nCustomersSlider = mo.ui.slider(
        start=0, 
        stop=1000, 
        step=10,
        label='Customers'
    )

    nVehiclesDropdown = mo.ui.dropdown(
        options={"1": 1, "10": 10, "25": 25, "50": 50, "100": 100},
        value='1',
        label="Vehicles"
    )

    try:
        vrp_points  # list of dicts: {"customers": n, "total_vars": v, "k": k}
    except NameError:
        vrp_points = []
    return (
        nCustomersSlider,
        nVehiclesDropdown,
        vrp_points,
        vrptw_problem_complexity,
    )


@app.cell(hide_code=True)
def _(alt, pd, vrp_points, vrptw_problem_complexity):
    def plot_complexity(n,k):
        # Add point if new
        seen = {(p["customers"], p["k"]) for p in vrp_points}
        if (n, k) not in seen:
            size = vrptw_problem_complexity(n_customers=n, n_vehicles=k)
            vrp_points.append({"customers": n, "total_vars": size["total_vars"], "k": str(k)})

        # Plot accumulated points
        df = pd.DataFrame(vrp_points, columns=["customers", "total_vars", "k"])

        chart = (
            alt.Chart(df)
            .mark_point(filled=True, size=50)
            .encode(
                x=alt.X("customers:Q", title="Number of customers (n)"),
                y=alt.Y("total_vars:Q", title="Total number of variables"),
                color=alt.Color("k:N", title="Vehicles (k)"),
                tooltip=[
                    alt.Tooltip("customers:Q", title="Customers (n)"),
                    alt.Tooltip("total_vars:Q", title="Total variables", format=","),
                    alt.Tooltip("k:N", title="Vehicles (k)"),
                ],
            )
            .properties(width=400, height=400, title="Problem size: variables vs. customers")
        )
        return chart
    return (plot_complexity,)


@app.cell(hide_code=True)
def _(mo, nCustomersSlider, nVehiclesDropdown, plot_complexity, sc):
    solvingOverviewSlide = sc.create_slide(
        "Solving VRPTW in practice",
        layout_type="side-by-side",
        page_number=16
    )

    solvingOverviewSlide.content1 = mo.md(
        r"""
    **Why it’s hard (but doable in practice)**  
    - The VRPTW is a **NP-hard** problem: the number of possible tours **explodes** with customers and vehicles.  
    - Time windows & capacities add **tight coupling** between routing and timing.  
    - Exact optimality may be expensive for large, real datasets — but **good solutions** are achievable.
    - Use ```vrptw_problem_complexity``` to calculate the number of decision variables

    **What we can use (toolbox)**  
    - **Exact MIP solvers:** open-source **HiGHS**, CBC; commercial **Gurobi**, CPLEX.  
    - **Heuristic / metaheuristic solvers:** **OR-Tools** (Routing/CP-SAT), savings, local search, Tabu, ALNS.  
    """
    )

    _n = nCustomersSlider.value
    _k = nVehiclesDropdown.value

    complexityChart = plot_complexity(_n,_k)

    _content2 = mo.vstack([
        mo.hstack([nCustomersSlider, nVehiclesDropdown], gap=3, justify='center'),
        complexityChart
    ], gap=2)


    solvingOverviewSlide.content2 = _content2

    solvingOverviewSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    solutionApproachSlide = sc.create_slide(
        "Solution approach (what we actually ran)",
        layout_type="side-by-side",
        page_number=17
    )

    solutionApproachSlide.content1 = mo.md(
        r"""
        **What we solved (overnight main run)**
        - Region: **Fürth depot**, catchment area **50 km**  
        - Data: real pharmacy snapshot + **precomputed** **distance/time** matrices  
        - Model: **VRPTW** (distance-minimizing), constraints as in the MIP slide

        **How we solved it**
        - Solver: **OR-Tools** (routing with time-window feasibility)  
        - Reason: scalable, fast, near-optimal in practice

        **Try it yourself**
        - We provide the full code to solve this problem on GitHub (code + instructions) 
        - Please follow the instructions in our repo (**[Repo link](https://github.com/NikoStein/om_lecture_fulfilment)**) to try it yourself
        """
    )

    solutionApproachSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/deliveryruns.png')

    solutionApproachSlide.render()
    return


@app.cell(hide_code=True)
def _(colorsys, folium, json, plugins, requests):
    def load_scenario(path: str) -> dict:
        """Load a precomputed VRPTW scenario JSON."""
        if path.startswith("http://") or path.startswith("https://"):
            # Load from URL
            response = requests.get(path)
            return json.loads(response.text)
        else:
            # Load from local file
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _generate_colors(n: int) -> list[str]:
        """Generate n visually distinct colors (HSV → hex)."""
        if n <= 1:
            return ["#1f77b4"]
        return [
            "#%02x%02x%02x" % tuple(int(c*255) for c in colorsys.hsv_to_rgb(i/n, 0.9, 0.95))
            for i in range(n)
        ]

    def build_folium_map_from_precomputed(
        scenario: dict,
        depot_lat: float,
        depot_lon: float
    ):
        solution = scenario.get("solution", {})
        routes = solution.get("routes", [])
        vehicles_used = solution.get("vehicles_used", len(routes))
        total_distance_km = solution.get("total_distance_km", 0.0)
        total_time_sec = solution.get("total_time_sec", 0)
        status = solution.get("status", "UNKNOWN")

        if not routes:
            raise ValueError("No routes found in scenario.")

        m = folium.Map(
            location=[depot_lat, depot_lon], 
            zoom_start=11, 
            tiles='OpenStreetMap',
            width=1100,
            height=600
        )


        # folium.TileLayer(
        #     tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        #     attr=('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        #           'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'),
        #     name="CartoDB Light",
        #     overlay=False,
        #     control=True,
        # ).add_to(m)

        folium.Marker(
            [depot_lat, depot_lon],
            popup=folium.Popup("<b>🏭 DEPOT</b><br/>Distribution Center", max_width=200),
            tooltip="Distribution Center",
            icon=folium.Icon(color="red", icon="warehouse", prefix="fa"),
        ).add_to(m)

        colors = _generate_colors(max(vehicles_used, len(routes)))
        plotted = set()

        for r_idx, route in enumerate(routes):
            color = colors[r_idx % len(colors)]
            fg = folium.FeatureGroup(
                name=f"Vehicle {route.get('vehicle', r_idx)} ({max(len(route.get('stops', [])) - 2, 0)} stops)",
                show=False  # <-- start unchecked
            )

            for j, stop in enumerate(route.get("stops", [])):
                if stop.get("is_depot"):
                    continue
                lat, lon = stop["lat"], stop["lon"]
                key = (lat, lon)
                if key in plotted:
                    continue
                arr = int(stop.get("arrival_time", 0))
                hh, mm = arr // 3600, (arr % 3600) // 60
                tstr = f"{hh:02d}:{mm:02d}"
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(
                        f"<b>💊 {stop.get('name','')}</b><br/>"
                        f"Vehicle: {route.get('vehicle', r_idx)}<br/>"
                        f"Stop: {j}<br/>"
                        f"Arrival: {tstr}",
                        max_width=260,
                    ),
                    tooltip=f"{stop.get('name','')} ({tstr})",
                    icon=folium.Icon(color="blue", icon="plus-square", prefix="fa"),
                ).add_to(fg)
                plotted.add(key)

            for seg in route.get("segments", []):
                geom = seg.get("geometry", [])
                if not geom:
                    continue
                pl = folium.PolyLine(
                    locations=geom, color=color, weight=3, opacity=0.7,
                    popup=f"Vehicle {route.get('vehicle', r_idx)}: "
                          f"{seg.get('start',{}).get('name','?')} → {seg.get('end',{}).get('name','?')}"
                ).add_to(fg)
                if len(geom) >= 2:
                    plugins.PolyLineTextPath(
                        pl, "  ►  ", repeat=True, offset=7,
                        attributes={"fill": color, "font-weight": "bold", "font-size": "10"},
                    ).add_to(fg)

            fg.add_to(m)

        folium.LayerControl(collapsed=True).add_to(m)
        return m
    return build_folium_map_from_precomputed, load_scenario


@app.cell(hide_code=True)
def _(
    DEPOT_LAT,
    DEPOT_LON,
    DataURLs,
    build_folium_map_from_precomputed,
    load_scenario,
    mo,
    sc,
):
    resultsBaseSlide = sc.create_slide(
        "What do the optimal routes look like",
        layout_type="1-column",
        page_number=18
    )

    file_path = f"{DataURLs.BASE}/routes/scenario_50_02_10.json"
    scenario_base_case = load_scenario(file_path)
    _m = build_folium_map_from_precomputed(scenario_base_case, DEPOT_LAT, DEPOT_LON)

    # --- LEFT COLUMN: bullets (edit text if needed) ---
    resultsBaseSlide.content1 = mo.vstack(
        [
            mo.hstack(
                [
                    mo.md('Catchment radius: **50 km**'),
                    mo.md('Delivery time window per customer: **2 hours**'),
                    mo.md('Service time per stop: **10 minutes**')
                ]
            ),
            _m
        ]
    )

    resultsBaseSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, pl):
    base_case_data = df_scenarios.filter(
        (pl.col('radius_km') == 50) & (pl.col('client_tw_hours') == 2) & (pl.col('service_time_sec') == 600)
    )

    base_vehicles = base_case_data['vehicles_used'].item()
    base_total_distance_km = base_case_data['total_distance_km'].item()
    base_total_time_min = base_case_data['total_time_sec'].item()/60
    base_total_stops = base_case_data['pharmacies_count'].item()

    avg_dist_per_vehicle = base_total_distance_km/base_vehicles
    avg_time_per_vehicle = base_total_time_min/base_vehicles
    avg_stops_per_vehicle = base_total_stops/base_vehicles

    def _fmt(x, unit=None, nd=1):
        if x is None:
            return "—"
        if isinstance(x, float):
            x = round(x, nd)
        return f"{x}{(' ' + unit) if unit else ''}"

    kpi_rows = [
        {"KPI": "Number of vehicles used", "Base case": _fmt(base_vehicles)},
        {"KPI": "Total distance",          "Base case": _fmt(base_total_distance_km, "km", nd=1)},
        {"KPI": "Total time",              "Base case": _fmt(base_total_time_min, "min", nd=0)},
        {"KPI": "Avg distance / vehicle",  "Base case": _fmt(avg_dist_per_vehicle, "km", nd=1)},
        {"KPI": "Avg tour time / vehicle", "Base case": _fmt(avg_time_per_vehicle, "min", nd=0)},
        {"KPI": "Avg stops / vehicle",     "Base case": _fmt(avg_stops_per_vehicle, nd=1)},
    ]
    return (kpi_rows,)


@app.cell(hide_code=True)
def _(kpi_rows, mo, sc):
    relevantKPISlide = sc.create_slide(
        "Relevant performance indicators",
        layout_type="side-by-side",
        page_number=19
    )

    relevantKPISlide.content1 = mo.md(
        r"""
        To compate different parameter configurations we need a quick way to compare solutions. We can use **K**ey **P**erformance **I**ndicators (KPIs) to get a good summary of our results.

        **KPIs we’ll use**
        - **Vehicles used**: fleet size required to serve all stops
        - **Total distance (km)**: sum of driven kilometers across all routes
        - **Total time (min)**: total driving + service time across all routes
        - **Avg distance per vehicle**: average distance a vehicle has to drive
        - **Avg tour time per vehicle**: average time a vehicle has to drive
        - **Avg stops per vehicle**: average number of pharmacies served per vehicle
        """
    )

    # You can replace the table with KPI tiles later if you prefer
    relevantKPISlide.content2 = mo.vstack(
        [
            mo.md("**Base Case — KPIs**"),
            mo.ui.table(kpi_rows, show_column_summaries=False, show_data_types=False, selection=None)
        ],
        gap=2,
    )

    relevantKPISlide.render()
    return


@app.cell(hide_code=True)
def _(alt, df_scenarios, mo, pl):
    tw_vals = sorted(df_scenarios.select(pl.col("client_tw_hours")).unique().to_series().to_list())
    tw_slider = mo.ui.slider(
        start=min(tw_vals),
        stop=max(tw_vals),
        step=1,
        value=2,  # Default to 2 hours
        label="Time Window Length (hours)"
    )

    kpi_choice = mo.ui.radio(
        options=["Vehicles", "Distance", "Time"],
        value="Vehicles",
        inline=True)



    def plot_kpis(
        df: pl.DataFrame,
        *,
        x_col: str,                   
        x_label: str,                 
        x_min: int,                   
        x_max: int,                   
        tick_step: int = 1,
        width: int = 420,
        height: int = 130,
    ):
        """
        Returns three Altair charts:
          (1) Vehicles used | Avg stops/vehicle
          (2) Total distance | Avg distance/vehicle
          (3) Total time | Avg tour time/vehicle

        Assumes df has columns:
          - vehicles_used, total_distance_km, total_time_min
          - pharmacies_count (or adapt to your stops column)
          - plus the sweep column given in `x_col`
        """

        # Derive averages directly in Polars
        df = df.with_columns(
            (pl.col("total_distance_km") / pl.col("vehicles_used")).alias("avg_distance_per_vehicle"),
            (pl.col("total_time_min") / pl.col("vehicles_used")).alias("avg_tour_time_per_vehicle"),
            (pl.col("pharmacies_count") / pl.col("vehicles_used")).alias("avg_stops_per_vehicle"),
        )

        # Base chart with fixed integer ticks/domain
        base = alt.Chart(df).encode(
            x=alt.X(
                f"{x_col}:Q",
                title=x_label,
                scale=alt.Scale(domain=[x_min, x_max], nice=False),
                axis=alt.Axis(values=list(range(x_min, x_max + 1, tick_step)), tickMinStep=tick_step),
            )
        ).properties(width=width, height=height)

        def _line(y_field: str, title: str, tooltip_fields):
            return (
                base.mark_line(point=True)
                .encode(
                    y=alt.Y(y_field, title=title),
                    tooltip=tooltip_fields,
                )
                .properties(title=title)
            )

        # Build individual charts (tooltips use the generic x_col)
        ch_vehicles = _line(
            "vehicles_used:Q",
            "Vehicles used",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("vehicles_used:Q", title="Vehicles")],
        )

        ch_avg_stops = _line(
            "avg_stops_per_vehicle:Q",
            "Avg stops per vehicle",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("avg_stops_per_vehicle:Q", title="Avg stops/veh", format=".1f")],
        )

        ch_distance = _line(
            "total_distance_km:Q",
            "Total distance (km)",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("total_distance_km:Q", title="Distance (km)", format=".1f")],
        )

        ch_avg_dist = _line(
            "avg_distance_per_vehicle:Q",
            "Avg distance per vehicle (km)",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("avg_distance_per_vehicle:Q", title="Avg dist/veh (km)", format=".1f")],
        )

        ch_time = _line(
            "total_time_min:Q",
            "Total time (min)",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("total_time_min:Q", title="Time (min)", format=".0f")],
        )

        ch_avg_time = _line(
            "avg_tour_time_per_vehicle:Q",
            "Avg tour time per vehicle (min)",
            [alt.Tooltip(f"{x_col}:Q", title=x_label), alt.Tooltip("avg_tour_time_per_vehicle:Q", title="Avg time/veh (min)", format=".0f")],
        )

        pair1 = alt.vconcat(ch_vehicles, ch_avg_stops).resolve_scale(x="shared")
        pair2 = alt.vconcat(ch_distance, ch_avg_dist).resolve_scale(x="shared")
        pair3 = alt.vconcat(ch_time, ch_avg_time).resolve_scale(x="shared")

        return pair1, pair2, pair3
    return kpi_choice, plot_kpis, tw_slider


@app.cell(hide_code=True)
def _(df_scenarios, pl, tw_slider):
    tw_df = (
        df_scenarios
        .filter(
            (pl.col("radius_km") == 50)
            & (pl.col("service_time_sec") == 600)   # 10 minutes
            & (pl.col("client_tw_hours").is_between(2, tw_slider.value, closed="both"))
        )
        .select(
            "client_tw_hours",
            pl.col("vehicles_used"),
            pl.col("total_distance_km"),
            (pl.col("total_time_sec") / 60).alias("total_time_min"),
            pl.col('pharmacies_count')
        )
        .sort("client_tw_hours")
    )
    return (tw_df,)


@app.cell(hide_code=True)
def _(kpi_choice, mo, plot_kpis, sc, tw_df, tw_slider):
    timeWindowSlide = sc.create_slide(
        "Sensitivity — Analyzing the impact of longer delivery time windows",
        layout_type="side-by-side",
        page_number=20
    )

    timeWindowSlide.content1 = mo.vstack(
            [
                mo.md(
                """
                The short delivery windows in the German market seem to be very **restrictive**. By **widening** the windows, planners might gain freedom to combine customers more efficiently.
                """),
                mo.md(
                """
                **Our experiment (sensitivity analysis)**  
                We increase the customer time window stepwise from **2 h → 10 h** and record the KPIs
                This experiment:
                - helps us to judge if a policy (e.g., “2-hour windows”) is **too restrictive**
                - reveals **diminishing returns**: after some width, extra flexibility may bring little benefit
                - supports data-driven negotiation between service quality (tight windows) and **operating cost**
                """
                )
            ]
        )

    tw_vehicles_plot, tw_distance_plot, tw_time_plot = plot_kpis(
        tw_df,
        x_col='client_tw_hours',
        x_label='Time-window length (hours)',
        x_min=2,
        x_max=10
    )

    if kpi_choice.value == 'Vehicles':
        tw_plot = tw_vehicles_plot
    elif kpi_choice.value == 'Distance':
        tw_plot = tw_distance_plot
    else:
        tw_plot = tw_time_plot


    timeWindowSlide.content2 = mo.vstack(
        [
            tw_slider,
            kpi_choice,
            tw_plot
        ],
        gap=2,
    )

    timeWindowSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, mo):
    st_vals = sorted(
        (df_scenarios["service_time_sec"] / 60).unique().to_list()
        if hasattr(df_scenarios, "to_pandas")  # polars DataFrame has .select; above was fine too
        else sorted(df_scenarios["service_time_sec"].unique() / 60)
    )
    st_slider = mo.ui.slider(
        start=int(min(st_vals)),
        stop=int(max(st_vals)),
        step=1,
        value=10,  # default to 10 minutes (base case)
        label="Service Time (minutes)"
    )
    return (st_slider,)


@app.cell(hide_code=True)
def _(df_scenarios, kpi_choice, pl, plot_kpis, st_slider):
    st_df = (
        df_scenarios
        .filter(
            (pl.col("radius_km") == 50) &
            (pl.col("client_tw_hours") == 2) &
            ((pl.col("service_time_sec") / 60).is_between(st_slider.value, 10, closed="both"))
        )
        .select(
            (pl.col("service_time_sec") / 60).alias("service_time_min"),
            pl.col("vehicles_used"),
            pl.col("total_distance_km"),
            (pl.col("total_time_sec") / 60).alias("total_time_min"),
            pl.col("pharmacies_count"),
        )
        .sort("service_time_min")
    )

    st_pair1, st_pair2, st_pair3 = plot_kpis(
        st_df,
        x_col="service_time_min",
        x_label="Service time per stop (minutes)",
        x_min=1,
        x_max=10,
        tick_step=1,
    )


    if kpi_choice.value == "Vehicles":
        st_plot = st_pair1   
    elif kpi_choice.value == "Distance":
        st_plot = st_pair2       
    else:
        st_plot = st_pair3
    return (st_plot,)


@app.cell(hide_code=True)
def _(kpi_choice, mo, sc, st_plot, st_slider):
    serviceTimeSlide = sc.create_slide(
        "Sensitivity — Impact of per-stop service time",
        layout_type="side-by-side",
        page_number=21
    )

    serviceTimeSlide.content1 = mo.vstack(
        [
            mo.md(
                """
                **Why vary service time?**  
                Minutes spent **servicing each stop** add up across a route.  
                Longer service time tightens schedules, increases total minutes,  
                and can require **more vehicles** to meet time windows.
                """
            ),
            mo.md(
                """
                **Our experiment (sensitivity analysis)**  
                We vary the per-stop service time from **1–10 minutes**  
                while holding the radius (**50 km**) and delivery window (**2 h**) fixed,  
                and we track the same KPIs as before.
                """
            ),
        ],
        gap=2,
    )

    serviceTimeSlide.content2 = mo.vstack(
        [
            st_slider,      # your existing slider for service time
            kpi_choice,     # reusing the SAME KPI selector you already have
            st_plot,        # selected two-panel chart
        ],
        gap=2,
    )

    serviceTimeSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, mo, pl):
    ra_vals = (
        df_scenarios
        .select(pl.col("radius_km"))
        .unique()
        .to_series()
        .to_list()
    )
    ra_vals = sorted(ra_vals)
    radius_slider = mo.ui.range_slider(
        start=min(ra_vals),
        stop=max(ra_vals),
        step=5,              # adjust if your data uses a different step
        value=[50,50],            # base case default
        label="Catchment Radius (km)"
    )
    return ra_vals, radius_slider


@app.cell(hide_code=True)
def _(df_scenarios, kpi_choice, pl, plot_kpis, ra_vals, radius_slider):
    ra_df = (
        df_scenarios
        .filter(
            (pl.col("client_tw_hours") == 2) &
            (pl.col("service_time_sec") == 600) &   # 10 minutes
            (pl.col("radius_km").is_between(radius_slider.value[0], radius_slider.value[1], closed="both"))
        )
        .select(
            pl.col("radius_km"),
            pl.col("vehicles_used"),
            pl.col("total_distance_km"),
            (pl.col("total_time_sec") / 60).alias("total_time_min"),
            pl.col("pharmacies_count"),
        )
        .sort("radius_km")
    )

    ra_pair1, ra_pair2, ra_pair3 = plot_kpis(
        ra_df,
        x_col="radius_km",
        x_label="Catchment radius (km)",
        x_min=min(ra_vals),
        x_max=max(ra_vals),
        tick_step=5,
    )

    if kpi_choice.value == "Vehicles":
        ra_plot = ra_pair1
    elif kpi_choice.value == "Distance":
        ra_plot = ra_pair2
    else:
        ra_plot = ra_pair3
    return (ra_plot,)


@app.cell(hide_code=True)
def _(kpi_choice, mo, ra_plot, radius_slider, sc):
    catchmentSlide = sc.create_slide(
        "Sensitivity — Impact of catchment radius",
        layout_type="side-by-side",
        page_number=22
    )

    catchmentSlide.content1 = mo.vstack(
        [
            mo.md(
                """
                **Why vary catchment radius?**  
                A larger radius brings **more customers** into scope but increases average travel.
                Planners trade off **coverage** and **service level** against **distance and time**.
                """
            ),
            mo.md(
                """
                **Our experiment (sensitivity analysis)**  
                We expand the catchment radius stepwise while **holding time-window (2 h)**
                and **service time (10 min)** fixed, and record the same KPIs as before.  
                This shows how geographic scope drives **fleet size**, **distance**, and **total minutes**.
                """
            ),
        ],
        gap=2,
    )

    catchmentSlide.content2 = mo.vstack(
        [
            radius_slider,
            kpi_choice,   # reuses your existing KPI selector
            ra_plot,
        ],
        gap=2,
    )

    catchmentSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, mo, pl):
    x_param_choice = mo.ui.dropdown(
        options=["Time window (h)", "Service time (min)", "Radius (km)"],
        value="Time window (h)",
        label="x-axis"
    )

    y_kpi_choice = mo.ui.dropdown(
        options=["Vehicles", "Distance", "Time"],
        value="Distance",
        label="KPI"
    )

    # Integer domains for clean ticks
    tw_vals_all = sorted(int(v) for v in df_scenarios.select(pl.col("client_tw_hours").cast(pl.Int64)).unique().to_series().to_list())
    st_vals_all = sorted(int(v) for v in df_scenarios.select((pl.col("service_time_sec") // 60).alias("service_time_min")).unique().to_series().to_list())
    ra_vals_all = sorted(int(v) for v in df_scenarios.select(pl.col("radius_km").cast(pl.Int64)).unique().to_series().to_list())

    # Sliders to FIX the two non-x parameters (base-case defaults)
    tw_fix_slider = mo.ui.slider(start=min(tw_vals_all), stop=max(tw_vals_all), step=1, value=2,  label="Time window")
    st_fix_slider = mo.ui.slider(start=min(st_vals_all), stop=max(st_vals_all), step=1, value=10, label="Service time")
    ra_fix_slider = mo.ui.slider(start=min(ra_vals_all), stop=max(ra_vals_all), step=5, value=50, label="Radius")
    return (
        ra_fix_slider,
        st_fix_slider,
        tw_fix_slider,
        x_param_choice,
        y_kpi_choice,
    )


@app.cell(hide_code=True)
def _(
    alt,
    df_scenarios,
    pl,
    ra_fix_slider,
    st_fix_slider,
    tw_fix_slider,
    x_param_choice,
    y_kpi_choice,
):
    df_all = (
        df_scenarios
        .with_columns(
            (pl.col("service_time_sec") // 60).alias("service_time_min"),
            (pl.col("total_time_sec") / 60).alias("total_time_min"),
        )
        .select(
            "client_tw_hours", "service_time_min", "radius_km",
            "vehicles_used", "total_distance_km", "total_time_min", "pharmacies_count"
        )
    )

    axis_key_map = {
        "Time window (h)": "client_tw_hours",
        "Service time (min)": "service_time_min",
        "Radius (km)": "radius_km",
    }
    kpi_field_map = {
        "Vehicles": ("vehicles_used", "Vehicles (count)"),
        "Distance": ("total_distance_km", "Total distance (km)"),
        "Time": ("total_time_min", "Total time (min)"),
    }
    x_title_map = {
        "client_tw_hours": "Time window (hours)",
        "service_time_min": "Service time (min)",
        "radius_km": "Radius (km)",
    }

    x_key = axis_key_map[x_param_choice.value]
    y_field, y_title = kpi_field_map[y_kpi_choice.value]
    x_title = x_title_map[x_key]

    y_max_global = float(df_all.select(pl.max(y_field)).to_series().item())
    y_domain = [0, y_max_global if y_max_global > 0 else 1.0]

    fixed_values = {
        "client_tw_hours": tw_fix_slider.value,
        "service_time_min": st_fix_slider.value,
        "radius_km": ra_fix_slider.value,
    }
    other_keys = [k for k in ["client_tw_hours", "service_time_min", "radius_km"] if k != x_key]
    expr = (pl.col(other_keys[0]) == fixed_values[other_keys[0]]) & (pl.col(other_keys[1]) == fixed_values[other_keys[1]])

    df_line = (
        df_all
        .filter(expr)
        .group_by(x_key)
        .agg(pl.mean(y_field).alias(y_field))
        .sort(x_key)
    )

    x_vals = df_line.select(pl.col(x_key)).to_series().to_list()
    if len(x_vals) == 0:
        x_ticks, x_domain = [], [0, 1]
    else:
        x_min, x_max = int(min(x_vals)), int(max(x_vals))
        x_ticks = list(range(x_min, x_max + 1))
        x_domain = [x_min, x_max]

    line_chart = (
        alt.Chart(df_line)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                f"{x_key}:Q",
                title=x_title,
                scale=alt.Scale(domain=x_domain, nice=False),
                axis=alt.Axis(values=x_ticks, tickMinStep=1),
            ),
            y=alt.Y(
                f"{y_field}:Q",
                title=y_title,
                scale=alt.Scale(domain=y_domain, nice=False),
            ),
            tooltip=[
                alt.Tooltip(f"{x_key}:Q", title=x_title),
                alt.Tooltip(
                    f"{y_field}:Q",
                    title=y_title,
                    format=".1f" if y_field != "vehicles_used" else ""
                ),
            ],
        )
        .properties(width=500, height=300, title=f"{y_title} vs. {x_title}")
    )
    return line_chart, x_key


@app.cell(hide_code=True)
def _(
    line_chart,
    mo,
    ra_fix_slider,
    sc,
    st_fix_slider,
    tw_fix_slider,
    x_key,
    x_param_choice,
    y_kpi_choice,
):
    oneParamSensitivitySlide = sc.create_slide(
        "Sensitivity — One-parameter sweep (line view)",
        layout_type="side-by-side",
        page_number=23
    )

    oneParamSensitivitySlide.content1 = mo.md(
        r"""
        Operations performance depends on **several levers at once** (time windows, service time, radius).
        By simulating different combinations, we can map how these choices jointly affect **fleet size**,
        **kilometers**, and **total minutes**—and identify settings that deliver the **best trade-offs**.

        **What this helps us decide**
        - **Service promise vs. cost:** quantify how stricter delivery windows shift vehicles and time.
        - **Process improvements:** estimate the payoff from shaving minutes off on-site handling.
        - **Coverage policy:** see when expanding the radius stops paying off (diminishing returns).

        **Takeaway**  
        Use these simulations to pick **cost-effective policies** and to set **guardrails**
        (e.g., minimum window length, maximum service time, or radius limits) that keep operations stable.
        """
    )

    if x_key == "client_tw_hours":
        fix_controls = mo.hstack([st_fix_slider, ra_fix_slider], gap=2)
    elif x_key == "service_time_min":
        fix_controls = mo.hstack([tw_fix_slider, ra_fix_slider], gap=2)
    else:  # radius_km on x
        fix_controls = mo.hstack([tw_fix_slider, st_fix_slider], gap=2)

    oneParamSensitivitySlide.content2 = mo.vstack(
        [
            mo.hstack([x_param_choice, y_kpi_choice], gap=2),
            fix_controls,
            line_chart,
        ],
        gap=2,
    )

    oneParamSensitivitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    sessionWrapSlide = sc.create_slide(
        "Session Wrap-Up — VRPTW with Phoenix (Fulfilment)",
        layout_type="side-by-side",
        page_number=24
    )

    sessionWrapSlide.content1 = mo.md(
        r"""
        **What we set out to do**
        - Figure out how Phoenix can **fulfil** customer orders in a **cost-efficient** way
        - Learn how to find **efficient last-mile routes** within a given distribution network

        **What you learned**
        - Translate business rules into a **VRPTW** formulation  
          (objective, flow, capacity, time-window timing)
        - Build a **parameterized dataset** (customers, depot, matrices, fleet) **from realistic data**
        - Read and communicate **KPIs**: vehicles, km, minutes, and per-vehicle averages
        """
    )

    sessionWrapSlide.content2 = mo.vstack(
        [
            mo.md(
                r"""
                **Skills you practiced**
                - Turning an operations narrative into a **formal model**
                - Running **sensitivity analyses** and interpreting KPIs
                """
            ),
            mo.md(
                r"""
                **Takeaways for practice**
                - Start with a **base case**, vary one lever, **hold others fixed**
                - Tie findings to **operational policies** customers **experience** (windows, handling)
                """
            ),
            mo.md(
                r"""
                **What’s next**
                - Add **cost terms** (vehicle start, driver, fuel) to reflect real economics
                - Reproduce the analysis with the repo (class notebook + data + plots)
                """
            ),
        ],
        gap=2,
    )


    sessionWrapSlide.render()
    return


if __name__ == "__main__":
    app.run()
