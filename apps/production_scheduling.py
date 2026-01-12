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
    import pulp
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
        Path("apps/public/mps"),
        Path("public/mps"),
        Path("../public/mps"),
        Path("public"),
        Path("apps/public"),
    ]
    local_data_dir = next((p for p in _candidates if p.exists() and p.is_dir()), None)
    use_local = (local_data_dir is not None) and not in_wasm

    class DataURLs:
        if use_local:
            BASE = str(local_data_dir)
            IMG_BASE = str(local_data_dir)
            if not os.path.exists(f"{IMG_BASE}/production_image.png"):
                IMG_BASE = (
                    str(local_data_dir.parent)
                    if local_data_dir.name == "mps"
                    else str(local_data_dir)
                )
        else:
            BASE = raw_url("apps", "public", "mps")
            IMG_BASE = "public/mps"
            CACHE_URL = "public/scheduling_cache.json"
    return


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
    # Step 1a: MPS Decides Batches - Intro
    step1a_slide = sc.create_slide("Step 1: MPS Decides How Many Batches", layout_type="1-column")
    step1a_slide.content1 = mo.md("""
    For one specific month (say **March**), the Master Production Schedule has already decided:

    $$y_i^{\\text{MPS}} \\quad \\text{batches of product } i \\quad (i = 1, \\dots, 8)$$

    Each of these batches now becomes a **"job"** in the scheduling model.

    For product $i$ we index the batches $k = 1, \\dots, y_i^{\\text{MPS}}$.
    """)
    return (step1a_slide,)


@app.cell(hide_code=True)
def _(step1a_slide):
    step1a_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 1b: MPS Batch Table
    step1b_slide = sc.create_slide("Step 1: March Batch Plan from MPS", layout_type="1-column")
    step1b_slide.content1 = mo.md("""
    | Product | Batches ($y_i^{\\text{MPS}}$) | Hours/Batch ($u_i$) |
    |:--------|:----------------------------:|:-------------------:|
    | Amox 500mg | 3 | 8.5 |
    | Amox 875mg | 2 | 9.5 |
    | Amox 1000mg | 2 | 7.5 |
    | Amox/Clav 500/125 | 2 | 8.0 |
    | Amox/Clav 875/125 | 2 | 9.0 |
    | Ampicillin 500mg | 2 | 8.5 |
    | Fluclox 500mg | 2 | 7.0 |
    | Amox 250mg Chew | 2 | 8.0 |

    **Total:** $\\sum_{i=1}^{8} y_i^{\\text{MPS}} = 17$ jobs (batches)

    **Total hours:** $\\sum_{i=1}^{8} y_i^{\\text{MPS}} \\cdot u_i \\approx 141$ hours
    """)
    return (step1b_slide,)


@app.cell(hide_code=True)
def _(step1b_slide):
    step1b_slide.render()
    return


