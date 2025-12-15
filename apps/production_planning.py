import marimo

__generated_with = "0.18.0"
app = marimo.App(
    width="medium",
    app_title="Production Planning and Scheduling",
    layout_file="layouts/production_planning.slides.json",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    import numpy as np
    import pulp
    import math
    import base64
    import textwrap
    import json
    from dataclasses import dataclass
    from typing import Optional, Iterable
    import html
    return Optional, alt, base64, dataclass, html, json, mo, np, pd, pulp


@app.cell(hide_code=True)
def _(np, pulp):
    # PuLP to SciPy solver for WASM compatibility
    # PuLP's CBC solver uses subprocess which doesn't work in WASM,
    # so we convert the PuLP model to scipy format and solve with HiGHS
    from scipy.sparse import coo_matrix
    from scipy.optimize import linprog

    def pulp_to_scipy_linprog(prob):
        """
        Convert a PuLP LP (prob) into the data structures expected by scipy.optimize.linprog.
        """
        variables = [v for v in prob.variables() if v.name != "__dummy"]
        n_vars = len(variables)
        var_index = {v: i for i, v in enumerate(variables)}

        c = np.zeros(n_vars, dtype=float)
        for v, coef in prob.objective.items():
            if v.name == "__dummy":
                continue
            c[var_index[v]] = float(coef)

        constant_offset = float(prob.objective.constant or 0.0)
        if prob.sense == pulp.LpMaximize:
            c = -c
            constant_offset = -constant_offset

        ub_rows, ub_cols, ub_data, b_ub = [], [], [], []
        eq_rows, eq_cols, eq_data, b_eq = [], [], [], []
        ub_count, eq_count = 0, 0

        for constr in prob.constraints.values():
            sense = constr.sense
            const_term = float(constr.constant or 0.0)

            if sense == pulp.LpConstraintLE:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    ub_rows.append(ub_count)
                    ub_cols.append(var_index[v])
                    ub_data.append(float(coef))
                b_ub.append(-const_term)
                ub_count += 1
            elif sense == pulp.LpConstraintGE:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    ub_rows.append(ub_count)
                    ub_cols.append(var_index[v])
                    ub_data.append(-float(coef))
                b_ub.append(const_term)
                ub_count += 1
            elif sense == pulp.LpConstraintEQ:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    eq_rows.append(eq_count)
                    eq_cols.append(var_index[v])
                    eq_data.append(float(coef))
                b_eq.append(-const_term)
                eq_count += 1

        A_ub = coo_matrix((ub_data, (ub_rows, ub_cols)), shape=(ub_count, n_vars)).tocsr() if ub_count > 0 else None
        b_ub = np.array(b_ub, dtype=float) if ub_count > 0 else None
        A_eq = coo_matrix((eq_data, (eq_rows, eq_cols)), shape=(eq_count, n_vars)).tocsr() if eq_count > 0 else None
        b_eq = np.array(b_eq, dtype=float) if eq_count > 0 else None

        bounds = []
        integrality = np.zeros(n_vars, dtype=int)
        for i, v in enumerate(variables):
            lb = float(v.lowBound) if v.lowBound is not None else -np.inf
            ub = float(v.upBound) if v.upBound is not None else np.inf
            bounds.append((lb, ub))
            if v.cat in (pulp.LpInteger, pulp.LpBinary):
                integrality[i] = 1

        return {
            'c': c, 'A_ub': A_ub, 'b_ub': b_ub, 'A_eq': A_eq, 'b_eq': b_eq,
            'bounds': bounds, 'integrality': integrality,
            'constant_offset': constant_offset, 'variables_list': variables,
        }

    def solve_with_scipy(prob):
        """
        Solve a PuLP problem using SciPy's linprog with HiGHS solver.
        Works in WASM where PuLP's CBC solver fails due to subprocess restrictions.
        """
        data = pulp_to_scipy_linprog(prob)
        result = linprog(
            c=data['c'], A_ub=data['A_ub'], b_ub=data['b_ub'],
            A_eq=data['A_eq'], b_eq=data['b_eq'],
            bounds=data['bounds'], integrality=data['integrality'],
            method='highs',
        )

        if result.success:
            for var_obj, xval in zip(data['variables_list'], result.x):
                var_obj.varValue = xval
            obj = result.fun + data['constant_offset']
            if prob.sense == pulp.LpMaximize:
                obj = -obj
            prob.objective_value = obj
            prob.status = pulp.LpStatusOptimal
        else:
            prob.status = pulp.LpStatusNotSolved
        return prob
    return


@app.cell(hide_code=True)
def _(json):
    # Load pre-computed solutions cache for instant WASM performance
    # Cache was generated by utils/generate_production_cache.py
    import os as _os

    _possible_paths = [
        "public/mps/production_cache.json",
        "apps/public/mps/production_cache.json"
    ]
    _cache_path = next((p for p in _possible_paths if _os.path.exists(p)), _possible_paths[0])

    try:
        with open(_cache_path, "r") as _f:
            production_cache = json.load(_f)
    except FileNotFoundError:
        # Fallback: empty cache (will solve on-the-fly)
        production_cache = None
    return (production_cache,)


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
                f'''
                <div class="slide-header">
                  <div class="slide-title" style="font-size: {TITLE_FONT_SIZE}px; font-weight: 700; line-height: 1.2; margin: 0;">{safe_title}</div>
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                </div>
                '''
            )

        def _footer(self):
            safe_page = html.escape(str(self.page_number))
            safe_chair = html.escape(self.chair)
            left_html = f"Page {safe_page} &nbsp;&nbsp;|&nbsp;&nbsp; {safe_chair}"
            center_img = (
                f'<img class="slide-logo" src="{html.escape(self.logo_url)}" alt="logo" style="display: block; max-height: 28px; max-width: 160px; margin: 0 auto; object-fit: contain;">'
                if self.logo_url else "&nbsp;"
            )
            return mo.Html(
                f'''
                <div class="slide-footer">
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                  <div class="slide-footer-row" style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;">
                    <div class="slide-footer-left" style="font-size: {FOOTER_FONT_SIZE}px; color: #6B7280; white-space: nowrap;">{left_html}</div>
                    <div class="slide-footer-center">{center_img}</div>
                    <div class="slide-footer-right">&nbsp;</div>
                  </div>
                </div>
                '''
            )

        def _title_layout(self):
            safe_title = html.escape(self.title)
            sub = f'<div class="title-slide-sub" style="font-size: 40px; margin: 0 0 16px 0; color: #374151;">{html.escape(self.subtitle)}</div>' if self.subtitle else ""
            body = mo.Html(
                f'''
                <div class="slide-body title-center" style="flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; height: 100%;">
                  <div class="title-stack" style="text-align: center;">
                    <div class="title-slide-title" style="font-size: 50px; font-weight: 800; margin: 0 0 8px 0;">{safe_title}</div>
                    {sub}
                    <div class="title-slide-meta" style="font-size: 30px; color: #6B7280;">{html.escape(self.course)}</div>
                    <div class="title-slide-meta" style="font-size: 22px; color: #6B7280;">{html.escape(self.presenter)}</div>
                  </div>
                </div>
                '''
            )
            return mo.Html(
                f'''
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {body}
                  {self._footer()}
                </div>
                '''
            )

        def _one_column_layout(self):
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
                f'''
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                '''
            )

        def _two_row_layout(self):
            top_content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            bottom_content = mo.md(self.content2) if isinstance(self.content2, str) else (self.content2 or mo.md(""))
            top = mo.vstack([top_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            bottom = mo.vstack([bottom_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
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
                f'''
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                '''
            )

        def _side_by_side_layout(self):
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
                f'''
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                '''
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
            return Slide(title, self.chair, self.course, self.presenter, self.logo_url, self._page_counter, layout_type=layout_type)

        def create_title_slide(self, title, subtitle=None):
            s = self.create_slide(title, layout_type="title")
            s.subtitle = subtitle
            return s

        def styles(self):
            return mo.Html(f"""
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
                    margin-bottom: 40px !important;
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
                """)
    return (SlideCreator,)


@app.cell(hide_code=True)
def _(SlideCreator):
    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Operations Management"
    presenter = "Richard Pibernik, Anh-Duy Pham"
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return (sc,)


@app.cell(hide_code=True)
def _(sc):
    titleSlide = sc.create_title_slide("Production Planning", subtitle="")
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    caseExampleSlide = sc.create_slide("Case Example", layout_type="2-row")
    caseExampleSlide.content1 = mo.md(
        r'''
        - Consider a pharmaceutical (contract) manufacturer that makes Amoxicillin-based products for various customers (e.g. Ratiopharm) in one dedicated (beta-lactam) facility
        - Products:
            1. Amoxicillin 500 mg film-coated tablets, box of 20
            2. Amoxicillin 875 mg film-coated tablets, box of 10
            3. Amoxicillin 1000 mg film-coated tablets, box of 14
            4. Amoxicillin / Clavulanic acid 500 mg / 125 mg film-coated tablets, box of 20
            5. Amoxicillin / Clavulanic acid 875 mg / 125 mg film-coated tablets, box of 10
            6. Ampicillin 500 mg hard capsules, box of 20
            7. Flucloxacillin 500 mg hard capsules, box of 20
            8. Amoxicillin 250 mg chewable tablets, box of 20
        '''
    )
    return (caseExampleSlide,)


@app.cell(hide_code=True)
def _(caseExampleSlide):
    caseExampleSlide.render()
    return


@app.cell(hide_code=True)
def _(base64, mo, sc):
    import os
    caseExample2Slide = sc.create_slide("Case Example (2)", layout_type="1-column")

    # Load static image - try multiple paths to handle CWD differences
    possible_paths = [
        "public/mps/production_image.png",
        "apps/public/mps/production_image.png"
    ]
    image_path = next((p for p in possible_paths if os.path.exists(p)), "public/mps/production_image.png")

    with open(image_path, "rb") as f:
        base64_string = base64.b64encode(f.read()).decode("ascii")
    image_url = f"data:image/png;base64,{base64_string}"

    caseExample2Slide.content1 = mo.md(
        f'''\
        \n        <div style="text-align: center;"><img src="{image_url}" style="max-width: 55%; height: auto;" /></div>\
        \n        **In our simplified model, we treat Line 2 (tablet line) as the bottleneck resource.**\
        \n        MPS and scheduling are about deciding which products use how many hours on this line in each period.\
        '''
    )

    caseExample2Slide.render()
    return


@app.cell(hide_code=True)
def _(mo, np, pd, sc):
    # Data Generation
    products_list = [
        "Amox 500mg (20)", "Amox 875mg (10)", "Amox 1000mg (14)", 
        "Amox/Clav 500/125mg (20)", "Amox/Clav 875/125mg (10)",
        "Ampicillin 500mg (20)", "Fluclox 500mg (20)", "Amox 250mg Chew (20)"
    ]
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

    # Reproducible random data
    np.random.seed(42)

    # 1. Demand (D_it): 500-3000 units per month
    _demand_data = np.random.randint(500, 3000, size=(8, 6))
    df_demand = pd.DataFrame(_demand_data, columns=months_list, index=products_list)

    # 2. Capacity Usage (a_i) & Batch Data
    # Hours per unit (box): 0.05 - 0.15
    # Batch Size: e.g., 500 - 2000 boxes
    # Setup Time per batch: e.g., 2.0 - 5.0 hours
    _usage_per_unit = np.round(np.random.uniform(0.05, 0.15, size=8), 3)
    _batch_sizes = (np.random.randint(5, 20, size=8) * 100).astype(int) # 500-2000
    _setup_times = np.round(np.random.uniform(2.0, 5.0, size=8), 1)

    df_usage = pd.DataFrame({
        "Hours/Unit": _usage_per_unit,
        "Batch Size": _batch_sizes,
        "Setup Hours": _setup_times
    }, index=products_list)

    # 3. Bottleneck Capacity (C_t)
    # Calculate total required hours if all demand is met, including crude setup estimation (1 per month)
    _prod_hours = df_demand.values.T @ _usage_per_unit
    _setup_hours_est = np.sum(_setup_times) * 6 # Assume 1 setup per product per month
    _total_required = _prod_hours + (_setup_hours_est / 6) # Spread setup estimate? Or just sum?

    # Actually, let's look at the monthly load.
    # Monthly Prod Load + Sum of all setups (worst case/typical case for tight capacity)
    _monthly_setup_load = np.sum(_setup_times)
    _total_required_monthly = _prod_hours + _monthly_setup_load

    # Make capacity tight: ~average requirement
    _avg_req = np.mean(_total_required_monthly)
    _capacity_val = int(_avg_req * 1.0) 

    # Create the slide
    demandSlide = sc.create_slide("Demand", layout_type="1-column")

    demandSlide.content1 = mo.vstack([
        mo.md(
            r'''
            *   The company has confirmed customer orders and forecasts of (the remaining) demand for the next 6 months. The forecasts come from Demand Planning.
            *   To make life simpler, we do not distinguish between confirmed orders and forecasts, but simply say that we have Demand $D_{it}$ for product $i$ ($i=1,...,8$) in period $t$ ($t=1,...,6$).
            '''
        ),
        mo.ui.table(df_demand, label="Demand $D_{it}$", selection=None)
    ])

    demandSlide.render()
    return df_demand, df_usage, months_list, products_list


@app.cell(hide_code=True)
def _(mo, sc):
    batchSlide = sc.create_slide("Batch Sizes and Lots", layout_type="1-column")

    batchSlide.content1 = mo.md(
        r'''
    **Batch vs. Lot**
    - **Batch:** One *production run* on the line under one batch number (same recipe, equipment, time window — GMP / traceability).
    - **Lot / Lot size:** Planned *quantity* produced in one go. Here: lot size = **batch size $b_i$** (units per batch).

    **From EOQ to Economic Lot Size (ELS)**
    - EOQ trade-off: setup cost $K_i \leftrightarrow$ holding cost $h_i$, demand $D_i$. For product $i$: 
    $$\quad ELS_i = \sqrt{\frac{2 D_i K_i}{h_i}}$$
    - Interpretation: best **lot size** if we only looked at this product alone.
        '''
    )

    batchSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    batchSlide2 = sc.create_slide("Batch Sizes and Lots (2)", layout_type="1-column")

    batchSlide2.content1 = mo.md(
        r'''
    ## Why we don't just use ELS in our pharma example:

    Even if $ELS_i$ is "economically optimal", we must respect:

    - **Capacity:** shared tablet line, campaigns, monthly hours

    - **Technical limits:** min/max batch size determined by equipment

    - **Regulatory limits:** validated batch size ranges (dossier)

    - **Contracts:** customer-specified batch sizes/multiples

    $\rightarrow$ In practice: use $ELS_i$ as a **starting point**, then choose a feasible **batch size $b_i$** satisfying these constraints.
        '''
    )

    batchSlide2.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    inventorySlide = sc.create_slide("Production decisions and inventory over time", layout_type="1-column")

    inventorySlide.content1 = mo.md(
        r'''
    For the moment, let's look at **one product $i$** over time.
    Assume that we are at the end of the month (e.g. January) and want to plan for the next six months (e.g., from February (t=1) to July (t=6)).
    At the end of January we have an inventory of $I_{i0}$, which is also the initial inventory (starting inventory) at the beginning of February (t=1).
    At the start of any month $t$, we have: Inventory from last month: $I_{i,t-1}$

    During month $t$:
    - We produce $y_{it}$ batches
    - Each batch has size $b_i$
    - Total production in units in month $t$: $b_i \cdot y_{it}$

    At the end of month $t$, we get a new inventory position $I_{it}$: $\quad I_{it} = I_{i,t-1} + b_i \cdot y_{it} - D_{it}$

    **Interpretation:**
    If $I_{it} > 0$:  we have **on-hand inventory**
    If $I_{it} < 0$:  we have **backorders** (unmet demand of $-I_{it}$ units)

    *This should be familiar to you – we had a very similar logic in our session on Inventory Planning.*
        '''
    )

    inventorySlide.render()
    return


@app.cell(hide_code=True)
def _(df_demand, df_usage, mo, products_list):
    # Interactive sliders for one product - use first product from generated data
    product_idx = 0
    product_name = products_list[product_idx]
    batch_size = int(df_usage.loc[product_name, "Batch Size"])

    # Calculate "tight" default values - slightly under-produce to create some backorders
    # Get demand for this product
    _demands = df_demand.loc[product_name].tolist()
    # Calculate batches needed to just meet demand (rounded down to cause slight shortage)
    _default_batches = [max(0, int(d / batch_size * 0.9)) for d in _demands]  # 90% of needed

    # Sliders with tight default values
    slider_jan = mo.ui.slider(0, 10, value=_default_batches[0], label="Jan (t=1)", show_value=True)
    slider_feb = mo.ui.slider(0, 10, value=_default_batches[1], label="Feb (t=2)", show_value=True)
    slider_mar = mo.ui.slider(0, 10, value=_default_batches[2], label="Mar (t=3)", show_value=True)
    slider_apr = mo.ui.slider(0, 10, value=_default_batches[3], label="Apr (t=4)", show_value=True)
    slider_may = mo.ui.slider(0, 10, value=_default_batches[4], label="May (t=5)", show_value=True)
    slider_jun = mo.ui.slider(0, 10, value=_default_batches[5], label="Jun (t=6)", show_value=True)
    return (
        batch_size,
        product_name,
        slider_apr,
        slider_feb,
        slider_jan,
        slider_jun,
        slider_mar,
        slider_may,
    )


@app.cell(hide_code=True)
def _(
    alt,
    batch_size,
    df_demand,
    mo,
    months_list,
    pd,
    product_name,
    sc,
    slider_apr,
    slider_feb,
    slider_jan,
    slider_jun,
    slider_mar,
    slider_may,
):
    # Use actual generated data
    _b_i = batch_size
    _I_0 = 200  # Initial inventory (assumption)
    _demand = df_demand.loc[product_name].tolist()  # Get demand for this product

    # Get batch counts
    _y = [slider_jan.value, slider_feb.value, slider_mar.value, 
          slider_apr.value, slider_may.value, slider_jun.value]

    # Compute inventory
    _inventory = []
    _I_prev = _I_0
    for t in range(6):
        _I_t = _I_prev + _b_i * _y[t] - _demand[t]
        _inventory.append(_I_t)
        _I_prev = _I_t

    # DataFrame
    df = pd.DataFrame({
        "Month": months_list,
        "Demand": _demand,
        "Batches (y)": _y,
        "Production": [_b_i * y for y in _y],
        "Inventory": _inventory
    })
    df["On-Hand"] = df["Inventory"].apply(lambda x: max(0, x))
    df["Backorders"] = df["Inventory"].apply(lambda x: max(0, -x))

    total_backorders = int(df["Backorders"].sum())
    total_holding = int(df["On-Hand"].sum())

    # Simple stacked bar chart - melt data for Altair
    _chart_df = df[["Month", "On-Hand", "Backorders"]].melt(
        id_vars=["Month"], 
        var_name="Type", 
        value_name="Units"
    )

    _chart = alt.Chart(_chart_df).mark_bar().encode(
        x=alt.X("Month:N", sort=months_list, title="Month"),
        y=alt.Y("Units:Q", title="Units"),
        color=alt.Color("Type:N", 
            scale=alt.Scale(domain=["On-Hand", "Backorders"], range=["#22c55e", "#ef4444"]),
            legend=alt.Legend(title="Status", orient="top")
        ),
        xOffset="Type:N",
        tooltip=["Month", "Type", "Units"]
    ).properties(width=400, height=220)

    # Slide with 2-row layout
    interactiveSlide = sc.create_slide("Interactive: Single-Product MPS", layout_type="2-row")

    interactiveSlide.content1 = mo.vstack([
        mo.md(f'''**Product:** {product_name} | **Batch Size:** {_b_i} units | **Initial Inventory:** {_I_0} units'''),
        mo.md("**Set number of batches per month:**"),
        mo.hstack([
            mo.vstack([mo.md("**Jan**"), slider_jan], align="center"),
            mo.vstack([mo.md("**Feb**"), slider_feb], align="center"),
            mo.vstack([mo.md("**Mar**"), slider_mar], align="center"),
            mo.vstack([mo.md("**Apr**"), slider_apr], align="center"),
            mo.vstack([mo.md("**May**"), slider_may], align="center"),
            mo.vstack([mo.md("**Jun**"), slider_jun], align="center"),
        ], justify="center", gap=1),
    ], gap=0.3)

    interactiveSlide.content2 = mo.hstack([
        mo.ui.altair_chart(_chart),
        mo.callout(
            mo.md(f'''
    **Results:**

    🟢 **On-Hand:** {total_holding:,} units

    🔴 **Backorders:** {total_backorders:,} units
            '''),
            kind="info"
        )
    ], justify="center", gap=2)

    interactiveSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    objectiveSlide1 = sc.create_slide("The overall objective (1)", layout_type="1-column")

    objectiveSlide1.content1 = mo.md(
        r'''
    We continue with **one product $i$** over the planning horizon $t = 1, \ldots, 6$.

    From the previous slide, we know that the batch decisions $y_{it}$ determine the inventory positions:
    $$I_{it} = I_{i,t-1} + b_i \cdot y_{it} - D_{it}$$

    Now we assign **costs** to these inventory positions.

    **Cost parameters**
    - $h_i$: holding cost per unit of **positive inventory** per month
    - $p_i$: penalty cost per unit of **backorders** (negative inventory) per month
        '''
    )

    objectiveSlide1.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    objectiveSlide2 = sc.create_slide("The overall objective (2)", layout_type="1-column")

    objectiveSlide2.content1 = mo.md(
        r'''
    **Cost in month $t$**
    - If $I_{it} > 0$: we hold inventory and pay $\quad C_{it} = h_i \cdot I_{it}$
    - If $I_{it} < 0$: we have backorders of $-I_{it}$ units and pay $\quad C_{it} = p_i \cdot (-I_{it})$

    Like in Chapter 3 (Inventory Planning), we can write the monthly cost as a function of the inventory position:
    $$C_{it}(I_{it}) = \begin{cases} h_i \, I_{it} & \text{if } I_{it} \geq 0 \\ p_i \, (-I_{it}) & \text{if } I_{it} < 0 \end{cases}$$

    **Total cost over the 6 months and all 8 products**
    $$\text{Total cost} = \sum_{t=1}^{6}\sum_{i=1}^{8}  C_{it}(I_{it})$$
        '''
    )

    objectiveSlide2.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    capacitySlide1 = sc.create_slide("Capacity constraints (1)", layout_type="1-column")

    capacitySlide1.content1 = mo.md(
        r'''
    We now look at the **bottleneck resource**: the shared tablet line (compression + coating) in our beta-lactam block.

    For each month $t$:
    - The line has a **limited number of hours** available:
      - $Cap_t$: available capacity in hours per month
    - For each product $i$:
      - We produce $y_{it}$ batches
      - Each batch of product $i$ needs $u_i$ hours of **run time** on the line
      - If we produce product $i$ at all in month $t$ (i.e. $z_{it} = 1$), we also need $st_i$ hours of **setup / cleaning** time
        '''
    )

    capacitySlide1.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    capacitySlide2 = sc.create_slide("Capacity constraints (2)", layout_type="1-column")

    capacitySlide2.content1 = mo.md(
        r'''
    Total time used on the line in month $t$:
    $$\sum_{i=1}^{8} \left( u_i \, y_{it} + st_i \, z_{it} \right)$$

    This must not exceed the available capacity:
    $$\sum_{i=1}^{8} \left( u_i \, y_{it} + st_i \, z_{it} \right) \leq Cap_t, \quad \forall t$$

    **Key message:**
    The batch decisions $y_{it}$ and the choice of which products to run $z_{it}$ are limited by the **shared line capacity**.
        '''
    )

    capacitySlide2.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    moreConstraintsSlide = sc.create_slide("More constraints....", layout_type="1-column")

    moreConstraintsSlide.content1 = mo.md(
        r'''
    We only have a setup (and we only incur the corresponding setup time) if we actually produce the product in that month.

    $$y_{it} \leq M_i \, z_{it}, \quad \forall i, t$$

    - If $z_{it} = 0 \rightarrow y_{it} \leq 0 \rightarrow$ no batches
    - If $z_{it} = 1 \rightarrow$ up to $M_i$ batches are allowed (limited in practice by capacity)

    ---

    **Variable domains**

    $$y_{it} \in \mathbb{Z}_{\geq 0}, \qquad z_{it} \in \{0, 1\}, \qquad I_{it} \in \mathbb{R}, \quad \forall i, t$$

    - $y_{it}$: non-negative integer number of batches
    - $z_{it}$: binary setup
    - $I_{it}$: inventory position (may be positive or negative)
        '''
    )

    moreConstraintsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    overallModelSlide = sc.create_slide("The overall model...", layout_type="1-column")

    overallModelSlide.content1 = mo.md(
        r'''
    $$\min Z = \sum_{i=1}^{8} \sum_{t=1}^{6} C_{it}(I_{it})$$

    $$C_{it}(I_{it}) = \begin{cases} h_i I_{it}, & I_{it} \geq 0 \\ p_i (-I_{it}), & I_{it} < 0 \end{cases}$$

    s.t.

    $$I_{it} = I_{i,t-1} + b_i y_{it} - D_{it} \quad \forall i, t$$

    $$\sum_{i=1}^{8} (u_i y_{it} + st_i z_{it}) \leq Cap_t \quad \forall t$$

    $$y_{it} \leq M_i z_{it} \quad \forall i, t$$

    $$y_{it} \in \mathbb{Z}_{\geq 0}, \quad z_{it} \in \{0, 1\}, \quad I_{it} \in \mathbb{R} \quad \forall i, t$$
        '''
    )

    overallModelSlide.render()
    return


@app.cell
def _(
    df_demand,
    df_usage,
    months_list,
    pd,
    production_cache,
    products_list,
    pulp,
):
    # ===== Model Configuration (for display) =====
    # Cost parameters
    _holding_cost = {_p: 0.5 for _p in products_list}  # h_i: $/unit/month
    _penalty_cost = {_p: 5.0 for _p in products_list}  # p_i: $/unit/month

    # Batch sizes from data
    _batch_sizes = df_usage["Batch Size"].to_dict()  # b_i

    # Run time per batch: u_i = Hours/Unit * Batch Size
    _run_time_per_batch = {_p: df_usage.loc[_p, "Hours/Unit"] * df_usage.loc[_p, "Batch Size"] 
                          for _p in products_list}  # u_i
    _setup_times = df_usage["Setup Hours"].to_dict()  # st_i

    # Capacity and initial inventory
    capacity_val = 1500  # Cap_t: hours per month
    init_inv = 200  # Same for all products
    _M = {_p: 20 for _p in products_list}  # Big-M for setup linking

    # ===== PuLP Model Definition (shown for educational purposes) =====
    # NOTE: We define the model structure but load pre-computed results from cache
    _model = pulp.LpProblem("ProductionPlanning", pulp.LpMinimize)

    # Decision variables
    _y = pulp.LpVariable.dicts("y", (products_list, months_list), lowBound=0, cat='Integer')  # batches
    _z = pulp.LpVariable.dicts("z", (products_list, months_list), cat='Binary')  # setup indicator
    _I_plus = pulp.LpVariable.dicts("I_plus", (products_list, months_list), lowBound=0)  # positive inventory
    _I_minus = pulp.LpVariable.dicts("I_minus", (products_list, months_list), lowBound=0)  # backorders

    # Objective: minimize total cost
    _model += pulp.lpSum(
        _holding_cost[_p] * _I_plus[_p][_t] + _penalty_cost[_p] * _I_minus[_p][_t]
        for _p in products_list for _t in months_list
    )

    # Constraints
    _I_0 = {_p: init_inv for _p in products_list}
    for _p in products_list:
        for _t_idx, _t in enumerate(months_list):
            _prev_inv = _I_0[_p] if _t_idx == 0 else (_I_plus[_p][months_list[_t_idx-1]] - _I_minus[_p][months_list[_t_idx-1]])
            _demand = df_demand.loc[_p, _t]
            _production = _batch_sizes[_p] * _y[_p][_t]
            _model += _I_plus[_p][_t] - _I_minus[_p][_t] == _prev_inv + _production - _demand, f"InvBal_{_p}_{_t}"
            _model += _y[_p][_t] <= _M[_p] * _z[_p][_t], f"Setup_{_p}_{_t}"

    for _t in months_list:
        _model += pulp.lpSum(
            _run_time_per_batch[_p] * _y[_p][_t] + _setup_times[_p] * _z[_p][_t]
            for _p in products_list
        ) <= capacity_val, f"Cap_{_t}"

    # ===== Load pre-computed solution from cache (instant!) =====
    # Use capacity=1500 solution for consistency with sensitivity sliders at default values
    _cached = production_cache["capacity"].get("1500") if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        _sol_data = [{"Product": _p[:15], **{f"y_{_t}": _cached["solution"][_p][_t] for _t in months_list}} for _p in products_list]
        _inv_data = [{"Product": _p[:15], **{f"I_{_t}": _cached["inventory"][_p][_t] for _t in months_list}} for _p in products_list]
        df_solution = pd.DataFrame(_sol_data)
        df_inventory = pd.DataFrame(_inv_data)
        total_cost = _cached["total_cost"]
        status_msg = f"**Optimal solution found!** Total Cost = **${total_cost:,.0f}**"
    else:
        df_solution = pd.DataFrame({"Status": ["No cached solution found"]})
        df_inventory = pd.DataFrame()
        status_msg = "**No cached solution found**"
        total_cost = None
    return capacity_val, init_inv, status_msg


@app.cell(hide_code=True)
def _(mo, sc):
    # === SLIDE: Cost Parameters ===
    costSlide = sc.create_slide("Parameters: Costs", layout_type="1-column")

    costSlide.content1 = mo.md('''
    **Holding Cost** $h_i$: Cost per unit of positive inventory per month
    - $h_i = 0.50$ $/unit/month

    **Penalty Cost** $p_i$: Cost per unit of backorder per month  
    - $p_i = 5.00$ $/unit/month

    *Note: Backorders are 10× more expensive than holding inventory!*
    ''')

    costSlide.render()
    return


@app.cell(hide_code=True)
def _(capacity_val, init_inv, mo, sc):
    # === SLIDE: Capacity & Initial Inventory ===
    capSlide = sc.create_slide("Parameters: Capacity & Inventory", layout_type="1-column")

    capSlide.content1 = mo.md(f'''
    **Monthly Capacity** $Cap_t$: Available hours on the bottleneck line
    - $Cap_t = {capacity_val}$ hours/month (same for all months)

    **Initial Inventory** $I_{{i0}}$: Starting inventory at $t=0$
    - $I_{{i0}} = {init_inv}$ units for each product
    ''')

    capSlide.render()
    return


@app.cell(hide_code=True)
def _(df_usage, mo, sc):
    # === SLIDE: Product Data ===
    prodDataSlide = sc.create_slide("Parameters: Product Data", layout_type="1-column")

    prodDataSlide.content1 = mo.vstack([
        mo.md('''**Product-Specific Parameters:**
    - **Hours/Unit** $u_i$: Processing time per unit (boxes)
    - **Batch Size** $b_i$: Units per batch
    - **Setup Hours** $st_i$: Time for setup/cleaning per production run'''),
        mo.ui.table(df_usage, selection=None)
    ], gap=0.5)

    prodDataSlide.render()
    return


@app.cell(hide_code=True)
def _(
    alt,
    df_demand,
    df_usage,
    mo,
    months_list,
    pd,
    production_cache,
    products_list,
    sc,
    status_msg,
):
    # === SLIDE: Optimal Solution with Faceted Visualization ===

    # Build comprehensive data for visualization
    _cached = production_cache["capacity"].get("1500") if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        # Build data for all products
        _viz_rows = []
        for _p in products_list:
            _batch_size = df_usage.loc[_p, "Batch Size"]
            for _t in months_list:
                _batches = _cached["solution"][_p][_t]
                _production = _batches * _batch_size
                _demand = df_demand.loc[_p, _t]
                _inventory = _cached["inventory"][_p][_t]
                _viz_rows.append({
                    "Product": _p[:12], "Month": _t,
                    "Production": _production, "Demand": _demand,
                    "On-Hand": max(0, _inventory), "Backorders": max(0, -_inventory)
                })

        _viz_df = pd.DataFrame(_viz_rows)
        _viz_long = _viz_df.melt(id_vars=["Product", "Month"], value_vars=["Production", "Demand", "On-Hand", "Backorders"], var_name="Metric", value_name="Units")

        # Split products into two groups for side-by-side display
        _products_left = [p[:12] for p in products_list[:4]]
        _products_right = [p[:12] for p in products_list[4:]]

        _legend_str = mo.md(
            """
            <span style='color:#3b82f6'><b>━ Production</b></span> &nbsp;
            <span style='color:#8b5cf6'><b>━ Demand</b></span> &nbsp;
            <span style='color:#22c55e'><b>-- On-Hand</b></span> &nbsp;
            <span style='color:#ef4444'><b>-- Backorders</b></span>
            """
        )

        def _make_chart(data, show_legend=False):
            _lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
                x=alt.X("Month:N", sort=months_list, title=None), y=alt.Y("Units:Q", title="Units"),
                color=alt.Color("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=["#3b82f6", "#8b5cf6", "#22c55e", "#ef4444"]), legend=None),
                strokeDash=alt.StrokeDash("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=[[0], [0], [4, 2], [4, 2]]), legend=None)
            )
            _points = alt.Chart(data).mark_circle(size=30).encode(x=alt.X("Month:N", sort=months_list), y=alt.Y("Units:Q"), color=alt.Color("Metric:N", legend=None), tooltip=["Product", "Month", "Metric", "Units"])
            return (_lines + _points).properties(width=360, height=75).facet(row=alt.Row("Product:N", title=None, header=alt.Header(labelFontSize=11, labelFontWeight="bold")))

        _chart_left = _make_chart(_viz_long[_viz_long["Product"].isin(_products_left)], show_legend=False)
        _chart_right = _make_chart(_viz_long[_viz_long["Product"].isin(_products_right)], show_legend=False)

        solutionSlide = sc.create_slide("Optimal Solution", layout_type="2-column")
        # Left column: Status + Left Chart
        solutionSlide.content1 = mo.vstack([
            mo.md(f"{status_msg}"),
            mo.ui.altair_chart(_chart_left)
        ], gap=0.5)
        # Right column: Legend + Right Chart
        solutionSlide.content2 = mo.vstack([
            _legend_str,
            mo.ui.altair_chart(_chart_right)
        ], gap=0.5)
    else:
        solutionSlide = sc.create_slide("Optimal Solution", layout_type="1-column")
        solutionSlide.content1 = mo.md("**No cached solution found**")

    solutionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    # Slider for sensitivity analysis
    capacity_slider = mo.ui.slider(800, 2500, value=1500, step=100, label="Capacity (hours/month)", show_value=True)
    return (capacity_slider,)


@app.cell(hide_code=True)
def _(
    alt,
    capacity_slider,
    df_demand,
    df_usage,
    mo,
    months_list,
    pd,
    production_cache,
    products_list,
    sc,
):
    # Load solution from cache (instant!) instead of solving
    _cap_val = capacity_slider.value
    _cached = production_cache["capacity"].get(str(_cap_val)) if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        _total_cost = _cached["total_cost"]
        _total_backorders = _cached["total_backorders"]
        _total_holding = _cached["total_holding"]
        _status = f"✅ Cost: **${_total_cost:,.0f}** | Backorders: **{_total_backorders:,.0f}** | On-Hand: **{_total_holding:,.0f}**"

        # Build visualization data
        _viz_rows = []
        for _p in products_list:
            _batch_size = df_usage.loc[_p, "Batch Size"]
            for _t in months_list:
                _batches = _cached["solution"][_p][_t]
                _production = _batches * _batch_size
                _demand = df_demand.loc[_p, _t]
                _inventory = _cached["inventory"][_p][_t]
                _viz_rows.append({"Product": _p[:12], "Month": _t, "Production": _production, "Demand": _demand, "On-Hand": max(0, _inventory), "Backorders": max(0, -_inventory)})
        _viz_df = pd.DataFrame(_viz_rows)
        _viz_long = _viz_df.melt(id_vars=["Product", "Month"], value_vars=["Production", "Demand", "On-Hand", "Backorders"], var_name="Metric", value_name="Units")

        _products_left = [p[:12] for p in products_list[:4]]
        _products_right = [p[:12] for p in products_list[4:]]

        _legend_str = mo.md(
            """
            <span style='color:#3b82f6'><b>━ Production</b></span> &nbsp;
            <span style='color:#8b5cf6'><b>━ Demand</b></span> &nbsp;
            <span style='color:#22c55e'><b>-- On-Hand</b></span> &nbsp;
            <span style='color:#ef4444'><b>-- Backorders</b></span>
            """
        )

        def _make_chart(data, show_legend=False):
            _lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
                x=alt.X("Month:N", sort=months_list, title=None), y=alt.Y("Units:Q", title="Units"),
                color=alt.Color("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=["#3b82f6", "#8b5cf6", "#22c55e", "#ef4444"]), legend=None),
                strokeDash=alt.StrokeDash("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=[[0], [0], [4, 2], [4, 2]]), legend=None)
            )
            _points = alt.Chart(data).mark_circle(size=30).encode(x=alt.X("Month:N", sort=months_list), y=alt.Y("Units:Q"), color=alt.Color("Metric:N", legend=None), tooltip=["Product", "Month", "Metric", "Units"])
            return (_lines + _points).properties(width=360, height=75).facet(row=alt.Row("Product:N", title=None, header=alt.Header(labelFontSize=11, labelFontWeight="bold")))

        _chart_left = _make_chart(_viz_long[_viz_long["Product"].isin(_products_left)], False)
        _chart_right = _make_chart(_viz_long[_viz_long["Product"].isin(_products_right)], False)

        sensitivitySlide = sc.create_slide("Sensitivity: Capacity", layout_type="2-column")
        # Left: Slider + Chart
        sensitivitySlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Capacity $Cap_t$:**"), capacity_slider], justify="start", gap=1),
            mo.md("&nbsp;"),
            mo.ui.altair_chart(_chart_left)
        ], gap=0.3)
        # Right: Status + Legend + Chart
        sensitivitySlide.content2 = mo.vstack([
            mo.md(f"**Result:** {_status}"),
            _legend_str,
            mo.ui.altair_chart(_chart_right)
        ], gap=0.3)
    else:
        sensitivitySlide = sc.create_slide("Sensitivity: Capacity", layout_type="1-column")
        sensitivitySlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Capacity $Cap_t$:**"), capacity_slider], justify="start", gap=1),
            mo.md("❌ No cached solution found")
        ], gap=0.3)

    sensitivitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    # Slider for penalty cost sensitivity
    penalty_slider = mo.ui.slider(1.0, 20.0, value=5.0, step=0.5, label="Penalty Cost ($/unit/mo)", show_value=True)
    return (penalty_slider,)


@app.cell(hide_code=True)
def _(
    alt,
    df_demand,
    df_usage,
    mo,
    months_list,
    pd,
    penalty_slider,
    production_cache,
    products_list,
    sc,
):
    # Load solution from cache (instant!) instead of solving
    _penalty_val = penalty_slider.value
    _cached = production_cache["penalty"].get(str(_penalty_val)) if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        _total_cost = _cached["total_cost"]
        _total_backorders = _cached["total_backorders"]
        _total_holding = _cached["total_holding"]
        _status = f"✅ Cost: **${_total_cost:,.0f}** | Backorders: **{_total_backorders:,.0f}** | On-Hand: **{_total_holding:,.0f}**"

        _viz_rows = []
        for _p in products_list:
            _batch_size = df_usage.loc[_p, "Batch Size"]
            for _t in months_list:
                _batches = _cached["solution"][_p][_t]
                _production = _batches * _batch_size
                _demand = df_demand.loc[_p, _t]
                _inventory = _cached["inventory"][_p][_t]
                _viz_rows.append({"Product": _p[:12], "Month": _t, "Production": _production, "Demand": _demand, "On-Hand": max(0, _inventory), "Backorders": max(0, -_inventory)})
        _viz_df = pd.DataFrame(_viz_rows)
        _viz_long = _viz_df.melt(id_vars=["Product", "Month"], value_vars=["Production", "Demand", "On-Hand", "Backorders"], var_name="Metric", value_name="Units")

        _products_left = [p[:12] for p in products_list[:4]]
        _products_right = [p[:12] for p in products_list[4:]]

        _legend_str = mo.md(
            """
            <span style='color:#3b82f6'><b>━ Production</b></span> &nbsp;
            <span style='color:#8b5cf6'><b>━ Demand</b></span> &nbsp;
            <span style='color:#22c55e'><b>-- On-Hand</b></span> &nbsp;
            <span style='color:#ef4444'><b>-- Backorders</b></span>
            """
        )

        def _make_chart(data, show_legend=False):
            _lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
                x=alt.X("Month:N", sort=months_list, title=None), y=alt.Y("Units:Q", title="Units"),
                color=alt.Color("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=["#3b82f6", "#8b5cf6", "#22c55e", "#ef4444"]), legend=None),
                strokeDash=alt.StrokeDash("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=[[0], [0], [4, 2], [4, 2]]), legend=None)
            )
            _points = alt.Chart(data).mark_circle(size=30).encode(x=alt.X("Month:N", sort=months_list), y=alt.Y("Units:Q"), color=alt.Color("Metric:N", legend=None), tooltip=["Product", "Month", "Metric", "Units"])
            return (_lines + _points).properties(width=360, height=75).facet(row=alt.Row("Product:N", title=None, header=alt.Header(labelFontSize=11, labelFontWeight="bold")))

        _chart_left = _make_chart(_viz_long[_viz_long["Product"].isin(_products_left)], False)
        _chart_right = _make_chart(_viz_long[_viz_long["Product"].isin(_products_right)], False)

        penSlide = sc.create_slide("Sensitivity: Penalty Cost", layout_type="2-column")
        # Left: Slider + Chart
        penSlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Penalty $p_i$:**"), penalty_slider], justify="start", gap=1),
            mo.md("&nbsp;"),
            mo.ui.altair_chart(_chart_left)
        ], gap=0.3)
        # Right: Status + Legend + Chart
        penSlide.content2 = mo.vstack([
            mo.md(f"**Result:** {_status}"),
            _legend_str,
            mo.ui.altair_chart(_chart_right)
        ], gap=0.3)
    else:
        penSlide = sc.create_slide("Sensitivity: Penalty Cost", layout_type="1-column")
        penSlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Penalty $p_i$:**"), penalty_slider], justify="start", gap=1),
            mo.md("❌ No cached solution found")
        ], gap=0.3)

    penSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    # Slider for holding cost sensitivity
    holding_slider = mo.ui.slider(0.1, 5.0, value=0.5, step=0.1, label="Holding Cost ($/unit/mo)", show_value=True)
    return (holding_slider,)


