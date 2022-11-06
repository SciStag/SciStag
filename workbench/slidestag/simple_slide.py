from __future__ import annotations
from scistag.slidestag import Slide, SlideApp, SlideSession, PaintEvent
from scistag.slidestag.slide_manager import SlideManager


class SimpleSlideSession(SlideSession):
    """
    Helper class for SimpleSlide to provide an easy start using SlideStag.
    """

    cls_title = ""
    "The session's initial title"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.resolution = SimpleSlide.cls_resolution
        self.slide_resolution = SimpleSlide.cls_resolution
        self.dpi = SimpleSlide.cls_dpi
        self.title = self.cls_title

    def build(self):
        super(SimpleSlideSession, self).build()
        SimpleSlide(self.get_slide_manager())
        self.get_slide_manager().start()


class SimpleSlide(Slide):
    """
    The SimpleSlide class shall help with the creation of small applications using a minimum amount of code.

    It allows the user to define the three main elements of a SlideStag application with just a single line of code
    * A SlideStag session
    * A SlideStag application class
    * The Slide class itself

    Usage:
        def build(slide: Slide):
            ...

        def paint(slide: Slide, canvas: Canvas):
            ...

        if __name__ == "__main__":
            SimpleSlide.create_simple_app(on_build=build, on_paint=paint).run_as_kivy_app()

    """

    cls_name = ""
    "The application's name"
    cls_title = ""
    "The main slide's title (displayed in the window title and the browser)"
    cls_resolution = (1920, 1080)
    "The apps resolution"
    cls_dpi = 96
    "Pixel density, usually 96 for a FullHD and 192 for an UltraHD presentation"
    cls_load_callback = None
    "Function to be called when the slide is loaded"
    cls_paint_callback = None
    "Function to be called when the slide is painted"
    cls_tap_callback = None
    "Function to be called on a tap (click)"
    cls_drag_callback = None
    "Function to be called on a drag (tap and mouse or finger movement)"
    cls_mouse_move_callback = None
    "Function to be called on pure mouse movement - not called on some devices, e.g. tablets"
    cls_repaint_frequency = 10.0
    "The automatic repaint frequency"

    def __init__(self, slide_manager: SlideManager,
                 parameters: dict = None) -> None:
        super().__init__(slide_manager, parameters)
        self.build_callback = self.cls_load_callback
        self.paint_callback = self.cls_paint_callback
        self.tap_callback = self.cls_tap_callback
        self.drag_callback = self.cls_drag_callback
        self.mouse_move_callback = self.cls_mouse_move_callback
        self.slide_app_name = self.cls_name
        self.title = self.cls_title
        self.auto_repaint_frequency = self.cls_repaint_frequency

    def handle_load(self) -> bool:
        return super().handle_load()

    def handle_paint(self, event: PaintEvent) -> bool:
        super().handle_paint(event)
        if self.paint_callback is not None:
            self.paint_callback(event.canvas)
        return True

    @classmethod
    def create_simple_app(cls, name="SlideStag", title: str | None = None,
                          resolution=(1920, 1080),
                          dpi=96.0, on_load=None, on_paint=None,
                          on_tap=None, on_drag=None, on_mouse_move=None,
                          repaint_frequency: float = 10.0) -> "SlideApp":
        """
        Setups a simple SlideStag application

        :param name: The application's name. "SlideStag" by default
        :param title: Title to be displayed in the window's title or the browser's title. "SlideStag by default"
        :param resolution: The application screen resolution in pixels. FullHD by default.
        :param dpi: The DPI value. 96 by default.
        :param on_load: Function to called when the slide becomes visible. You can use this callback to
            construct your slide's UI or prepare temporary data. Remember and access data via slide["myData"] = myValue.
        :param on_paint: Function to be called when the app is repainted.
        :param on_tap: Function to be called when the Slide is clicked (and no other component was hit)
        :param on_drag: Function to be called when the user tries to drag the slide
        :param on_mouse_move: Function to be called when the user just moves the mouse. (not supported on all devices)
        :param repaint_frequency: The automatic repaint frequency. (repaints per second). If set to a value>0 the
            on_paint function will be called automatically multiple times a second so the user can use it to display
            his or her data. This makes it especially easy for beginners o write their first simple application.
            More experienced users can just set this value to zero (or directly implement their own SlideClass ;-).
        :return: The application handle.
        """
        cls.cls_name = name
        cls.cls_title = title if title is not None else name
        SimpleSlideSession.cls_title = cls.cls_title
        cls.cls_resolution = resolution
        cls.cls_dpi = dpi
        cls.cls_load_callback = on_load
        cls.cls_paint_callback = on_paint
        cls.cls_tap_callback = on_tap
        cls.cls_drag_callback = on_drag
        cls.cls_mouse_move_callback = on_mouse_move
        cls.cls_repaint_frequency = repaint_frequency
        app = SlideApp(cls.cls_name, SimpleSlideSession).register()
        return app