@app.cell(hide_code=True)
def _(np, pd):
    mps_march_counts = {
        "Amox 500mg (20)": 3,
        "Amox 875mg (10)": 2,
        "Amox 1000mg (14)": 2,
        "Amox/Clav 500/125mg (20)": 2,
        "Amox/Clav 875/125mg (10)": 2,
        "Ampicillin 500mg (20)": 2,
        "Fluclox 500mg (20)": 2,
        "Amox 250mg Chew (20)": 2,
    }

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
                # Some urgent orders with very tight deadlines
                delivery_at_dc = np.random.randint(4, 10)
                pack_qa_buffer = np.random.choice([2, 3])
                ship_buffer = np.random.choice([1, 2])
                due_day = max(1, min(24, delivery_at_dc - pack_qa_buffer - ship_buffer))
            else:
                # DC replenishments - some very urgent
                reorder_hit = np.random.randint(3, 8)
                pack_qa_buffer = np.random.choice([1, 2])
                due_day = max(1, min(24, reorder_hit - pack_qa_buffer))

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
    # Step 2a: Customer Orders - Intro
    step2a_slide = sc.create_slide("Step 2: Batches Need Due Dates", layout_type="1-column")
    step2a_slide.content1 = mo.md("""
    Each batch $(i,k)$ now needs a **due date** inside the month.

    Due dates come from two sources:

    1. **Customer Orders** → delivery date at customer's DC
    2. **DC Replenishment** → when DC hits reorder point

    We use **backward scheduling** to derive the tablet line due date:

    $$\\text{due}_{i,k} = \\text{(downstream requirement)} - \\text{(lead times)}$$
    """)
    return (step2a_slide,)


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 2a2: Customer Order Example
    step2a2_slide = sc.create_slide("Step 2: Customer-Order Example", layout_type="1-column")
    step2a2_slide.content1 = mo.md("""
    **Example:** A hospital needs product by day 25 at their DC.

    | Stage | Lead Time | Required Complete |
    |:------|:---------:|:-----------------:|
    | Customer DC | - | Day 25 |
    | ← Shipping | 2 days | Day 23 |
    | ← Packaging/QA | 3 days | Day 20 |
    | **Tablet Line** | - | **Due: Day 20** |

    $$\\text{due}_{i,k} = 25 - 2 - 3 = 20$$
    """)
    return (step2a2_slide,)


@app.cell(hide_code=True)
def _(step2a2_slide):
    step2a2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 2b: DC Replenishment Example
    step2b_slide = sc.create_slide("Step 2: DC Replenishment Example", layout_type="1-column")
    step2b_slide.content1 = mo.md("""
    **Example:** **Fürth DC** will hit reorder point for **Fluclox 500mg** on day 22.

    | Stage | Lead Time | Required Complete |
    |:------|:---------:|:-----------------:|
    | DC Reorder Point | - | Day 22 |
    | ← Packaging/QA | 2 days | Day 20 |
    | **Tablet Line** | - | **Due: Day 20** |

    $$\\text{due}_{i,k} = 22 - 2 = 20$$

    ---

    **Summary:** Every batch $(i,k)$ gets a due date $\\text{due}_{i,k} \\in \\{1,\\dots,24\\}$ derived from either a customer order or a DC inventory plan.
    """)
    return (step2b_slide,)


@app.cell(hide_code=True)
def _(step2a_slide):
    step2a_slide.render()
    return


@app.cell(hide_code=True)
def _(step2b_slide):
    step2b_slide.render()
    return


@app.cell(hide_code=True)
def _(df_batches, mo, sc):
    # Step 2c: Complete Job List
    step2c_slide = sc.create_slide("Step 2: The 17 Jobs with Due Dates", layout_type="1-column")
    jobs_table = df_batches[
        ["BatchID", "Product", "Origin", "ProcessTime", "DueDay", "Priority"]
    ].rename(
        columns={"ProcessTime": "Hours", "DueDay": "Due Day", "Priority": "Weight"}
    )
    step2c_slide.content1 = mo.vstack([
        mo.md("""Every batch $(i, k)$ now has: **due date**, **processing time**, and **priority weight**"""),
        mo.ui.table(jobs_table, selection=None, page_size=10),
    ])
    return (step2c_slide,)


@app.cell(hide_code=True)
def _(step2c_slide):
    step2c_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3a: The Scheduling Problem - Intro
    step3a_slide = sc.create_slide("Step 3: The Scheduling Model", layout_type="1-column")
    step3a_slide.content1 = mo.md("""
    The scheduling model assigns each batch to a **day** and **line**, respecting daily capacity and trying to minimize late completion (tardiness).

    **Given:** Batches from MPS with due dates

    **Decide:** Which day and which line for each batch

    **Respect:** Daily capacity per line

    **Minimize:** Total weighted tardiness
    """)
    return (step3a_slide,)