@app.cell(hide_code=True)
def _(
    alt,
    df_demand,
    df_usage,
    holding_slider,
    mo,
    months_list,
    pd,
    production_cache,
    products_list,
    sc,
):
    _holding_val = holding_slider.value
    _cached = production_cache["holding"].get(str(_holding_val)) if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        _total_cost = _cached["total_cost"]
        _total_backorders = _cached["total_backorders"]
        _total_holding = _cached["total_holding"]
        _status = f"✅ Cost: **${_total_cost:,.0f}** | Backorders: **{_total_backorders:,.0f}** | On-Hand: **{_total_holding:,.0f}**"

        _viz_rows = []
        for _p in products_list:
            _batch_size = df_usage.loc[_p, "Batch Size"]
            for _t in months_list:
                _batches = _cached["solution"][_p][_t]
                _production = _batches * _batch_size
                _demand = df_demand.loc[_p, _t]
                _inventory = _cached["inventory"][_p][_t]
                _viz_rows.append({"Product": _p[:12], "Month": _t, "Production": _production, "Demand": _demand, "On-Hand": max(0, _inventory), "Backorders": max(0, -_inventory)})
        _viz_df = pd.DataFrame(_viz_rows)
        _viz_long = _viz_df.melt(id_vars=["Product", "Month"], value_vars=["Production", "Demand", "On-Hand", "Backorders"], var_name="Metric", value_name="Units")

        _products_left = [p[:12] for p in products_list[:4]]
        _products_right = [p[:12] for p in products_list[4:]]

        _legend_str = mo.md(
            """
            <span style='color:#3b82f6'><b>━ Production</b></span> &nbsp;
            <span style='color:#8b5cf6'><b>━ Demand</b></span> &nbsp;
            <span style='color:#22c55e'><b>-- On-Hand</b></span> &nbsp;
            <span style='color:#ef4444'><b>-- Backorders</b></span>
            """
        )

        def _make_chart(data, show_legend=False):
            _lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
                x=alt.X("Month:N", sort=months_list, title=None), y=alt.Y("Units:Q", title="Units"),
                color=alt.Color("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=["#3b82f6", "#8b5cf6", "#22c55e", "#ef4444"]), legend=None),
                strokeDash=alt.StrokeDash("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=[[0], [0], [4, 2], [4, 2]]), legend=None)
            )
            _points = alt.Chart(data).mark_circle(size=30).encode(x=alt.X("Month:N", sort=months_list), y=alt.Y("Units:Q"), color=alt.Color("Metric:N", legend=None), tooltip=["Product", "Month", "Metric", "Units"])
            return (_lines + _points).properties(width=360, height=75).facet(row=alt.Row("Product:N", title=None, header=alt.Header(labelFontSize=11, labelFontWeight="bold")))

        _chart_left = _make_chart(_viz_long[_viz_long["Product"].isin(_products_left)], False)
        _chart_right = _make_chart(_viz_long[_viz_long["Product"].isin(_products_right)], False)

        holdSlide = sc.create_slide("Sensitivity: Holding Cost", layout_type="2-column")
        # Left: Slider + Chart
        holdSlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Holding $h_i$:**"), holding_slider], justify="start", gap=1),
            mo.md("&nbsp;"),
            mo.ui.altair_chart(_chart_left)
        ], gap=0.3)
        # Right: Status + Legend + Chart
        holdSlide.content2 = mo.vstack([
            mo.md(f"**Result:** {_status}"),
            _legend_str,
            mo.ui.altair_chart(_chart_right)
        ], gap=0.3)
    else:
        holdSlide = sc.create_slide("Sensitivity: Holding Cost", layout_type="1-column")
        holdSlide.content1 = mo.vstack([mo.hstack([mo.md("**Vary Holding $h_i$:**"), holding_slider], justify="start", gap=1), mo.md("❌ No cached solution found")], gap=0.3)

    holdSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    # Slider for initial inventory sensitivity
    init_inv_slider = mo.ui.slider(0, 500, value=200, step=50, label="Initial Inventory (units)", show_value=True)
    return (init_inv_slider,)


