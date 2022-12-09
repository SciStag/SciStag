from __future__ import annotations
import io
import PIL.Image
import numpy as np
from scistag.imagestag import Color
from scistag.imagestag.image import Image

try:
    from scistag.third_party.imgkit_fix import from_string, from_url

    IMG_KIT_AVAILABLE = True
except ModuleNotFoundError:
    IMG_KIT_AVAILABLE = False


class HtmlRenderer:
    """
    The HtmlLogRenderer allows the conversion from HTML code to an image for
    example to create the thumbnail of a web page or to integrate HTML elements
    into a slide.

    Important: Needs te optional imgkit module and wkhtmltopdf
    (https://wkhtmltopdf.org/)
    """

    def __init__(self):
        """
        Initializer
        """
        self.image: np.ndarray | None = None
        """
        The rendered web page
        """

    @staticmethod
    def dummy_image() -> Image:
        """
        Returns a dummy image if not data is available

        :return: Dummy image in the current framework's representation
        """
        result = np.ones((1, 1, 3), dtype=np.uint8)
        return Image(result)

    def render(self, options: dict | None = None) -> Image:
        """
        Renders the HTML code to an image

        :param options: One of the following optins can be provided:
            * html - The website's full HTML code (if set body & style are
                ignored)
            * body - Only the website's body. You can pass only the content
                code or
             the full <body> block
            * style - The site's style configuration (head.style)
            * width - The rendering width. Otherwise auto detected / clipped at
                1024. None by default.
            * height - The rendering height. Otherwise auto detected / no
                limitation. None by default.
            * transparent - Defines if the page shall be rendered onto
                transparent background so an RGBA image will be
            created. False by default.
            * backgroundColor - The color as Color object. White by default.
            * trimWidth - Automatically reduce the image's width if the full
                extend is not used. True by default.
            * trimHeight - Defines if the height shall be trimmed. False by
                default
        :return: An image handle
        """
        if not IMG_KIT_AVAILABLE:
            self.dummy_image()
        options = options if options is not None else {}
        quality = options.get("quality", 100)
        transparent = options.get("transparent", False)
        background_color = \
            options.get("backgroundColor",
                        Color(1.0, 1.0, 1.0, 0.0 if transparent else 1.0))
        if not transparent and background_color.to_rgba()[3] < 1.0:
            transparent = True
        image_format = options.get("format",
                                   "bmp" if not transparent else "png")
        red, green, blue, alpha = background_color.to_int_rgba()
        bg_color = f'rgba({red},{green},{blue},{alpha / 255})'
        html_data = self._generate_html(bg_color, options)
        html_options = {"format": image_format, "quality": quality,
                        "quiet": None}
        trim_width, trim_height = options.get("trimWidth", True), options.get(
            "trimHeight", False)
        if "width" in options:
            html_options["width"] = options["width"]
        if "height" in options:
            html_options["height"] = options["height"]
        if transparent:
            html_options["transparent"] = None
        image = from_string(html_data, False, options=html_options)
        pil_image = PIL.Image.open(io.BytesIO(image))
        if trim_width or trim_height:
            image = self._trim(np.array(pil_image), transparent=transparent,
                               trim_width=trim_width,
                               trim_height=trim_height)
            return Image(image)
        return Image(pil_image)

    @staticmethod
    def _trim(image: np.ndarray, transparent: bool, trim_width=True,
              trim_height=False) -> np.ndarray:
        """
        Searches for the first and last non-empty rows and columns and reduces
        the image to the valid pixels.

        :param image: The original image
        :param transparent: Defines if the image was transparent and the alpha
            channel can be used
        :param trim_width: Defines if the image shall be reduced horizontally
        :param trim_height: Defines if the image shall be reduced vertically
        :return: The trimmed image
        """
        if transparent and image.shape[2] == 4:
            alpha_channel: np.ndarray = image[:, :, 3]
            search_value = 255
        else:
            alpha_channel = Image.normalize_to_gray(image)
            search_value = alpha_channel[-1, -1]
        row_sums = np.sum(alpha_channel, axis=1)
        col_sums = np.sum(alpha_channel, axis=0)
        if trim_height:
            row_mismatch = np.where(
                row_sums != alpha_channel.shape[1] * search_value)
            first_row = row_mismatch[0][0] if len(row_mismatch) != 0 else 0
            last_row = row_mismatch[0][-1] if len(row_mismatch) != 0 else \
                image.shape[1] - 1
        else:
            first_row = 0
            last_row = image.shape[0] - 1
        if trim_width:
            col_mismatch = np.where(
                col_sums != alpha_channel.shape[0] * search_value)
            first_col = col_mismatch[0][0] if len(col_mismatch) != 0 else 0
            last_col = col_mismatch[0][-1] if len(col_mismatch) != 0 else \
                image.shape[0] - 1
        else:
            first_col = 0
            last_col = image.shape[1] - 1
        return image[first_row:last_row + 1, first_col:last_col + 1, :]

    @staticmethod
    def _generate_html(bg_color, options):
        """
        Generates the html data

        :param bg_color: The background color
        :param options: Generator options. See render
        :return: The html code
        """
        html = options.get("html", None)
        body = options.get("body", "")

        if html is not None:
            html_data = html
        else:
            style = options.get("style", "")
            html_data = f'<html><style>{style}</style>'
            if body.startswith("<body>"):
                html_data += body + "</html>"
            else:
                html_data += f'<body style="padding:0;margin:0;' \
                             f'background-color:{bg_color};">' + body + \
                             '</body></html>'
        return html_data