@app.cell(hide_code=True)
def _(step3a_slide):
    step3a_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3a2: Calendar and Capacity
    step3a2_slide = sc.create_slide("Step 3: Calendar and Capacity", layout_type="1-column")
    step3a2_slide.content1 = mo.md("""
    **24 working days** in the month: $d = 1, \\dots, 24$

    **3 identical tablet lines**: $\\ell = 1, 2, 3$

    Each line has 2×7.5 h + 1×5 h = **20 hours per day**

    | Level | Capacity |
    |:------|:--------:|
    | Per line per day | $\\text{Cap}^{\\text{line}} = 20$ h |
    | Site per day | $3 \\times 20 = 60$ h |
    | Full month | $24 \\times 60 = 1{,}440$ h |

    > **Processing time:** $u_i$ = hours per batch of product $i$ (from MPS data)
    """)
    return (step3a2_slide,)


@app.cell(hide_code=True)
def _(step3a2_slide):
    step3a2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3b: Sets (Indices)
    step3b_slide = sc.create_slide("Step 3: Sets (Indices)", layout_type="1-column")
    step3b_slide.content1 = mo.md("""
    | Symbol | Range | Description |
    |:------:|:------|:------------|
    | $i$ | $1, \\dots, 8$ | Products |
    | $k$ | $1, \\dots, y_i^{\\text{MPS}}$ | Batches of product $i$ |
    | $d$ | $1, \\dots, 24$ | Days in the month |
    | $\\ell$ | $1, 2, 3$ | Tablet lines |

    > **Note:** A **job** is uniquely identified by $(i, k)$: product $i$, batch number $k$.
    """)
    return (step3b_slide,)


@app.cell(hide_code=True)
def _(step3b_slide):
    step3b_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3b2: Parameters
    step3b2_slide = sc.create_slide("Step 3: Parameters", layout_type="1-column")
    step3b2_slide.content1 = mo.md("""
    | Symbol | Description |
    |:------:|:------------|
    | $y_i^{\\text{MPS}}$ | Batches of product $i$ (from MPS) |
    | $u_i$ | Processing time (hours/batch) |
    | $\\text{Cap}^{\\text{line}}$ | Hours per line per day (20h) |
    | $\\text{due}_{i,k}$ | Due day for batch $(i,k)$ |
    | $w_i$ | Priority weight ($\\ge 1$) |

    > **Note:** $\\text{due}_{i,k}$ comes from customer orders or DC inventory planning.
    """)
    return (step3b2_slide,)


@app.cell(hide_code=True)
def _(step3b2_slide):
    step3b2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3c: Decision Variables
    step3c_slide = sc.create_slide("Step 3: Decision Variables", layout_type="1-column")
    step3c_slide.content1 = mo.md("""
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
    return (step3c_slide,)


@app.cell(hide_code=True)
def _(step3c_slide):
    step3c_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3d: Objective Function
    step3d_slide = sc.create_slide("Step 3: Objective Function", layout_type="1-column")
    step3d_slide.content1 = mo.md("""
    ### Minimize Total Weighted Tardiness

    $$\\min \\; Z = \\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} w_i \\cdot T_{i,k}$$

    **Interpretation:**
    - On-time jobs contribute **zero** to the objective
    - Late jobs contribute $w_i \\times$ (days late)
    - Critical SKUs (high $w_i$) are penalized more → solver prioritizes them
    """)
    return (step3d_slide,)


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3d2: Priority Weights
    step3d2_slide = sc.create_slide("Step 3: Priority Weights", layout_type="1-column")
    step3d2_slide.content1 = mo.md("""
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
    return (step3d2_slide,)


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3d3: Priority Weights Example
    step3d3_slide = sc.create_slide("Step 3: Priority Weights Example", layout_type="1-column")
    step3d3_slide.content1 = mo.md("""
    ### Example: A batch that's 2 days late

    If a job is $T$ days late, its penalty is: $\\text{Penalty} = w_i \\cdot T$

    | Priority | Weight $w_i$ | Penalty |
    |:---------|:------------:|:-------:|
    | Standard | 1.0 | 2.0 |
    | High-volume | 1.1 | 2.2 |
    | Critical | 1.3 | **2.6** |

    > **Higher weight → Larger penalty → Solver prioritizes it!**
    """)
    return (step3d3_slide,)


