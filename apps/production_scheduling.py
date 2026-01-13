import marimo

__generated_with = "0.18.0"
app = marimo.App(
    width="medium",
    app_title="Production Scheduling",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    import numpy as np
    import pulp  # For educational purposes (model structure), but we load from cache, don't solve
    import sys
    import os
    import datetime
    from dataclasses import dataclass
    from typing import List, Dict, Optional
    import html
    import json
    import warnings

    try:
        warnings.filterwarnings("ignore")
    except Exception:
        pass
    return Optional, alt, dataclass, html, json, mo, np, os, pd, sys


@app.cell(hide_code=True)
def _(os, sys):
    from pathlib import Path

    GH_USER = "d3group"
    GH_REPO = "OM-lecture"
    BRANCH = "main"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    in_wasm = sys.platform == "emscripten"

    _candidates = [
        Path("apps/public"),
        Path("public"),
        Path("../public"),
    ]
    local_public_dir = next((p for p in _candidates if p.exists() and p.is_dir()), None)
    use_local = (local_public_dir is not None) and not in_wasm

    class DataURLs:
        if use_local:
            BASE = str(local_public_dir)
            CACHE_PATH = f"{BASE}/scheduling_cache.json"
        else:
            BASE = raw_url("apps", "public")
            CACHE_URL = f"{BASE}/scheduling_cache.json"
    return (DataURLs,)


@app.cell(hide_code=True)
def _(Optional, dataclass, html, mo):
    # Slide Infrastructure
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
        logo_url: Optional[str]
        page_number: int
        layout_type: str = "side-by-side"
        subtitle: Optional[str] = None
        content1: Optional[object] = None
        content2: Optional[object] = None

        def _header(self):
            safe_title = html.escape(self.title)
            return mo.Html(
                f"""
                <div class="slide-header">
                  <div class="slide-title" style="font-size: {TITLE_FONT_SIZE}px; font-weight: 700; line-height: 1.2; margin: 0;">{safe_title}</div>
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                </div>
                """
            )

        def _footer(self):
            safe_page = html.escape(str(self.page_number))
            safe_chair = html.escape(self.chair)
            left_html = f"Page {safe_page} &nbsp;&nbsp;|&nbsp;&nbsp; {safe_chair}"
            center_img = (
                f'<img class="slide-logo" src="{html.escape(self.logo_url)}" alt="logo" style="display: block; max-height: 28px; max-width: 160px; margin: 0 auto; object-fit: contain;">'
                if self.logo_url
                else "&nbsp;"
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

        def _title_layout(self):
            safe_title = html.escape(self.title)
            sub = (
                f'<div class="title-slide-sub" style="font-size: 40px; margin: 0 0 16px 0; color: #374151;">{html.escape(self.subtitle)}</div>'
                if self.subtitle
                else ""
            )
            body = mo.Html(
                f"""
                <div class="slide-body title-center" style="flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; height: 100%;">
                  <div class="title-stack" style="text-align: center;">
                    <div class="title-slide-title" style="font-size: 36px; font-weight: 800; margin: 0 0 8px 0;">{safe_title}</div>
                    {sub}
                    <div class="title-slide-meta" style="font-size: 30px; color: #6B7280;">{html.escape(self.course)}</div>
                    <div class="title-slide-meta" style="font-size: 22px; color: #6B7280;">{html.escape(self.presenter)}</div>
                  </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _one_column_layout(self):
            content = (
                mo.md(self.content1)
                if isinstance(self.content1, str)
                else (self.content1 or mo.md(""))
            )
            content_wrapped = mo.vstack([content], gap=0).style(
                {"gap": "0", "margin": "0", "padding": "0"}
            )
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

        def _two_row_layout(self):
            top_content = (
                mo.md(self.content1)
                if isinstance(self.content1, str)
                else (self.content1 or mo.md(""))
            )
            bottom_content = (
                mo.md(self.content2)
                if isinstance(self.content2, str)
                else (self.content2 or mo.md(""))
            )
            top = mo.vstack([top_content], gap=0).style(
                {"gap": "0", "margin": "0", "padding": "0"}
            )
            bottom = mo.vstack([bottom_content], gap=0).style(
                {"gap": "0", "margin": "0", "padding": "0"}
            )
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
                    <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px; display: flex; flex-direction: column; gap: {GAP}px;">
                        {top}
                        {bottom}
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

        def _side_by_side_layout(self):
            left_content = (
                mo.md(self.content1)
                if isinstance(self.content1, str)
                else (self.content1 or mo.md(""))
            )
            right_content = (
                mo.md(self.content2)
                if isinstance(self.content2, str)
                else (self.content2 or mo.md(""))
            )
            left = mo.vstack([left_content], gap=0).style(
                {"gap": "0", "margin": "0", "padding": "0"}
            )
            right = mo.vstack([right_content], gap=0).style(
                {"gap": "0", "margin": "0", "padding": "0"}
            )
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
                        <div class="slide-col.tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
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

        def render(self):
            if self.layout_type == "title":
                return self._title_layout()
            elif self.layout_type == "1-column":
                return self._one_column_layout()
            elif self.layout_type == "2-row":
                return self._two_row_layout()
            return self._side_by_side_layout()

    class SlideCreator:
        def __init__(self, chair, course, presenter, logo_url=None):
            self.chair = chair
            self.course = course
            self.presenter = presenter
            self.logo_url = logo_url
            self._page_counter = 0

        def create_slide(self, title, layout_type="side-by-side"):
            self._page_counter += 1
            return Slide(
                title,
                self.chair,
                self.course,
                self.presenter,
                self.logo_url,
                self._page_counter,
                layout_type=layout_type,
            )

        def create_title_slide(self, title, subtitle=None):
            s = self.create_slide(title, layout_type="title")
            s.subtitle = subtitle
            return s

        def styles(self):
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
                  @media print {{
                    /* Remove all Marimo wrapper margins */
                    marimo-cell, marimo-cell > div, [data-cell-id] {{
                        margin: 0 !important;
                        padding: 0 !important;
                    }}
                    /* Each slide on its own page */
                    div.slide, .slide {{
                        page-break-after: always !important;
                        break-after: page !important;
                        margin: 0 !important;
                    }}
                    div.slide:last-of-type, .slide:last-of-type {{
                        page-break-after: auto !important;
                        break-after: auto !important;
                    }}
                    /* Hide Marimo UI */
                    div[class*="fixed"], button, nav {{
                        display: none !important;
                    }}
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
    return (SlideCreator,)


@app.cell(hide_code=True)
def _(SlideCreator):
    chair = "Chair of Logistics and Quantitative Methods"
    course = "Operations Management"
    presenter = "Richard Pibernik, Anh-Duy Pham"
    logo_url = "https://raw.githubusercontent.com/d3group/.github/refs/heads/main/assets/D3_2c.png"

    sc = SlideCreator(chair, course, presenter, logo_url=logo_url)
    title_slide = sc.create_title_slide("Production Scheduling", "Translating Plans into Shop Floor Schedules")
    return sc, title_slide


@app.cell(hide_code=True)
def _(sc, title_slide):
    sc.styles()
    title_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Introduction: What is Production Scheduling?
    intro_slide = sc.create_slide("What is Production Scheduling?", layout_type="1-column")
    intro_slide.content1 = mo.md("""
    **Production Scheduling** assigns jobs (batches) to specific days and production lines, respecting capacity constraints and optimizing performance objectives.

    ### Key Objectives

    | Objective | Description | Use Case |
    |:----------|:------------|:---------|
    | **Weighted Tardiness** | Minimize total weighted days late | Customer service, priority management |
    | **Makespan** | Minimize completion time of last job | Throughput, resource utilization |
    | **Flow Time** | Minimize average time jobs spend in system | Work-in-process reduction |
    | **Setup Costs** | Minimize changeover time/cost | Efficiency, cost reduction |

    > In this module, we focus on **minimizing weighted tardiness** to balance customer service and product priorities.
    """)
    return (intro_slide,)


@app.cell(hide_code=True)
def _(intro_slide):
    intro_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Inputs: Batches from MPS
    inputs_batches_slide = sc.create_slide("Inputs: Batches from MPS", layout_type="1-column")
    # Calculate totals for display
    total_batches = sum([13, 7, 13, 7, 13, 13, 20, 13])  # 99 batches
    
    inputs_batches_slide.content1 = mo.md(f"""
    For one specific month (say **March**), the Master Production Schedule has already decided:

    $$y_i^{{\\text{{MPS}}}} \\quad \\text{{batches of product }} i \\quad (i = 1, \\dots, 8)$$

    Each of these batches becomes a **"job"** in the scheduling model, indexed as $(i, k)$ where $k = 1, \\dots, y_i^{{\\text{{MPS}}}}$.

    | Product | Batches ($y_i^{{\\text{{MPS}}}}$) | Hours/Batch ($u_i$) |
    |:--------|:----------------------------:|:-------------------:|
    | Amox 500mg | 13 | 8.5 |
    | Amox 875mg | 7 | 9.5 |
    | Amox 1000mg | 13 | 7.5 |
    | Amox/Clav 500/125 | 7 | 8.0 |
    | Amox/Clav 875/125 | 13 | 9.0 |
    | Ampicillin 500mg | 13 | 8.5 |
    | Fluclox 500mg | 20 | 7.0 |
    | Amox 250mg Chew | 13 | 8.0 |

    **Total:** $\\sum_{{i=1}}^{{8}} y_i^{{\\text{{MPS}}}} = {total_batches}$ jobs (batches)
    """)
    return (inputs_batches_slide,)


@app.cell(hide_code=True)
def _(inputs_batches_slide):
    inputs_batches_slide.render()
    return


@app.cell(hide_code=True)
def _(np, pd):
    # Batch counts based on production_planning March demand, scaled to make problem slightly tight
    # Original from MPS: 2, 1, 2, 1, 2, 2, 3, 2 batches (total 15)
    # Scaled proportionally to ~1,600h total work
    # Reduced batch counts to allow some 0-tardiness scenarios
    mps_march_counts = {
        "Amox 500mg (20)": 13,
        "Amox 875mg (10)": 7,
        "Amox 1000mg (14)": 13,
        "Amox/Clav 500/125mg (20)": 7,
        "Amox/Clav 875/125mg (10)": 13,
        "Ampicillin 500mg (20)": 13,
        "Fluclox 500mg (20)": 20,  # Highest demand in production_planning
        "Amox 250mg Chew (20)": 13,
    }  # Total: 99 batches, ~800h

    proc_times = {
        "Amox 500mg (20)": 8.5,
        "Amox 875mg (10)": 9.5,
        "Amox 1000mg (14)": 7.5,
        "Amox/Clav 500/125mg (20)": 8.0,
        "Amox/Clav 875/125mg (10)": 9.0,
        "Ampicillin 500mg (20)": 8.5,
        "Fluclox 500mg (20)": 7.0,
        "Amox 250mg Chew (20)": 8.0,
    }

    priority_weights = {
        "Amox/Clav 875/125mg (10)": 1.3,
        "Amox 875mg (10)": 1.2,
        "Amox/Clav 500/125mg (20)": 1.1,
    }

    np.random.seed(42)

    batches = []
    batch_counter = 0
    for prod, count in mps_march_counts.items():
        for _ in range(count):
            batch_counter += 1
            origin = np.random.choice(["Customer Order", "DC Replenishment"], p=[0.4, 0.6])

            if origin == "Customer Order":
                # Customer orders - balanced due dates (not too tight, not too easy)
                delivery_at_dc = np.random.randint(7, 28)
                pack_qa_buffer = np.random.choice([2, 3])
                ship_buffer = np.random.choice([1, 2])
                due_day = max(1, min(30, delivery_at_dc - pack_qa_buffer - ship_buffer))
            else:
                # DC replenishments - balanced due dates
                reorder_hit = np.random.randint(5, 26)
                pack_qa_buffer = np.random.choice([1, 2])
                due_day = max(1, min(30, reorder_hit - pack_qa_buffer))

            batches.append(
                {
                    "BatchID": f"B{batch_counter:02d}",
                    "Product": prod,
                    "ProcessTime": proc_times.get(prod, 10.0),
                    "DueDay": int(due_day),
                    "Origin": origin,
                    "Priority": float(priority_weights.get(prod, 1.0)),
                }
            )

    df_batches = pd.DataFrame(batches)
    return (df_batches,)


@app.cell(hide_code=True)
def _(mo, sc):
    # Inputs: Processing Times
    inputs_proc_times_slide = sc.create_slide("Inputs: Processing Times", layout_type="1-column")
    inputs_proc_times_slide.content1 = mo.md("""
    Each batch of product $i$ requires $u_i$ hours of processing time on a tablet line.

    **Processing time** ($u_i$) = hours needed to complete one batch of product $i$

    These values come from the MPS data (see previous slide) and typically range from 7-10 hours per batch.

    > **Note:** Processing times are product-specific and determined by batch size and production rate.
    """)
    return (inputs_proc_times_slide,)


@app.cell(hide_code=True)
def _(inputs_proc_times_slide):
    inputs_proc_times_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Inputs: Due Dates
    inputs_due_dates_slide = sc.create_slide("Inputs: Due Dates", layout_type="1-column")
    inputs_due_dates_slide.content1 = mo.md("""
    Each batch $(i,k)$ needs a **due date** $\\text{due}_{i,k}$ inside the month.

    Due dates come from two sources:

    1. **Customer Orders** → delivery date at customer's DC
    2. **DC Replenishment** → when DC hits reorder point

    We use **backward scheduling** to derive the tablet line due date:

    $$\\text{due}_{i,k} = \\text{(downstream requirement)} - \\text{(lead times)}$$

    **Example (Customer Order):** Hospital needs product by day 25 at their DC.
    - Shipping: 2 days → Required at packaging by day 23
    - Packaging/QA: 3 days → **Due at tablet line: Day 20**

    **Example (DC Replenishment):** Fürth DC hits reorder point on day 22.
    - Packaging/QA: 2 days → **Due at tablet line: Day 20**
    """)
    return (inputs_due_dates_slide,)


@app.cell(hide_code=True)
def _(inputs_due_dates_slide):
    inputs_due_dates_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Inputs: Capacity
    inputs_capacity_slide = sc.create_slide("Inputs: Production Capacity", layout_type="1-column")
    inputs_capacity_slide.content1 = mo.md("""
    **30 working days** in the month: $d = 1, \\dots, 30$

    **3 identical tablet lines**: $\\ell = 1, 2, 3$

    Each line has 2×7.5 h + 1×5 h = **20 hours per day**

    | Level | Capacity Calculation |
    |:------|:---------------------|
    | Per line per day | $\\text{Cap}^{\\text{line}} = 20$ h |
    | Site per day | $3 \\times 20 = 60$ h |
    | Full month | $30 \\times 60 = 1{,}800$ h |

    > **Note:** Later in the interactive lab, we can "play" by adjusting capacity to show that planning used a conservative number.
    """)
    return (inputs_capacity_slide,)


@app.cell(hide_code=True)
def _(inputs_capacity_slide):
    inputs_capacity_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, mps_march_counts, proc_times, sc):
    # Inputs: Capacity vs. Requirements
    inputs_capacity_analysis_slide = sc.create_slide("Inputs: Capacity Analysis", layout_type="1-column")
    
    # Calculate total processing time from mps_march_counts and proc_times
    total_proc_time = sum(mps_march_counts[prod] * proc_times[prod] for prod in mps_march_counts)
    # Estimate setup times (assume 2h per product change, 8 products)
    setup_time_per_product = 2.0
    num_products = len(mps_march_counts)
    total_setup_time = setup_time_per_product * num_products
    total_required = total_proc_time + total_setup_time
    
    # Available capacity: 30 days × 3 lines × 20h = 1800h (base capacity from document)
    available_capacity_30d = 30 * 3 * 20
    
    slack_30d = (available_capacity_30d - total_required) / available_capacity_30d * 100
    
    inputs_capacity_analysis_slide.content1 = mo.md(f"""
    ### Total Work Required

    **Processing time:** $\\sum_{{i=1}}^{{8}} \\sum_{{k=1}}^{{y_i^{{\\text{{MPS}}}}}} u_i = {total_proc_time:.1f}$ hours

    **Setup times:** $\\sum_{{i=1}}^{{8}} \\text{{setup}}_i \\approx {total_setup_time:.0f}$ hours (estimated)

    **Total required:** $\\approx {total_required:.1f}$ hours

    ### Available Capacity

    **30 working days:** $30 \\times 3 \\times 20 = {available_capacity_30d}$ hours  
    **Slack:** ${slack_30d:.1f}\\%$

    > With sufficient total capacity, the challenge is **daily scheduling** — fitting jobs to meet due dates while respecting daily line capacity.
    """)
    return (inputs_capacity_analysis_slide,)


@app.cell(hide_code=True)
def _(inputs_capacity_analysis_slide):
    inputs_capacity_analysis_slide.render()
    return


@app.cell(hide_code=True)
def _(df_batches, mo, sc):
    # Inputs: Complete Job List
    inputs_jobs_slide = sc.create_slide("Inputs: Complete Job List", layout_type="1-column")
    jobs_table = df_batches[
        ["BatchID", "Product", "Origin", "ProcessTime", "DueDay", "Priority"]
    ].rename(
        columns={"ProcessTime": "Hours", "DueDay": "Due Day", "Priority": "Weight"}
    )
    inputs_jobs_slide.content1 = mo.vstack([
        mo.md("""Every batch $(i, k)$ has: **due date**, **processing time**, and **priority weight**"""),
        mo.ui.table(jobs_table, selection=None, page_size=10),
    ])
    return (inputs_jobs_slide,)


@app.cell(hide_code=True)
def _(inputs_jobs_slide):
    inputs_jobs_slide.render()
    return


@app.cell(hide_code=True)
def _(alt, df_batches, mo, pd, sc):
    # Gantt Chart: Example Schedule
    gantt_example_slide = sc.create_slide("What Does a Schedule Look Like?", layout_type="1-column")
    
    # Create a simple example schedule for visualization
    # Assign jobs to days and lines (simple round-robin for demo)
    example_schedule = []
    example_days = list(range(1, 25))
    example_lines = ["Line 1", "Line 2", "Line 3"]
    day_idx = 0
    line_idx = 0
    
    for idx, batch_row in df_batches.iterrows():
        example_schedule.append({
            "BatchID": batch_row["BatchID"],
            "Product": batch_row["Product"][:15],  # Shorten for display
            "Day": example_days[day_idx % len(example_days)],
            "Line": example_lines[line_idx % len(example_lines)],
            "ProcessTime": batch_row["ProcessTime"],
            "DueDay": batch_row["DueDay"],
            "Tardiness": max(0, example_days[day_idx % len(example_days)] - batch_row["DueDay"]),
        })
        # Move to next day/line (simple assignment)
        if (idx + 1) % 3 == 0:
            day_idx += 1
        line_idx = (line_idx + 1) % 3
    
    df_example = pd.DataFrame(example_schedule)
    df_example["StartPos"] = df_example["Day"] - 0.4
    df_example["EndPos"] = df_example["Day"] + 0.4
    df_example["LateFlag"] = df_example["Tardiness"] > 0
    
    example_base = alt.Chart(df_example).encode(
        x=alt.X("StartPos:Q", title="Working Day", scale=alt.Scale(domain=[0, 25])),
        x2="EndPos:Q",
        y=alt.Y("Line:N", title="Production Line", sort=["Line 1", "Line 2", "Line 3"]),
        color=alt.Color(
            "Product:N", 
            legend=alt.Legend(title="Product", orient="bottom", columns=4),
            scale=alt.Scale(scheme="tableau10")
        ),
        tooltip=[
            alt.Tooltip("BatchID:N", title="Batch"),
            alt.Tooltip("Product:N", title="Product"),
            alt.Tooltip("Day:Q", title="Scheduled Day"),
            alt.Tooltip("DueDay:Q", title="Due Day"),
            alt.Tooltip("Tardiness:Q", title="Days Late"),
        ],
    )
    
    example_bars = example_base.mark_rect(height=30, cornerRadius=3)
    example_labels = example_base.mark_text(color="white", fontSize=9, fontWeight="bold").encode(text="BatchID:N")
    example_late_outline = (
        example_base.transform_filter("datum.LateFlag == true")
        .mark_rect(height=30, stroke="#dc2626", strokeWidth=2, fillOpacity=0.0, cornerRadius=3)
    )
    
    example_chart = (example_bars + example_labels + example_late_outline).properties(
        title=alt.TitleParams(
            text="Example Production Schedule (Gantt Chart)",
            subtitle="Red outline indicates late jobs",
            fontSize=16,
        ),
        width=900,
        height=180,
    )
    
    gantt_example_slide.content1 = mo.vstack([
        mo.md("""
        A **Gantt chart** visualizes the schedule, showing which jobs run on which days and lines.
        
        This example shows a simple assignment — but is it **optimal**?
        """),
        mo.ui.altair_chart(example_chart),
    ])
    return (gantt_example_slide,)


@app.cell(hide_code=True)
def _(gantt_example_slide):
    gantt_example_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Translate to Model: We Want an Optimized Schedule
    translate_slide = sc.create_slide("From Schedule to Optimization Model", layout_type="1-column")
    translate_slide.content1 = mo.md("""
    The simple schedule shown may not be **optimal**. We need a mathematical model to find the best assignment.

    ### What Makes a Schedule "Good"?

    - **Minimize tardiness:** Jobs completed on or before their due dates
    - **Respect priorities:** High-priority products get scheduled first
    - **Use capacity efficiently:** No line overloads, balanced utilization

    ### The Optimization Approach

    We formulate a **Mixed-Integer Linear Program (MILP)** that:

    1. **Decides:** Which day and line for each batch
    2. **Respects:** Daily capacity constraints per line
    3. **Minimizes:** Total weighted tardiness

    > Next, we'll introduce the mathematical model step by step.
    """)
    return (translate_slide,)


@app.cell(hide_code=True)
def _(translate_slide):
    translate_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model Introduction: The Scheduling Problem
    model_intro_slide = sc.create_slide("The Scheduling Model", layout_type="1-column")
    model_intro_slide.content1 = mo.md("""
    The scheduling model assigns each batch to a **day** and **line**, respecting daily capacity and trying to minimize late completion (tardiness).

    **Given:** Batches from MPS with due dates, processing times, priorities

    **Decide:** Which day and which line for each batch

    **Respect:** Daily capacity per line

    **Minimize:** Total weighted tardiness

    > We'll now build the mathematical model step by step.
    """)
    return (model_intro_slide,)


@app.cell(hide_code=True)
def _(model_intro_slide):
    model_intro_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Sets (Indices)
    model_sets_slide = sc.create_slide("Model: Sets (Indices)", layout_type="1-column")
    model_sets_slide.content1 = mo.md("""
    | Symbol | Range | Description |
    |:------:|:------|:------------|
    | $i$ | $1, \\dots, 8$ | Products |
    | $k$ | $1, \\dots, y_i^{\\text{MPS}}$ | Batches of product $i$ |
    | $d$ | $1, \\dots, 30$ | Days in the month |
    | $\\ell$ | $1, 2, 3$ | Tablet lines |

    > **Note:** A **job** is uniquely identified by $(i, k)$: product $i$, batch number $k$.
    """)
    return (model_sets_slide,)


@app.cell(hide_code=True)
def _(model_sets_slide):
    model_sets_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Parameters
    model_params_slide = sc.create_slide("Model: Parameters", layout_type="1-column")
    model_params_slide.content1 = mo.md("""
    | Symbol | Description |
    |:------:|:------------|
    | $y_i^{\\text{MPS}}$ | Batches of product $i$ (from MPS) |
    | $u_i$ | Processing time (hours/batch) |
    | $\\text{Cap}^{\\text{line}}$ | Hours per line per day (20h) |
    | $\\text{due}_{i,k}$ | Due day for batch $(i,k)$ |
    | $w_i$ | Priority weight ($\\ge 1$) |

    > **Note:** $\\text{due}_{i,k}$ comes from customer orders or DC inventory planning.
    """)
    return (model_params_slide,)


@app.cell(hide_code=True)
def _(model_params_slide):
    model_params_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Decision Variables
    model_vars_slide = sc.create_slide("Model: Decision Variables", layout_type="1-column")
    model_vars_slide.content1 = mo.md("""
    ### Decision Variables

    **Primary Decision Variable:**

    $$x_{i,k,d,\\ell} \\in \\{0, 1\\}$$

    Equals **1** if batch $(i, k)$ is run on line $\\ell$ on day $d$, **0** otherwise.

    **Auxiliary Variables:**

    | Variable | Domain | Description |
    |:--------:|:------:|:------------|
    | $C_{i,k}$ | $\\ge 0$ | Completion day of batch $(i,k)$ |
    | $T_{i,k}$ | $\\ge 0$ | Tardiness of batch $(i,k)$ |

    ### Tardiness Definition

    $$T_{i,k} = \\max(0, \\, C_{i,k} - \\text{due}_{i,k})$$

    - If completed **on time**: $T_{i,k} = 0$
    - If completed **late**: $T_{i,k} =$ days overdue

    > **Early completion has no benefit** — only lateness is penalized.
    """)
    return (model_vars_slide,)


@app.cell(hide_code=True)
def _(model_vars_slide):
    model_vars_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Objective Function
    model_obj_slide = sc.create_slide("Model: Objective Function", layout_type="1-column")
    model_obj_slide.content1 = mo.md("""
    ### Minimize Total Weighted Tardiness

    $$\\min \\; Z = \\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} w_i \\cdot T_{i,k}$$

    **Interpretation:**
    - On-time jobs contribute **zero** to the objective
    - Late jobs contribute $w_i \\times$ (days late)
    - Critical SKUs (high $w_i$) are penalized more → solver prioritizes them
    """)
    return (model_obj_slide,)


@app.cell(hide_code=True)
def _(model_obj_slide):
    model_obj_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Priority Weights
    model_weights_slide = sc.create_slide("Model: Priority Weights", layout_type="1-column")
    model_weights_slide.content1 = mo.md("""
    ### Priority Weights

    $$w_i \\ge 1.0$$

    Weights reflect the **importance** of a product:

    | Product Type | Weight $w_i$ | Why? |
    |:-------------|:------------:|:-----|
    | Standard SKU | 1.0 | Normal priority |
    | High-volume SKU | 1.1 | Revenue impact |
    | Hospital contract | 1.2 | Service level |
    | Critical/shortage | 1.3+ | Urgent need |
    """)
    return (model_weights_slide,)


@app.cell(hide_code=True)
def _(model_weights_slide):
    model_weights_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Priority Weights Example
    model_weights_ex_slide = sc.create_slide("Model: Priority Weights Example", layout_type="1-column")
    model_weights_ex_slide.content1 = mo.md("""
    ### Example: A batch that's 2 days late

    If a job is $T$ days late, its penalty is: $\\text{Penalty} = w_i \\cdot T$

    | Priority | Weight $w_i$ | Penalty |
    |:---------|:------------:|:-------:|
    | Standard | 1.0 | 2.0 |
    | High-volume | 1.1 | 2.2 |
    | Critical | 1.3 | **2.6** |

    > **Higher weight → Larger penalty → Solver prioritizes it!**
    """)
    return (model_weights_ex_slide,)


@app.cell(hide_code=True)
def _(model_weights_ex_slide):
    model_weights_ex_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Constraint 1 - Assignment
    model_const1_slide = sc.create_slide("Model: Constraint 1 - Assignment", layout_type="1-column")
    model_const1_slide.content1 = mo.md("""
    ### Each Batch Scheduled Exactly Once

    $$\\sum_{d=1}^{30} \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} = 1 \\quad \\forall \\, i, \\; k = 1, \\dots, y_i^{\\text{MPS}}$$

    Every batch must be assigned to **exactly one day** and **exactly one line**.
    """)
    return (model_const1_slide,)


@app.cell(hide_code=True)
def _(model_const1_slide):
    model_const1_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Constraint 2 - Capacity
    model_const2_slide = sc.create_slide("Model: Constraint 2 - Capacity", layout_type="1-column")
    model_const2_slide.content1 = mo.md("""
    ### Daily Capacity Per Line

    $$\\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} u_i \\cdot x_{i,k,d,\\ell} \\le \\text{Cap}^{\\text{line}} \\quad \\forall \\, d = 1, \\dots, 30, \\; \\ell = 1, 2, 3$$

    Total processing time on each line per day cannot exceed capacity (default: 20 hours).
    """)
    return (model_const2_slide,)


@app.cell(hide_code=True)
def _(model_const2_slide):
    model_const2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Constraint 3 - Completion Day
    model_const3_slide = sc.create_slide("Model: Constraint 3 - Completion Day", layout_type="1-column")
    model_const3_slide.content1 = mo.md("""
    ### Completion Day Definition

    $$C_{i,k} = \\sum_{d=1}^{30} d \\cdot \\left( \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} \\right) \\quad \\forall \\, i, k$$

    The completion day equals the day on which the batch is scheduled (weighted sum extracts the day).
    """)
    return (model_const3_slide,)


@app.cell(hide_code=True)
def _(model_const3_slide):
    model_const3_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Constraint 4 - Tardiness
    model_const4_slide = sc.create_slide("Model: Constraint 4 - Tardiness", layout_type="1-column")
    model_const4_slide.content1 = mo.md("""
    ### Tardiness Definition

    $$T_{i,k} \\ge C_{i,k} - \\text{due}_{i,k} \\quad \\forall \\, i, k$$

    $$T_{i,k} \\ge 0 \\quad \\forall \\, i, k$$

    Tardiness is at least (completion − due) or zero. The solver minimizes $T_{i,k}$, so it will equal $\\max(0, C_{i,k} - \\text{due}_{i,k})$.
    """)
    return (model_const4_slide,)


@app.cell(hide_code=True)
def _(model_const4_slide):
    model_const4_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Model: Complete Formulation
    model_complete_slide = sc.create_slide("Complete Formulation (MILP)", layout_type="1-column")
    model_complete_slide.content1 = mo.md("""
    **Objective:** Minimize total weighted tardiness

    $$\\min \\; Z = \\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} w_i \\cdot T_{i,k}$$

    **Subject to:**

    | Constraint | Formula |
    |:-----------|:--------|
    | **(1) Assignment** | $\\sum_{d=1}^{30} \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} = 1 \\quad \\forall \\, i, k$ |
    | **(2) Capacity** | $\\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} u_i \\cdot x_{i,k,d,\\ell} \\le \\text{Cap}^{\\text{line}} \\quad \\forall \\, d = 1, \\dots, 30, \\; \\ell = 1, 2, 3$ |
    | **(3) Completion** | $C_{i,k} = \\sum_{d=1}^{30} d \\cdot \\left( \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} \\right) \\quad \\forall \\, i, k$ |
    | **(4) Tardiness** | $T_{i,k} \\ge C_{i,k} - \\text{due}_{i,k}, \\; T_{i,k} \\ge 0 \\quad \\forall \\, i, k$ |

    **Domains:** $x_{i,k,d,\\ell} \\in \\{0, 1\\}, \\quad C_{i,k} \\ge 0, \\quad T_{i,k} \\ge 0$

    *This is a Mixed-Integer Linear Program (MILP) — solved with branch-and-bound algorithms.*
    """)
    return (model_complete_slide,)


@app.cell(hide_code=True)
def _(model_complete_slide):
    model_complete_slide.render()
    return


@app.cell
def _(mo):
    cap_slider = mo.ui.slider(10, 24, step=1, value=20, label="Capacity (h/day)")
    horizon_slider = mo.ui.slider(5, 30, step=1, value=30, label="Days")

    controls = mo.vstack(
        [
            mo.md("**Parameters**"),
            cap_slider,
            horizon_slider,
        ],
        gap=1,
    )
    return cap_slider, controls, horizon_slider


@app.cell
def _(df_batches):
    jobs_df = (
        df_batches[["BatchID", "Product", "Origin", "ProcessTime", "DueDay", "Priority"]]
        .rename(columns={"ProcessTime": "u_i", "DueDay": "due", "Priority": "w_i"})
        .copy()
    )
    jobs_df["due"] = jobs_df["due"].astype(int)
    jobs_df["w_i"] = jobs_df["w_i"].astype(float)
    jobs_df["u_i"] = jobs_df["u_i"].astype(float)
    return (jobs_df,)


@app.cell
async def _(DataURLs, json, os, sys):
    SCHEDULING_CACHE = {}
    cache_loaded = False
    cache_status = "Cache not found. Run: python apps/generate_scheduling_cache.py"

    try:
        if sys.platform == "emscripten":
            import pyodide.http

            url = DataURLs.CACHE_URL
            res = await pyodide.http.pyfetch(url)
            if res.ok:
                SCHEDULING_CACHE = await res.json()
                cache_loaded = True
                cache_status = f"Cache loaded: {len(SCHEDULING_CACHE)} scenarios"
            else:
                cache_status = f"Failed to fetch cache: {res.status}"
        else:
            path = DataURLs.CACHE_PATH
            if os.path.exists(path):
                with open(path, "r") as f:
                    SCHEDULING_CACHE = json.load(f)
                cache_loaded = True
                cache_status = f"Cache loaded: {len(SCHEDULING_CACHE)} scenarios"
            else:
                cache_status = f"Cache file not found at {path}"
    except Exception as exc:
        cache_status = f"Warning: Failed to load cache: {exc}"

    return SCHEDULING_CACHE, cache_loaded, cache_status


@app.cell
def _(
    SCHEDULING_CACHE,
    alt,
    cache_loaded,
    cache_status,
    cap_slider,
    horizon_slider,
    jobs_df,
    mo,
    pd,
):
    cap = int(cap_slider.value)
    days = int(horizon_slider.value)
    lines = 3
    mode = "tard"  # Min weighted tardiness only

    # Capacity analysis
    req_hours = float(jobs_df["u_i"].sum())
    avail_hours = days * lines * cap
    slack_pct = (avail_hours - req_hours) / avail_hours * 100 if avail_hours > 0 else 0

    # Lookup in cache
    key = f"{cap}_{days}_{mode}"
    cache_entry = SCHEDULING_CACHE.get(key) if cache_loaded else None

    if cache_entry:
        status_msg = cache_entry["status"]
        data = cache_entry["data"]
        df_res = pd.DataFrame(data) if data and len(data) > 0 else pd.DataFrame()
    else:
        status_msg = cache_status if not cache_loaded else f"Scenario '{key}' not in cache"
        df_res = pd.DataFrame()

    # Build results
    if df_res.empty:
        # Show status message for infeasible or missing scenarios
        if "Infeasible" in status_msg:
            status_display = mo.callout(
                mo.md(f"**{status_msg}**\n\nTry increasing capacity or extending the horizon."),
                kind="warn"
            )
        else:
            status_display = mo.callout(mo.md(f"**{status_msg}**"), kind="info")

        results_bundle = {
            "kpis": status_display,
            "schedule": mo.md(""),
            "diagnostics": mo.md(f"Required: {req_hours:.0f}h | Available: {avail_hours:.0f}h | Slack: {slack_pct:.1f}%"),
        }
    else:
        total_tard = int(df_res["Tardiness"].sum())
        max_tard = int(df_res["Tardiness"].max())
        late_jobs = int((df_res["Tardiness"] > 0).sum())
        total_jobs = int(len(df_res))

        # KPIs display
        if late_jobs == 0:
            kpi_kind = "success"
            kpi_text = f"✓ **All {total_jobs} jobs on time!**"
        elif late_jobs <= 3:
            kpi_kind = "warn"
            kpi_text = f"⚠ **{late_jobs} of {total_jobs} jobs late** (total tardiness: {total_tard} days)"
        else:
            kpi_kind = "danger"
            kpi_text = f"✗ **{late_jobs} of {total_jobs} jobs late** (total tardiness: {total_tard} days, max: {max_tard})"

        kpis = mo.callout(mo.md(kpi_text), kind=kpi_kind)

        # Schedule Gantt chart - handle multiple jobs per day/line
        dfp = df_res.copy()
        dfp["LateFlag"] = dfp["Tardiness"] > 0

        # Calculate proportional positions within each day
        # Sort by Day, Line, then BatchID for consistent ordering
        dfp = dfp.sort_values(["Day", "Line", "BatchID"]).reset_index(drop=True)

        # Calculate start position within day (as fraction of day)
        start_positions = []
        for _, row in dfp.iterrows():
            same_day_line = dfp[(dfp["Day"] == row["Day"]) & (dfp["Line"] == row["Line"])]
            # Get cumulative hours before this job
            idx_in_group = list(same_day_line["BatchID"]).index(row["BatchID"])
            hours_before = same_day_line.iloc[:idx_in_group]["ProcessTime"].sum()
            total_hours = same_day_line["ProcessTime"].sum()
            # Scale to fit within the day (0 to 1)
            start_frac = hours_before / cap if cap > 0 else 0
            start_positions.append(start_frac)

        dfp["StartPos"] = dfp["Day"] + pd.Series(start_positions).values
        dfp["EndPos"] = dfp["StartPos"] + dfp["ProcessTime"] / cap

        base = alt.Chart(dfp).encode(
            x=alt.X("StartPos:Q", title="Working Day", scale=alt.Scale(domain=[1, days + 1])),
            x2="EndPos:Q",
            y=alt.Y("Line:N", title="Production Line", sort=["Line 1", "Line 2", "Line 3"]),
            color=alt.Color(
                "Product:N", 
                legend=alt.Legend(title="Product", orient="bottom", columns=4),
                scale=alt.Scale(scheme="tableau10")
            ),
            tooltip=[
                alt.Tooltip("BatchID:N", title="Batch"),
                alt.Tooltip("Product:N", title="Product"),
                alt.Tooltip("Day:Q", title="Scheduled Day"),
                alt.Tooltip("DueUsed:Q", title="Due Day"),
                alt.Tooltip("Tardiness:Q", title="Days Late"),
                alt.Tooltip("ProcessTime:Q", title="Hours", format=".1f"),
            ],
        )

        bars = base.mark_rect(height=30, cornerRadius=3)
        labels = base.mark_text(color="white", fontSize=10, fontWeight="bold").encode(text="BatchID:N")

        # Red outline for late jobs
        late_outline = (
            base.transform_filter("datum.LateFlag == true")
            .mark_rect(height=30, stroke="#dc2626", strokeWidth=3, fillOpacity=0.0, cornerRadius=3)
        )

        schedule_chart = (bars + labels + late_outline).properties(
            title=alt.TitleParams(
                text="Production Schedule",
                subtitle="Red outline indicates late jobs" if late_jobs > 0 else "All jobs on time",
                fontSize=16,
            ),
            width=900,
            height=180,
        )

        schedule = mo.ui.altair_chart(schedule_chart)

        diagnostics = mo.md(f"*Capacity: {cap}h/line/day × 3 lines × {days} days = {avail_hours:.0f}h available | {req_hours:.0f}h required | {slack_pct:.1f}% slack*")

        results_bundle = {
            "kpis": kpis,
            "schedule": schedule,
            "diagnostics": diagnostics,
        }
    return (results_bundle,)


@app.cell(hide_code=True)
def _(controls, mo, results_bundle, sc):
    analysis_slide = sc.create_slide("Analysis: Interactive Scheduling Lab", layout_type="1-column")

    lab_intro = mo.md("""
    <div style="background: #f0f9ff; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #0284c7; margin-bottom: 16px;">
    <strong>Experiment:</strong> Adjust capacity and planning horizon to see how the schedule changes. 
    The solver minimizes weighted tardiness — watch how jobs get pushed to later days when capacity is tight!
    </div>
    """)

    analysis_slide.content1 = mo.vstack(
        [
            lab_intro,
            mo.hstack([
                controls,
                mo.vstack([
                    results_bundle["kpis"],
                    results_bundle["diagnostics"],
                ], gap=1),
            ], gap=2, justify="start", align="start"),
            results_bundle["schedule"],
        ],
        gap=2,
    )

    analysis_slide.render()
    return


if __name__ == "__main__":
    app.run()
