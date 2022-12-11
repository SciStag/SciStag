"""
Implements the class :class:`EmojiRenderer` which can render emojis in different
resolutions.
"""

from __future__ import annotations
from scistag.imagestag import svg, Image, Size2D, ColorTypes, Color, Canvas
from .emoji_db import EmojiDb
from ..imagestag.size2d import Size2DTypes

ENFORCE_SVG_QUALITY = 91
"The quality level from which on SVG rendering is enforced"

MINIMUM_SVG_RENDERING_QUALITY = 50
"The minimum quality required to allow SVG rendering"

EMOJI_DEFAULT_SIZE = Size2D(136, 128)
"The Noto Emoji default size for pre-rendered emojis"

EMOJI_DEFAULT_SIZE_RATIO = 136 / 128
"The emoji default size's ratio between width and height"


class EmojiRenderer:
    """
    Renders an emoji by either rendering an SVG or resizing a pre-rendered
    PNG from the Noto Emoji database.
    """

    @classmethod
    def get_svg_support(cls) -> bool:
        """
        Returns if SVG rendering is supported tne SVG repo installed

        :return: True if high quality rendering is possible
        """
        return EmojiDb.get_svg_support()

    @classmethod
    def render_emoji(
        cls,
        identifier: str | list[str],
        size: int | None | Size2DTypes = None,
        width: float = None,
        height: float = None,
        bg_color: ColorTypes | None = None,
        quality: int = 90,
    ) -> Image | None:
        """
        Tries to read an emoji and render it to a transparent image

        :param identifier: The emoji's markdown identifier such as :deer:, the
            official unicode name such as "deer",  the unicode sequence,
            e.g. ["u1f98c"] for a stag or just the emoji as single character.
        :param size: The size in pixels in which the emoji shall be rendered.
            By default the original Noto Emoji data set will be used providing
            the Emojis in a 136x128 resolution.
        :param width: The desired emoji width. The height will be computed
            automatically.
        :param height: The desired emoji height. The width will be computed
            automatically.
        :param bg_color: The color with which the background of the emoji shall
            be filled. By default the emoji will be a transparent RGBA image.
        :param quality: The desired quality. By default the renderer will try to
            use pre-rendered PNGs if the requested emoji size is small
            (<=136x128).
            These images are slightly quantized. If you want to maximize the
            image quality at all costs, you can set this value to >90 to enforce
            SVG rendering.

            This requires the SVG package to be installed.

            See ``python3 -m scistag.addons`` for details.

            If a very small value is passed (<50) SVG rendering will never be
            used.
        :return: The SVG data on success, otherwise None
        """
        svg_renderer_available = (
            svg.SvgRenderer.available() and quality >= MINIMUM_SVG_RENDERING_QUALITY
        )

        sequence = EmojiDb.get_character_sequence(identifier)
        # compute size
        if size is None:
            if width is not None:
                height = int(round(width * (1.0 / EMOJI_DEFAULT_SIZE_RATIO)))
                size = (int(round(width)), height)
            elif height is not None:
                width = int(round(height * EMOJI_DEFAULT_SIZE_RATIO))
                size = width, int(round(height))
            else:
                size = EMOJI_DEFAULT_SIZE
                size = size.to_int_tuple()
        else:
            if width is not None or height is not None:
                raise ValueError(
                    "Can not pass size and width or height at " "the same time."
                )
            if isinstance(size, (int, float)):
                size = round(int(size)), round(int(size))
            else:
                size = Size2D(size).to_int_tuple()
        # try to fetch emoji data
        svg_data = None
        is_default_size = size == EMOJI_DEFAULT_SIZE.to_int_tuple()
        # prefer lanczos instead of rendering when emoji is anyway very small
        very_small = size[0] <= 68 and size[1] <= 64
        if svg_renderer_available and (
            (not is_default_size and not very_small) or quality >= ENFORCE_SVG_QUALITY
        ):
            svg_data = EmojiDb.get_svg(sequence=sequence)
        png_data = None
        if not svg_data:
            png_data = EmojiDb.get_png(sequence)
        if svg_data is not None:
            image = svg.SvgRenderer.render(
                svg_data, size[0], size[1], bg_color=bg_color
            )
            if image is not None:
                return image
        if png_data is not None:
            image = Image(png_data)
            if bg_color is not None:  # insert background color if desired
                bg_color = Color(bg_color)
                canvas = Canvas(size=image.get_size(), default_color=bg_color)
                canvas.draw_image(image, pos=(0, 0)).to_image()
                image = canvas.to_image()
            image.resize(size)
            return image
        return None


def render_emoji(
    identifier: str | list[str],
    size: int | None | Size2DTypes = None,
    width: float = None,
    height: float = None,
    bg_color: ColorTypes | None = None,
    quality: int = 90,
) -> Image | None:
    """
    Tries to read an emoji and render it to a transparent image

    :param identifier: The emoji's markdown identifier such as :deer:, the
        official unicode name such as "deer",  the unicode sequence,
        e.g. ["u1f98c"] for a stag or just the emoji as single character.
    :param size: The size in pixels in which the emoji shall be rendered.
        By default the original Noto Emoji data set will be used providing
        the Emojis in a 136x128 resolution.
    :param width: The desired emoji width. The height will be computed
        automatically.
    :param height: The desired emoji height. The width will be computed
        automatically.
    :param bg_color: The color with which the background of the emoji shall
        be filled. By default the emoji will be a transparent RGBA image.
    :param quality: The desired quality. By default the renderer will try to
        use pre-rendered PNGs if the requested emoji size is small (<=136x128).
        These images are slightly quantized. If you want to maximize the
        image quality at all costs, you can set this value to >90 to enforce
        SVG rendering.

        This requires the SVG package to be installed.

        See ``python3 -m scistag.addons`` for details.

        If a very small value is passed (<50) SVG rendering will never be used.
    :return: The emoji as image.
    """
    return EmojiRenderer.render_emoji(
        identifier,
        size=size,
        width=width,
        height=height,
        bg_color=bg_color,
        quality=quality,
    )