@app.cell(hide_code=True)
def _(step3d_slide):
    step3d_slide.render()
    return


@app.cell(hide_code=True)
def _(step3d2_slide):
    step3d2_slide.render()
    return


@app.cell(hide_code=True)
def _(step3d3_slide):
    step3d3_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3e: Constraint 1
    step3e_slide = sc.create_slide("Step 3: Constraint 1 - Assignment", layout_type="1-column")
    step3e_slide.content1 = mo.md("""
    ### Each Batch Scheduled Exactly Once

    $$\\sum_{d=1}^{24} \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} = 1 \\quad \\forall \\, i, \\; k = 1, \\dots, y_i^{\\text{MPS}}$$

    Every batch must be assigned to **exactly one day** and **exactly one line**.
    """)
    return (step3e_slide,)


@app.cell(hide_code=True)
def _(step3e_slide):
    step3e_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3e2: Constraint 2
    step3e2_slide = sc.create_slide("Step 3: Constraint 2 - Capacity", layout_type="1-column")
    step3e2_slide.content1 = mo.md("""
    ### Daily Capacity Per Line

    $$\\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} u_i \\cdot x_{i,k,d,\\ell} \\le \\text{Cap}^{\\text{line}} \\quad \\forall \\, d = 1, \\dots, 24, \\; \\ell = 1, 2, 3$$

    Total processing time on each line per day cannot exceed capacity (default: 20 hours).
    """)
    return (step3e2_slide,)


@app.cell(hide_code=True)
def _(step3e2_slide):
    step3e2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3f: Constraint 3
    step3f_slide = sc.create_slide("Step 3: Constraint 3 - Completion Day", layout_type="1-column")
    step3f_slide.content1 = mo.md("""
    ### Completion Day Definition

    $$C_{i,k} = \\sum_{d=1}^{24} d \\cdot \\left( \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} \\right) \\quad \\forall \\, i, k$$

    The completion day equals the day on which the batch is scheduled (weighted sum extracts the day).
    """)
    return (step3f_slide,)


@app.cell(hide_code=True)
def _(step3f_slide):
    step3f_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3f2: Constraint 4
    step3f2_slide = sc.create_slide("Step 3: Constraint 4 - Tardiness", layout_type="1-column")
    step3f2_slide.content1 = mo.md("""
    ### Tardiness Definition

    $$T_{i,k} \\ge C_{i,k} - \\text{due}_{i,k} \\quad \\forall \\, i, k$$

    $$T_{i,k} \\ge 0 \\quad \\forall \\, i, k$$

    Tardiness is at least (completion − due) or zero. The solver minimizes $T_{i,k}$, so it will equal $\\max(0, C_{i,k} - \\text{due}_{i,k})$.
    """)
    return (step3f2_slide,)


@app.cell(hide_code=True)
def _(step3f2_slide):
    step3f2_slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    # Step 3g: Complete Formulation
    step3g_slide = sc.create_slide("Step 4: Complete Formulation (MILP)", layout_type="1-column")
    step3g_slide.content1 = mo.md("""
    **Objective:** Minimize total weighted tardiness

    $$\\min \\; Z = \\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} w_i \\cdot T_{i,k}$$

    **Subject to:**

    | Constraint | Formula |
    |:-----------|:--------|
    | **(1) Assignment** | $\\sum_{d=1}^{24} \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} = 1 \\quad \\forall \\, i, k$ |
    | **(2) Capacity** | $\\sum_{i=1}^{8} \\sum_{k=1}^{y_i^{\\text{MPS}}} u_i \\cdot x_{i,k,d,\\ell} \\le \\text{Cap}^{\\text{line}} \\quad \\forall \\, d = 1, \\dots, 24, \\; \\ell = 1, 2, 3$ |
    | **(3) Completion** | $C_{i,k} = \\sum_{d=1}^{24} d \\cdot \\left( \\sum_{\\ell=1}^{3} x_{i,k,d,\\ell} \\right) \\quad \\forall \\, i, k$ |
    | **(4) Tardiness** | $T_{i,k} \\ge C_{i,k} - \\text{due}_{i,k}, \\; T_{i,k} \\ge 0 \\quad \\forall \\, i, k$ |

    **Domains:** $x_{i,k,d,\\ell} \\in \\{0, 1\\}, \\quad C_{i,k} \\ge 0, \\quad T_{i,k} \\ge 0$

    *This is a Mixed-Integer Linear Program (MILP) — solved with branch-and-bound algorithms.*
    """)
    return (step3g_slide,)


