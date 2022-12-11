from __future__ import annotations
from typing import TYPE_CHECKING
from scistag.imagestag.canvas import Canvas
from scistag.imagestag import Color
from scistag.slidestag.widget import Widget

if TYPE_CHECKING:
    from scistag.slidestag.slide import Slide
    from scistag.slidestag.base_events import PaintEvent


class SlideManager(Widget):
    """
    The slider manager handles the "screen" (in our case slide) life cycle and
    is usually the second highest view hierarchy element, directly after the
    window.

    It's responsible for showing and hiding single slides and to tell them when
    to load and when to unload their data or save and reload their state.
    """

    def __init__(self, parent: Widget, parameters: dict):
        """
        Initializer
        :param parent: The parent view
        :param parameters: The creation parameters
        """
        super().__init__(parent, parameters)
        self._current_slide: Slide = None
        self.slides = []  # List of all slides in order
        self._first_slide = None
        "The first slide to be visited"
        self.developer_mode = True
        """If defines breakpoint stepping is enabled. In addition the initial 
        slide will always be the one with a
        defined breakpoint"""

    def start(self, with_slide: Slide | None = None) -> Slide | None:
        """
        Starts the presentation with the following priority:
        * If a slide set a breakpoint via Slide.add_breakpoint this will
            always be the initial slide
        * If with_slide is provided this will be the initial slide
        * Otherwise it will start with the first added, non-hidden slide.

        :param with_slide: The session to start the slide with.
        :return: The slide selected
        """
        start_slide = None
        for slide in self.slides:
            if len(slide.breakpoints):
                start_slide = slide
                break
        if start_slide is None:
            start_slide = with_slide
        if start_slide is None:
            if self._first_slide is None:
                if len(self.slides) != 0:
                    start_slide = self.slides[0]
        if start_slide is not None:
            self.show_slide(start_slide)
        return start_slide

    def show_slide(self, slide: str | Slide | None) -> Slide | None:
        """
        Requests swapping from the current to another slide

        :param slide: The new slide
        :return: The slide object if it was found
        """
        if self._current_slide is not None:
            self._current_slide.set_visible(False)
        if slide is not None:
            if isinstance(slide, str):
                for element in self.slides:
                    element: "Slide"
                    if element.get_name() == slide:
                        slide = element
                        break
            if slide is None:
                return
            slide: "Slide"
            slide.set_visible(True)
            self.to_top(slide)
            self._current_slide = slide

    def get_current(self) -> Slide | None:
        """
        Returns the current visible slide
        :return: The current slide
        """
        return self._current_slide

    def go_last(self, current: Slide | None = None) -> bool:
        """
        Goes to the previous slide. Pass the current slide as verification
        of the current slide sending the event.

        :param current: The current (assumed) slide
        :return True if the slide could successfully be changed
        """
        if (
            current is not None
            and current != self._current_slide
            or len(self.slides) == 0
        ):
            return False
        if self._current_slide is None:
            target = 0
        else:
            cur_index = self.slides.index(self._current_slide)
            if cur_index == 0:
                return False
            target = cur_index - 1
        self.show_slide(self.slides[target])
        return True

    def go_next(self, current: Slide | None = None) -> bool:
        """
        Goes to the next slide. Pass the current slide as verification of
        the current slide sending the event.

        :param current: The current (assumed) slide
        :return True if the slide could successfully be changed
        """
        if (current is not None and current != self._current_slide) or len(
            self.slides
        ) == 0:
            return False
        if self._current_slide is None:
            target = 0
        else:
            cur_index = self.slides.index(self._current_slide)
            if cur_index == len(self.slides) - 1:
                return False
            target = cur_index + 1
        self.show_slide(self.slides[target])
        return True

    def add_widget(self, child: Widget):
        super().add_widget(child)
        from .slide import Slide

        if isinstance(child, Slide):
            self.slides.append(child)

    def remove_widget(self, child: Widget) -> bool:
        if child in self.slides:
            self.slides.remove(child)
        return super().remove_widget(child)

    def handle_paint(self, event: PaintEvent) -> bool:
        canvas: Canvas = event.canvas
        theme = self.theme
        canvas.rect(
            pos=(0.0, 0.0),
            size=self.size,
            color=theme.default_background,
            outline_color=Color(0, 0, 0),
            outline_width=0,
        )
        return super().handle_paint(event)
