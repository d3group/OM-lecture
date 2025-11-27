import marimo as mo


class Slide:
    def __init__(
        self,
        title,
        slide_number,
        chair_title="Default Chair Title",
        lecture_name="Default Lecture Name",
        layout_type="2-column",
        presenter="Default Presenter",
        section="Default Section",
    ):
        self.slide_data = {}
        self.section = section
        self.layout_type = layout_type
        self.lecture_name = lecture_name
        self.presenter = presenter
        self.title = title
        self.title_raw = title
        self.content1 = mo.md("")
        self.content2 = mo.md("")
        self.content3 = mo.md("")
        self.chair_title = chair_title
        self.slide_number = slide_number
        self.logo = mo.image(
            "https://raw.githubusercontent.com/d3group/.github/refs/heads/main/assets/D3_2c.png",
            width=200,
        )
        self.vertical_spacer_height = "auto"
        self.horizontal_spacer_width = "100%"

    def get_spacer_horizontal(self, size=None):
        width = "auto" if size is None else f"{size}px"
        return mo.md(r"""&nbsp;""").style({"width": width, "flex-shrink": 0})

    def get_spacer_vertical(self, size=None):
        height = "1rem" if size is None else f"{size}px"
        return mo.md(r"""&nbsp;""").style({"height": height, "flex-shrink": 0})

    def get_horizontal_rule(self):
        return mo.md(
            f"<div style='width: 100%; height: 1px; background-color: darkgray;'></div>"
        )

    def get_footer(self, slide_number=0):
        # Wrap text with HTML span to adjust font size since mo.md doesn't support size arg
        small = lambda text: f"<span style='font-size:0.7em;'>{text}</span>"

        if slide_number is not None:
            return mo.vstack(
                [
                    self.get_horizontal_rule(),
                    mo.hstack(
                        [
                            mo.hstack(
                                [
                                    mo.md(
                                        small(f"Page {slide_number}  |  "),
                                    ),
                                    mo.md(
                                        small(f"_{self.chair_title}_  | "),
                                    ),
                                    mo.md(
                                        small(f"_{self.lecture_name}_"),
                                    ),
                                ],
                                gap=0,
                                justify="start",
                            ),
                            mo.vstack([self.logo], gap=0, align="end"),
                        ],
                        widths=[0.8, 0.2],
                    ),
                ],
                align="start",
            )
        else:
            return mo.vstack(
                [
                    self.get_horizontal_rule(),
                    mo.hstack(
                        [
                            mo.hstack(
                                [
                                    mo.md(
                                        small("Agenda | "),
                                    ),
                                    mo.md(
                                        small(f"_{self.chair_title}_ | "),
                                    ),
                                    mo.md(
                                        small(f"_{self.lecture_name}_"),
                                    ),
                                ],
                                gap=0,
                                justify="start",
                            ),
                            mo.vstack([self.logo], gap=0, align="end"),
                        ],
                        widths=[0.8, 0.2],
                    ),
                ],
                align="start",
            )

    def render_slide(
        self, left_width=None, right_width=None, content1=None, content2=None
    ):
        title_style = {
            "width": "100%",
            "text-align": "left",
        }

        if self.title != "Agenda":
            title_content = mo.vstack(
                [
                    mo.md(
                        f"<span style='font-size: 90%; color: gray;'>_{self.section}_</span>"
                    ),
                    mo.md(f"# {self.title}").style(title_style),
                ],
                align="start",
            )
        else:
            title_content = mo.vstack(
                [
                    mo.md(f"<span style='font-size: 90%; color: gray;'>_ _</span>"),
                    mo.md(f"# {self.title}").style(title_style),
                ],
                align="start",
            )

        # Generic slide structure
        def create_slide_content(content, include_footer=True):
            # Use HTML structure with CSS classes for layout
            header = mo.vstack([
                title_content,
                self.get_horizontal_rule(),
            ], gap=0, align="start", justify="start").style({"width": "100%"})
            
            footer = self.get_footer(self.slide_number) if include_footer else mo.md("")
            
            return mo.Html(f"""
                <div class="slide-container">
                    <div class="slide-content-wrapper">
                        {header}
                        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; width: 100%;">
                            {content}
                        </div>
                        <div class="slide-footer">
                            {footer}
                        </div>
                    </div>
                </div>
            """)

        if self.layout_type == "title-slide":
            self.section = None
            
            # Title slide content
            main_content = mo.hstack(
                [
                    mo.md(
                        """<div style='width: 4px; height: 300px; background-color: darkgray;'></div>"""
                    ),
                    mo.vstack(
                        [
                            mo.md(
                                f"<span style='font-size:2em;'>{self.lecture_name}</span>"
                            ),
                            mo.md(f"#{self.title_raw}"),
                            mo.md(""),
                            mo.md(""),
                            mo.hstack(
                                [
                                    mo.vstack(
                                        [
                                            mo.md(
                                                f"{self.presenter} ({self.chair_title})"
                                            )
                                        ],
                                        align="start",
                                    ),
                                    self.content2,
                                ],
                                align="center",
                                gap=1,
                                justify="space-around",
                            ),
                        ],
                        align="start",
                    ),
                ],
                justify="start",
                align="center",
                gap=2,
            ).style({"text-align": "left"})
            
            slide = create_slide_content(main_content, include_footer=False)
            # Add logo manually for title slide if needed, or rely on footer logic if we want it there.
            # The original code added logo at the bottom right.
            # Let's add it to the footer area but without the rule/text if that was the intent,
            # or just use the standard footer logic but maybe different content.
            # Re-reading original: title slide had logo at bottom right but no footer text.
            
            slide = mo.Html(f"""
                <div class="slide-container">
                    <div class="slide-content-wrapper" style="justify-content: center;">
                        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; width: 100%;">
                            {main_content}
                        </div>
                        <div class="slide-footer" style="display: flex; justify-content: flex-end;">
                            {self.logo}
                        </div>
                    </div>
                </div>
            """)


        elif self.layout_type == "1-column":
            content = self.content1.style({"width": "100%"})
            slide = create_slide_content(content)

        elif self.layout_type == "side-by-side":
            # Add CSS for compact text spacing (PowerPoint-like)
            compact_text_style = mo.Html("""
                <style>
                    .slide-content-compact p { 
                        margin: 0.35em 0 !important; 
                        line-height: 1.5;
                    }
                    .slide-content-compact ul { 
                        margin: 0.4em 0 !important; 
                        padding-left: 1.5em; 
                    }
                    .slide-content-compact ol { 
                        margin: 0.4em 0 !important; 
                        padding-left: 1.5em; 
                    }
                    .slide-content-compact li { 
                        margin: 0.2em 0 !important; 
                        line-height: 1.4;
                    }
                    .slide-content-compact h1, 
                    .slide-content-compact h2, 
                    .slide-content-compact h3,
                    .slide-content-compact h4 { 
                        margin: 0.6em 0 0.3em 0 !important; 
                    }
                </style>
            """)
            
            content = mo.vstack([
                compact_text_style,
                mo.Html(f"""
                    <div class="layout-2-column">
                        <div class="layout-column slide-content-compact">
                            {self.content1}
                        </div>
                        <div class="layout-column slide-content-compact">
                            {self.content2}
                        </div>
                    </div>
                """)
            ], gap=0)
            slide = create_slide_content(content)

        elif self.layout_type == "flexible-2-column":
            # Use flex-basis or width percentages if provided, otherwise equal width
            # Converting pixel widths to approximate flex ratios or just using flex
            
            style1 = {"flex": "1"}
            style2 = {"flex": "1"}
            
            if left_width and right_width:
                 total = left_width + right_width
                 p1 = (left_width / total) * 100
                 p2 = (right_width / total) * 100
                 style1 = {"width": f"{p1}%"}
                 style2 = {"width": f"{p2}%"}
            
            content = mo.Html(f"""
                <div class="layout-2-column">
                    <div class="layout-column" style="flex: {style1.get('flex', 'none')}; width: {style1.get('width', 'auto')}">
                        {self.content1}
                    </div>
                    <div class="layout-column" style="flex: {style2.get('flex', 'none')}; width: {style2.get('width', 'auto')}">
                        {self.content2}
                    </div>
                </div>
            """)
            slide = create_slide_content(content)

        elif self.layout_type == "2-row":
            top = self.content1.style({"width": "100%", "height": "auto"})
            bot = self.content2.style({"width": "100%", "height": "auto"})

            content = mo.vstack([top, bot], gap=2, justify="start", align="stretch")
            slide = create_slide_content(content)

        elif self.layout_type == "3-row":
            top = self.content1.style({"width": "100%", "height": "auto"})
            mid = self.content2.style({"width": "100%", "height": "auto"})
            bot = self.content3.style({"width": "100%", "height": "auto"})

            content = mo.vstack([top, mid, bot], gap=1.5, justify="start", align="stretch")
            slide = create_slide_content(content)

        else:  # Default layout
             # 2 columns equal width default? Original code had 2 columns with 1600px width each which implies stacking or overflow?
             # Actually original code:
             # content = mo.hstack([spacer, content1, content2])
             # where content1 and content2 both had width 1600. This seems like they would stack or overflow horizontally.
             # Assuming side-by-side or just one column if content2 is empty?
             # Let's assume standard 2-column for default if 2 contents exist.
             
            content = mo.Html(f"""
                <div class="layout-2-column">
                    <div class="layout-column">
                        {self.content1}
                    </div>
                    <div class="layout-column">
                        {self.content2}
                    </div>
                </div>
            """)
            slide = create_slide_content(content)

        slide = mo.vstack([slide, mo.Html("""<div class="page-break"></div>""")])
        return slide

    def get_title_number(self):
        return (self.title_raw, self.slide_number)