@app.cell(hide_code=True)
def _(step3g_slide):
    step3g_slide.render()
    return


@app.cell
def _(mo):
    cap_slider = mo.ui.slider(10, 24, step=1, value=20, label="Capacity (h/day)")
    horizon_slider = mo.ui.slider(5, 24, step=1, value=24, label="Days")

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
async def _(json, os, sys):
    import importlib.util

    SCHEDULING_CACHE = {}
    cache_loaded = False
    cache_status = "Cache not found. Run: python apps/generate_scheduling_cache.py"

    if sys.platform == "emscripten":
        # WASM: load JSON via HTTP to avoid local-module imports.
        try:
            import pyodide.http

            url_candidates = [
                "public/scheduling_cache.json",
                "apps/public/scheduling_cache.json",
            ]
            last_status = None
            for url in url_candidates:
                res = await pyodide.http.pyfetch(url)
                last_status = res.status
                if res.ok:
                    SCHEDULING_CACHE = await res.json()
                    cache_loaded = True
                    cache_status = f"Cache loaded: {len(SCHEDULING_CACHE)} scenarios"
                    break
            if not cache_loaded and last_status is not None:
                cache_status = f"Cache fetch failed: {last_status}"
        except Exception as exc:
            cache_status = f"Cache fetch failed: {exc}"
    else:
        # Prefer local JSON to avoid dependency auto-install for local modules.
        base_dir = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
        path_candidates = [
            os.path.join(base_dir, "public", "scheduling_cache.json"),
            os.path.join(base_dir, "..", "public", "scheduling_cache.json"),
            os.path.join(base_dir, "scheduling_cache.json"),
            "apps/public/scheduling_cache.json",
            "public/scheduling_cache.json",
        ]

        for path in path_candidates:
            if os.path.exists(path):
                with open(path, "r") as f:
                    SCHEDULING_CACHE = json.load(f)
                cache_loaded = True
                cache_status = f"Cache loaded: {len(SCHEDULING_CACHE)} scenarios"
                break

        if not cache_loaded:
            module_path = os.path.join(base_dir, "production_scheduling_cache.py")
            if os.path.exists(module_path):
                try:
                    spec = importlib.util.spec_from_file_location(
                        "production_scheduling_cache", module_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        SCHEDULING_CACHE = module.SCHEDULING_CACHE
                        cache_loaded = True
                        cache_status = f"Cache loaded: {len(SCHEDULING_CACHE)} scenarios"
                except Exception as exc:
                    cache_status = f"Cache load failed: {exc}"

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
    step5_slide = sc.create_slide("Step 5: Interactive Scheduling Lab", layout_type="1-column")

    lab_intro = mo.md("""
    <div style="background: #f0f9ff; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #0284c7; margin-bottom: 16px;">
    <strong>Experiment:</strong> Adjust capacity and planning horizon to see how the schedule changes. 
    The solver minimizes weighted tardiness — watch how jobs get pushed to later days when capacity is tight!
    </div>
    """)

    step5_slide.content1 = mo.vstack(
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

    step5_slide.render()
    return


if __name__ == "__main__":
    app.run()
