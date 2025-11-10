
# slides.py
# Minimal marimo slide system: fixed 16:9 master, Title + Side-by-Side layouts.
# Uses mo.Html (capital H) and f-string interpolation (no unsupported kwargs).

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import marimo as mo
import html as _html

# ---- Tunable constants ----------------------------------------------------
SLIDE_WIDTH = 1280     # px
SLIDE_HEIGHT = 720      # px  (16:9)
GAP = 24               # px between columns
PADDING_X = 24         # px horizontal internal padding
PADDING_Y = 16         # px vertical internal padding
TITLE_FONT_SIZE = 28   # px (top headline)
FOOTER_FONT_SIZE = 12  # px

@dataclass
class Slide:
    title: str
    chair: str
    course: str
    presenter: str
    logo_url: Optional[str]
    page_number: int
    layout_type: str = "side-by-side"
    # Title slide
    subtitle: Optional[str] = None
    # Side-by-side content slots
    content1: Optional[mo.core.MIME] = None
    content2: Optional[mo.core.MIME] = None

    # ---- Sections (as mo.Html wrappers) ----------------------------------
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

    # ---- Layouts ----------------------------------------------------------
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
        # Convert strings to mo.md, keep mo.md objects as-is
        content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))

        # Wrap in vstack but override its styling to remove gaps
        content_wrapped = mo.vstack([content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})

        # Use mo.Html with single column spanning full width
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
        # Convert strings to mo.md, keep mo.md objects as-is
        left_content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
        right_content = mo.md(self.content2) if isinstance(self.content2, str) else (self.content2 or mo.md(""))

        # Wrap in vstack but override its styling to remove gaps
        left = mo.vstack([left_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
        right = mo.vstack([right_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})

        # Use mo.Html with proper nesting and inline styles as fallback
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
    def __init__(self, chair: str, course: str, presenter: str, logo_url: Optional[str] = None):
        self.chair = chair
        self.course = course
        self.presenter = presenter
        self.logo_url = logo_url
        self._page_counter = 0

    # Inject global CSS once near the top of your app
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

              /* Force slide dimensions in all modes */
              div.slide,
              .slide {{
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

              div.slide-title,
              .slide-title {{
                font-size: var(--title-size) !important;
                font-weight: 700 !important;
                line-height: 1.2 !important;
                margin: 0 !important;
              }}

              div.slide-hr,
              .slide-hr {{
                height: 1px !important;
                background: var(--border-color) !important;
                margin: 8px 0 !important;
              }}

              div.slide-body,
              .slide-body {{
                flex: 1 1 auto !important;
                min-height: 0 !important;
                display: flex !important;
                flex-direction: column !important;
              }}

              div.slide-cols,
              .slide-cols {{
                display: grid !important;
                grid-template-columns: 1fr 1fr !important;
                gap: var(--gap) !important;
                height: 100% !important;
                min-height: 0 !important;
              }}

              div.slide-col,
              .slide-col {{
                min-height: 0 !important;
                overflow: auto !important;
                padding-right: 2px !important;
              }}

              div.slide-footer div.slide-footer-row,
              .slide-footer .slide-footer-row {{
                display: grid !important;
                grid-template-columns: 1fr auto 1fr !important;
                align-items: center !important;
              }}

              div.slide-footer-left,
              .slide-footer-left {{
                font-size: var(--footer-size) !important;
                color: var(--text-muted) !important;
                white-space: nowrap !important;
              }}

              img.slide-logo,
              .slide-logo {{
                display: block !important;
                max-height: 28px !important;
                max-width: 160px !important;
                margin: 0 auto !important;
                object-fit: contain !important;
              }}

              /* Title slide */
              div.title-center,
              .title-center {{
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                height: 100% !important;
              }}

              div.title-stack,
              .title-stack {{
                text-align: center !important;
              }}

              div.title-slide-title,
              .title-slide-title {{
                font-size: 40px !important;
                font-weight: 800 !important;
                margin: 0 0 8px 0 !important;
              }}

              div.title-slide-sub,
              .title-slide-sub {{
                font-size: 20px !important;
                margin: 0 0 16px 0 !important;
                color: #374151 !important;
              }}

              div.title-slide-meta,
              .title-slide-meta {{
                font-size: 16px !important;
                color: var(--text-muted) !important;
              }}

              /* Tighter markdown spacing */
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

    def create_slide(self, title: str, layout_type: str = "side-by-side", page_number: Optional[int] = None) -> Slide:
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

    def create_title_slide(self, title: str, subtitle: Optional[str] = None, page_number: Optional[int] = None) -> Slide:
        slide = self.create_slide(title, layout_type="title", page_number=page_number)
        slide.subtitle = subtitle
        return slide
