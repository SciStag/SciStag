from scistag.imagestag.color import Color

from scistag.imagestag.canvas import Canvas


class Theme:
    """
    Defines a color theme to be used by the components by default
    """

    def __init__(self, scaling):
        """
        :param scaling: The scaling factor for all elements defined in inch
        """
        super().__init__()
        self.scaling = scaling
        self.default_control_height = 40.0
        "Default control height in pixels"
        self.default_font = "Roboto"
        "Default font for control elements"
        self.default_font_size = self.scaled(12)
        "Font size for control elements"
        self.default_background = Color(0.6, 0.6, 0.6, 1.0)
        "The background color"
        self.slide_background = Color(1.0, 1.0, 1.0, 1.0)
        "The slide background color"
        self.control_color = Color(0.8, 0.8, 0.8, 1.0)
        "The control background color"
        self.control_frame_border_width = self.scaled(2)
        "The control frame width"
        self.control_frame_border_color = Color(0.2, 0.0, 0.8, 1.0)
        "The control frame color"

    def scaled(self, value) -> int:
        """
        Returns value scaled by the current UI's scaling factor.

        This helps working with constants and definitions on a "common" 96 DPI
        windows monitor and scaling them by the current target device's
        requirements.

        :param value: The base size or offset in pixels at the base scaling
            factor (of 1.0)
        :return: The effective size or offset in effective pixels at the
            theme's scaling factor
        """
        return int(round(value * self.scaling))

    def get_default_font(self, canvas: Canvas):
        """
        Returns the theme's default font

        :param canvas: The output canvas
        :return: The font handle
        """
        return canvas.get_font(font_face=self.default_font, size=self.default_font_size)