@app.cell(hide_code=True)
def _(
    alt,
    df_demand,
    df_usage,
    init_inv_slider,
    mo,
    months_list,
    pd,
    production_cache,
    products_list,
    sc,
):
    _init_val = init_inv_slider.value
    _cached = production_cache["init_inv"].get(str(_init_val)) if production_cache else None

    if _cached and _cached.get("status") == "optimal":
        _total_cost = _cached["total_cost"]
        _total_backorders = _cached["total_backorders"]
        _total_holding = _cached["total_holding"]
        _status = f"✅ Cost: **${_total_cost:,.0f}** | Backorders: **{_total_backorders:,.0f}** | On-Hand: **{_total_holding:,.0f}**"

        _viz_rows = []
        for _p in products_list:
            _batch_size = df_usage.loc[_p, "Batch Size"]
            for _t in months_list:
                _batches = _cached["solution"][_p][_t]
                _production = _batches * _batch_size
                _demand = df_demand.loc[_p, _t]
                _inventory = _cached["inventory"][_p][_t]
                _viz_rows.append({"Product": _p[:12], "Month": _t, "Production": _production, "Demand": _demand, "On-Hand": max(0, _inventory), "Backorders": max(0, -_inventory)})
        _viz_df = pd.DataFrame(_viz_rows)
        _viz_long = _viz_df.melt(id_vars=["Product", "Month"], value_vars=["Production", "Demand", "On-Hand", "Backorders"], var_name="Metric", value_name="Units")

        _products_left = [p[:12] for p in products_list[:4]]
        _products_right = [p[:12] for p in products_list[4:]]

        _legend_str = mo.md(
            """
            <span style='color:#3b82f6'><b>━ Production</b></span> &nbsp;
            <span style='color:#8b5cf6'><b>━ Demand</b></span> &nbsp;
            <span style='color:#22c55e'><b>-- On-Hand</b></span> &nbsp;
            <span style='color:#ef4444'><b>-- Backorders</b></span>
            """
        )

        def _make_chart(data, show_legend=False):
            _lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
                x=alt.X("Month:N", sort=months_list, title=None), y=alt.Y("Units:Q", title="Units"),
                color=alt.Color("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=["#3b82f6", "#8b5cf6", "#22c55e", "#ef4444"]), legend=None),
                strokeDash=alt.StrokeDash("Metric:N", scale=alt.Scale(domain=["Production", "Demand", "On-Hand", "Backorders"], range=[[0], [0], [4, 2], [4, 2]]), legend=None)
            )
            _points = alt.Chart(data).mark_circle(size=30).encode(x=alt.X("Month:N", sort=months_list), y=alt.Y("Units:Q"), color=alt.Color("Metric:N", legend=None), tooltip=["Product", "Month", "Metric", "Units"])
            return (_lines + _points).properties(width=360, height=75).facet(row=alt.Row("Product:N", title=None, header=alt.Header(labelFontSize=11, labelFontWeight="bold")))

        _chart_left = _make_chart(_viz_long[_viz_long["Product"].isin(_products_left)], False)
        _chart_right = _make_chart(_viz_long[_viz_long["Product"].isin(_products_right)], False)

        initSlide = sc.create_slide("Sensitivity: Initial Inventory", layout_type="2-column")
        # Left: Slider + Chart
        initSlide.content1 = mo.vstack([
            mo.hstack([mo.md("**Vary Initial Inv. $I_{i0}$:**"), init_inv_slider], justify="start", gap=1),
            mo.md("&nbsp;"),
            mo.ui.altair_chart(_chart_left)
        ], gap=0.3)
        # Right: Status + Legend + Chart
        initSlide.content2 = mo.vstack([
            mo.md(f"**Result:** {_status}"),
            _legend_str,
            mo.ui.altair_chart(_chart_right)
        ], gap=0.3)
    else:
        initSlide = sc.create_slide("Sensitivity: Initial Inventory", layout_type="1-column")
        initSlide.content1 = mo.vstack([mo.hstack([mo.md("**Vary Initial Inv. $I_{i0}$:**"), init_inv_slider], justify="start", gap=1), mo.md("❌ No cached solution found")], gap=0.3)

    initSlide.render()
    return


if __name__ == "__main__":
    app.run()