class SlideCreator:
    def __init__(
        self,
        chair_title="Default Chair Title",
        lecture_name="Default Lecture Name",
        presenter="Default Presenter",
    ):
        self.chair_title = chair_title
        self.lecture_name = lecture_name
        self.presenter = presenter
        self.pages = []
        self.currentSection = "Default Section"

    def create_slide(self, title, layout_type="2-column", newSection=None):
        if newSection:
            self.currentSection = newSection
        slide = Slide(
            title,
            len(self.pages) + 1,
            chair_title=self.chair_title,
            lecture_name=self.lecture_name,
            presenter=self.presenter,
            layout_type=layout_type,
            section=self.currentSection,
        )
        self.pages.append(slide)
        return slide

    def create_agenda(self, title="Agenda", currentSection=None):
        agenda = {}
        for page in self.pages:
            if page.section is not None:
                if page.section not in agenda:
                    agenda[page.section] = []
                agenda[page.section].append(page.get_title_number()[0])

        # Creating a slide similar to the title-slide layout
        agenda_slide = Slide(
            title,
            None,
            chair_title=self.chair_title,
            lecture_name=self.lecture_name,
            presenter=self.presenter,
            layout_type="1-column",
            section=currentSection or self.currentSection,
        )

        # Building the markdown content for agenda
        agenda_content = ""
        for section, titles in agenda.items():
            if currentSection is not None and section == currentSection:
                agenda_content += f"<span style='background-color:lightblue; font-weight:bold; color:gray; display: inline-block; width: 450px;'>{section}</span>\n\n"
            else:
                agenda_content += f"**{section}**\n\n"
            # if currentSection is not None and section == currentSection:
            #     for slide_title in titles:
            #         agenda_content += f"\n &nbsp;&nbsp; <sub>{slide_title}</sub> \n"
            # agenda_content += "\n \n"

        # Setting the content of the slide
        agenda_slide.content1 = mo.md(agenda_content)

        self.pages.append(agenda_slide)
        return agenda_slide.render_slide()
