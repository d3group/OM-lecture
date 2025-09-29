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
        self.vertical_spacer_height = 800
        self.horizontal_spacer_width = 1600

    def get_spacer_horizontal(self, size=None):
        width = "auto" if size is None else f"{size}px"
        return mo.md(r"""&nbsp;""").style({"width": width})

    def get_spacer_vertical(self, size=600):
        height = "auto" if size is None else f"{size}px"
        return mo.md(r"""&nbsp;""").style({"height": height})

    def get_horizontal_rule(self):
        return mo.md(
            f"<div style='width: {self.horizontal_spacer_width}px; height: 1px; background-color: darkgray;'></div>"
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
        self, left_width=750, right_width=450, content1=None, content2=None
    ):
        title_style = {
            "width": "100%",
            "text-align": "left",
        }  # Ensure full width and left alignment

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
            elements = [
                self.get_spacer_horizontal(),
                title_content,
                self.get_horizontal_rule(),
                content,
            ]
            if include_footer:
                elements.append(self.get_footer(self.slide_number))
            return mo.vstack(elements, gap=0, justify="start", align="start")

        if self.layout_type == "title-slide":
            self.section = None
            content = mo.hstack(
                [
                    self.get_spacer_vertical(),
                    mo.vstack(
                        [
                            self.get_spacer_horizontal(),
                            self.get_spacer_vertical(100),
                            mo.hstack(
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
                                align="start",
                                gap=5,
                            ).style({"text-align": "left"}),
                            self.get_spacer_vertical(100),
                        ],
                        gap=0,
                        justify="start",
                    ),
                ]
            )
            slide = mo.vstack(
                [content, mo.vstack([self.logo], gap=0, align="end")], gap=0
            )

        elif self.layout_type == "1-column":
            content = mo.hstack(
                [self.get_spacer_vertical(), self.content1.style({"width": "100%"})],
                gap=0,
                justify="center",
                align="center",
            )
            slide = create_slide_content(content)

        elif self.layout_type == "side-by-side":
            content = mo.hstack(
                [
                    self.get_spacer_vertical(),
                    self.content1.style(
                        {
                            "width": "600px",
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                    self.content2.style(
                        {
                            "width": "600px",
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                ],
                gap=0,
                justify="center",
                align="center",
            )
            slide = create_slide_content(content)

        elif self.layout_type == "flexible-2-column":
            content = mo.hstack(
                [
                    self.get_spacer_vertical(),
                    self.content1.style(
                        {
                            "width": f"{left_width}px",
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                    self.content2.style(
                        {
                            "width": f"{right_width}px",
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                ],
                gap=0,
                justify="center",
                align="center",
            )
            slide = create_slide_content(content)

        elif self.layout_type == "2-row":
            top = self.content1.style({"width": 1600, "height": "50%", "margin-left": "auto", "margin-right": "auto"})
            bot = self.content2.style({"width": 1600, "height": "50%", "margin-left": "auto", "margin-right": "auto"})

            content = mo.vstack([top, bot], gap=2, justify="start", align="stretch")

            slide = create_slide_content(content)

        elif self.layout_type == "3-row":
            top = self.content1.style({"width": 1600, "height": "33%", "margin-left": "auto", "margin-right": "auto"})
            mid = self.content2.style({"width": 1600, "height": "33%", "margin-left": "auto", "margin-right": "auto"})
            bot = self.content3.style({"width": 1600, "height": "33%", "margin-left": "auto", "margin-right": "auto"})
            content = mo.vstack(
                [top, mid, bot], gap=1.5, justify="start", align="stretch"
            )
            slide = create_slide_content(content)

        else:  # Default layout
            content = mo.hstack(
                [
                    self.get_spacer_vertical(),
                    self.content1.style(
                        {
                            "width": 1600 ,
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                    self.content2.style(
                        {
                            "width": 1600,
                            "margin-left": "auto",
                            "margin-right": "auto",
                        }
                    ),
                ],
                gap=0,
                justify="center",
                align="center",
            )
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
