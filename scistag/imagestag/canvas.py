"""
Defines the :class:`.Canvas` class which provides functions for drawing elements
into an image.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from math import ceil
from typing import Literal

import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
import numpy as np

from .font import Font
from .pixel_format import PixelFormatTypes
from .text_alignment_definitions import (
    HTextAlignment,
    VTextAlignment,
    HTextAlignmentTypes,
    VTextAlignmentTypes,
)
from .definitions import ImsFramework
from .image import Image, ImageSourceTypes
from .bounding import Bounding2D, Bounding2DTypes, RawBoundingType
from .pos2d import Pos2DTypes
from . import Size2D, Pos2D, PixelFormat
from .size2d import Size2DTypes
from .anchor2d import Anchor2D, Anchor2DTypes
from .color import Color, Colors, ColorTypes, RawColorType


@dataclass
class CanvasState:
    """
    Defines the canvas's current transformation state
    """

    offset: tuple[float, float] = (0.0, 0.0)
    "The offset in pixels by which all content shall be moved"
    clipping: tuple[tuple[float, float], tuple[float, float]] = ((0.0, 0.0), (0.0, 0.0))
    """
    The bounding in pixels to which the painting shall be limited
    (if supported by the function
    """


class Canvas:
    """
    The Canvas class provides functions for drawing graphical elements such as
    lines, circles or text into an Image's pixel buffer.
    """

    def __init__(
        self,
        size: Size2DTypes = None,
        target_image: Image = None,
        default_color: ColorTypes = Colors.BLACK,
        pixel_format: PixelFormatTypes = "RGB",
    ):
        """
        :param size: The size in pixels (if a new image shall be created)
        :param target_image: An image into which the canvas shall paint
        :param default_color: The background fill color
        :param pixel_format: The image format, currently only RGB, RGBA and G
        """
        default_color = (
            default_color if isinstance(default_color, Color) else Color(default_color)
        )
        if (size is None and target_image is None) or (
            target_image is not None and size is not None
        ):
            raise ValueError("Either the size or a target image must be " "specified")
        if target_image is not None:
            size = target_image.get_size()
        else:
            size = Size2D(size).to_int_tuple()
        self.size = size
        "The image's size"
        self.width = size[0]
        "The image's width in pixels"
        self.height = size[1]
        "The image's height in pixels"
        self.size = (self.width, self.height)
        "The canvas' size in pixels"
        self.offset = (0, 0)
        """The current painting offset in pixels"""
        self.clip_region: tuple[tuple[float, float], tuple[float, float]] = (
            (0, 0),
            (self.width, self.height),
        )
        """The min and max x y position valid for painting. Note that this is 
        not respected by many paint commands but shall just help skipping 
        irrelevant geometries completely."""
        self.framework = ImsFramework.PIL
        "The rendering framework being used"
        self.stat_stack: list[CanvasState] = []
        """
        Buffer to backup and restore the current painting state such as
        offset and clipping bounding
        """
        self.target_image: PIL.Image
        "The image into which the canvas will paint"
        if target_image is not None:
            self.target_image = target_image.get_handle()
            assert isinstance(self.target_image, PIL.Image.Image)
        else:
            img_format = PixelFormat(pixel_format).to_pil()
            self.target_image = PIL.Image.new(
                img_format, (self.width, self.height), color=default_color.to_int_rgba()
            )
        self.image_draw = PIL.ImageDraw.ImageDraw(self.target_image)

    def __setattr__(self, key, value):
        if "image_draw" in self.__dict__:
            if key in {"width", "height", "size", "image", "image_draw", "framework"}:
                raise RuntimeError(
                    f"You may not modify {key} anymore after "
                    f"the canvas was constructed."
                )
        super().__setattr__(key, value)

    def to_image(self) -> Image:
        """
        Returns an image representation of this canvas.

        If the canvas draws directly to a PIL image handle the returned image
        will not be a copy and point ot the
        current PIL image handle as well.

        :return: The image handle
        """
        return Image(self.target_image)

    def push_state(self) -> Canvas:
        """
        Backups the current state

        :return: Self
        """
        self.stat_stack.append(
            CanvasState(offset=self.offset, clipping=self.clip_region)
        )
        return self

    def pop_state(self) -> Canvas:
        """
        Restores the previous state

        :return: Self
        """
        prev_state = self.stat_stack.pop()
        self.offset = prev_state.offset
        self.clip_region = prev_state.clipping
        return self

    def add_offset_shift(self, offset: (float, float)) -> Canvas:
        """
        Shifts the painting offset by given x, y distance in pixels

        :param offset: The distance of movement in pixels
        :return: Self
        """
        self.offset = (self.offset[0] + offset[0], self.offset[1] + offset[1])
        return self

    def transform_list(
        self, coordinates: list[Pos2D] | list[tuple]
    ) -> list[tuple[float, float]]:
        """
        Transforms a list of points by the defined scaling and offset settings
        of this canvas

        :param coordinates: The coordinates to transform
        :return: The transformed values
        """
        if len(coordinates) == 0:
            return []
        cleaned_coords: list[tuple[float, float]]
        if isinstance(coordinates[0], Pos2D):
            cleaned_coords = [coord.to_tuple() for coord in coordinates]
        else:
            cleaned_coords = coordinates
        result = cleaned_coords
        if not self.transformations_applied:  # nothing to do
            return result

        ox, oy = self.offset
        return [(ox + coord[0], oy + coord[1]) for coord in cleaned_coords]

    def transform(self, coord: tuple | Pos2D) -> tuple[float, float]:
        """
        Shifts given coordinates by this canvas' current drawing offset

        :param coord: The position or list of positions
        :return: The new position as tuple
        """
        if isinstance(coord, Pos2D):
            return self.offset[0] + coord.x, self.offset[1] + coord.y
        return self.offset[0] + coord[0], self.offset[1] + coord[1]

    def transform_size(self, size: Size2D) -> Size2D:
        """
        Scales the provided size by the canvas' scaling settings

        :param size: The size to scale
        :return: The new size
        """
        return size  # just prepared for later

    @property
    def transformations_applied(self) -> bool:
        """
        Returns if any transformations are applied to the canvas
        """
        return self.offset[0] != 0.0 or self.offset[1] != 0.0

    def clip(self, offset: (float, float), size: (float, float)) -> Canvas:
        """
        Clips the current painting region, relative to the current one

        :param offset: The distance of movement in pixels
        :param size: The width and height of the painting region
        """
        self.offset = (self.offset[0] + offset[0], self.offset[1] + offset[1])
        self.clip_region = (
            (
                max(self.offset[0], self.clip_region[0][0]),
                max(self.offset[1], self.clip_region[0][1]),
            ),
            (
                min(self.offset[0] + size[0], self.clip_region[1][0]),
                min(self.offset[1] + size[1], self.clip_region[1][1]),
            ),
        )
        self.clip_region = (
            (
                min(self.clip_region[0][0], self.clip_region[1][0]),
                # x/y should be <= x2/y2
                min(self.clip_region[0][1], self.clip_region[1][1]),
            ),
            (
                max(self.clip_region[0][0], self.clip_region[1][0]),
                # x2/y2 should be >= x/y
                max(self.clip_region[0][1], self.clip_region[1][1]),
            ),
        )
        return self

    def clear(self, color: ColorTypes = Colors.BLACK) -> Canvas:
        """
        Clears the canvas

        :param color: The color with which the canvas shall be cleared
        :return: Self
        """
        if self.framework != ImsFramework.PIL:
            raise NotImplementedError
        color = color if isinstance(color, Color) else Color(color)
        self.target_image.paste(color.to_int_rgba(), (0, 0, self.width, self.height))
        return self

    # noinspection PyMethodMayBeStatic
    def get_font(
        self, font_face: str, size: int, flags: set[str] | None = None
    ) -> Font | None:
        """
        Tries to create a font handle for given font and returns it.

        :param font_face: The font's face
        :param size: The font's size in pt
        :param flags: The flags such as {'Bold'} or {'Bold', 'Italic'}
        :return: On success the handle of the font
        """
        from scistag.imagestag.font_registry import FontRegistry

        return FontRegistry.get_font(font_face=font_face, size=size, flags=flags)

    # noinspection PyMethodMayBeStatic
    def get_default_font(
        self, size_factor=1.0, size: float | None = None, flags: set[str] | None = None
    ) -> Font:
        """
        Returns the default font configured for this canvas

        :param size_factor: Factor by which the font shall be scaled
        :param size: The effective size in pixels. Overrides size_factor.
        :param flags: The font flags. See :meth:`get_font`.

        :return: The default font
        """
        if size is not None:
            size = int(round(size))
        else:
            size = int(round(24 * size_factor))
        return self.get_font(font_face="Roboto", size=size, flags=flags)

        # noinspection PyMethodMayBeStatic

    # noinspection PyMethodMayBeStatic
    def load_image(self, source: ImageSourceTypes) -> Image:
        """
        Loads an image and returns it

        :param source: The image source, e.g. a filename, an URL or a
            bytes object.

            See :class:`ImageSourceTypes` for supported types.
        :return: The image handle
        """
        return Image(source, framework=ImsFramework.PIL)

    def draw_image(self, image: Image, pos: Pos2DTypes, auto_blend=True) -> Canvas:
        """
        Draws given image onto the canvas

        :param image: The source image to draw
        :param pos: The target position in pixels
        :param auto_blend: Defines if the image shall automatically alpha blend
            if it contains an alpha channel
        :return: Self
        """
        pos = self.transform(Pos2D(pos).to_int_tuple())
        pos = (int(round(pos[0])), int(round(pos[1])))
        pil_image: PIL.Image.Image = image.to_pil()
        if pil_image.mode == "RGBA" and auto_blend:
            self.target_image.paste(pil_image, pos, pil_image)
        else:
            self.target_image.paste(pil_image, pos)
        return self

    def pattern(
        self,
        image: Image,
        bounding: Bounding2DTypes,
        only_full_fit: bool = False,
        **params,
    ) -> Canvas:
        """
        Repeats an image within the specified area as often as possible

        :param image: The image to repeat
        :param bounding: The bounding in which the image shall be repeated
        :param only_full_fit: Defines if the pattern may only be repeated as
            long as the image fully fits into the area
        :param params: See :meth:`draw_image` for additional parameters
        :return: Self
        """
        bounding = Bounding2D(bounding)
        size = bounding.get_size_tuple()
        if only_full_fit:
            repetitions = (int(size[0] / image.width), int(size[1] / image.height))
        else:
            repetitions = (
                int(ceil(size[0] / image.width)),
                int(ceil(size[1] / image.height)),
            )
        for row in range(repetitions[1]):
            y = row * image.height
            for col in range(repetitions[0]):
                x = col * image.width
                self.draw_image(image, (x, y), **params)
        return self

    def rect(
        self,
        pos: Pos2DTypes | None = None,
        size: Size2DTypes | None = None,
        bounding: Bounding2DTypes | None = None,
        color: ColorTypes | None = None,
        outline_color: ColorTypes | None = None,
        outline_width: int = 1,
    ) -> Canvas:
        """
        Draws a rectangle onto the canvas

        :param pos: The position of the upper left edge
        :param size: The rectangle's size in pixels
        :param bounding: The bounding of the rectangle (alternative to
            pos and size).
        :param color: The inner color
        :param outline_color: The outline color
        :param outline_width: The outline's width
        :return: Self
        """
        if bounding is not None:
            bounding = Bounding2D(bounding)
            pos = bounding.pos
            size = bounding.get_size()
        else:
            pos = Pos2D(pos)
            size = Size2D(size)
        if color is not None:
            color = Color(color)
        if outline_color is not None and isinstance(outline_color, tuple):
            outline_color = Color(outline_color)
        xy = self.transform(pos)
        size = self.transform_size(size)
        x2y2 = (xy[0] + size.width - 1.0, xy[1] + size.height - 1.0)
        self.image_draw.rectangle(
            xy=(xy, x2y2),
            fill=color.to_int_rgba() if color is not None else None,
            outline=outline_color.to_int_rgba() if outline_color is not None else None,
            width=outline_width,
        )
        return self

    def rectangle_list(
        self,
        rectangles: list[RawBoundingType],
        colors: list[RawColorType] | None = None,
        single_color: RawColorType | None = None,
        outline_width: int = 0,
    ) -> Canvas:
        """
        Optimized rectangle drawing function for drawing a large amount of
        filled rectangles or frames in a single or multiple colors.

        Assumes raw-types for fast processing and can optimize the
        transformation process. This function is not (reasonable) faster if
        you just draw a single rectangle but should be preferred if you draw
        many ones.

        :param rectangles: The list of rectangles ((x,y),(x2,y2))
        :param colors: The list of colors (has to match the length of
            rectangles)
        :param single_color: The rectangle color (if all rectangles have the
            same color)
        :param outline_width: If defined a non-filled rectangles with given
            frame width will be painted
        :return: Self
        """
        ox, oy = self.offset
        if self.offset[0] != 0 or self.offset[1] != 0:
            rectangles = [
                ((cur[0][0] + ox, cur[0][1] + oy), (cur[1][0] + ox, cur[1][1] + oy))
                for cur in rectangles
            ]
        if outline_width != 0:
            if isinstance(outline_width, float):
                raise TypeError("Outline has to be defined as integer")
            if single_color is not None:
                for cur_rect in rectangles:
                    self.image_draw.rectangle(
                        xy=cur_rect, outline=single_color, width=outline_width
                    )
            else:
                if colors is None:
                    raise ValueError("No colors specified")
                if len(rectangles) != len(colors):
                    raise ValueError(
                        "The count of colors has to match the count" "of rectangles."
                    )
                for cur_rect, cur_color in zip(rectangles, colors):
                    self.image_draw.rectangle(
                        xy=cur_rect, outline=cur_color, width=outline_width
                    )
        else:
            if single_color is not None:
                for cur_rect in rectangles:
                    self.image_draw.rectangle(xy=cur_rect, fill=single_color)
            else:
                if colors is None:
                    raise ValueError("No colors specified")
                if len(rectangles) != len(colors):
                    raise ValueError(
                        "The count of colors has to match the count" "of rectangles."
                    )
                for cur_rect, cur_color in zip(rectangles, colors):
                    self.image_draw.rectangle(xy=cur_rect, fill=cur_color)
        return self

    def polygon(
        self,
        coords: list[Pos2DTypes] | np.ndarray,
        color: ColorTypes | None = None,
        outline_color: ColorTypes | None = None,
        outline_width: int = 1,
    ) -> Canvas:
        """
        Draws a polygon onto the canvas

        :param coords: A list of coordinates defining the polygon's bounding
        :param color: The inner color
        :param outline_color: The outline color
        :param outline_width: The outline's width
        :return: Self
        """
        if isinstance(coords, np.ndarray):
            coords = coords.astype(float).tolist()
        if len(coords) == 0:
            return self
        coords = self.transform_list(coords)
        coords = np.array(coords).flatten().tolist()
        pixel_format = PixelFormat.from_pil(self.target_image.mode)
        if color is not None:
            color = Color(color).to_format(pixel_format)
        if outline_color is not None:
            outline_color = Color(outline_color).to_format(pixel_format)
        self.image_draw.polygon(
            xy=coords,
            fill=color if color is not None else None,
            outline=outline_color if outline_color is not None else None,
            width=outline_width,
        )
        return self

    def line(
        self,
        coords: list[Pos2DTypes] | np.ndarray,
        color: ColorTypes | None = None,
        width: int = 1,
        curved_joints: bool = False,
    ) -> Canvas:
        """
        Draws a line onto the canvas between two or more points

        :param coords: A list of at least two x,y coordinates
        :param color: The line's color
        :param width: The line's width in pixels
        :param curved_joints: Defines if the connections shall be smoothed,
            recommend for very thick lines
        :return: Self
        """
        if isinstance(coords, np.ndarray):
            coords = coords.astype(float).tolist()
        if self.transformations_applied:
            coords = [self.transform(coord) for coord in coords]
        coords = np.array(coords).flatten().tolist()
        pixel_format = PixelFormat.from_pil(self.target_image.mode)
        if color is not None:
            color = Color(color).to_format(pixel_format)
        self.image_draw.line(
            xy=coords,
            fill=color if color is not None else None,
            width=width,
            joint="curve" if curved_joints else None,
        )
        return self

    def circle(
        self,
        coord: Pos2DTypes,
        radius: float | tuple[float, float] | None = None,
        color: ColorTypes | None = None,
        outline_color: ColorTypes | None = None,
        outline_width: float = 1.0,
        size: Size2DTypes | None = None,
    ) -> Canvas:
        """
        Draws a circle or ellipse onto the canvas

        :param coord: The circle's or ellipse's center coordinate
        :param radius: The circle's radius or the ellipse radius on
            the x and y axis
        :param color: The circle's fill color
        :param outline_color: The outline color
        :param outline_width: The outline's width
        :param size: The circle or ellipse's size
        :return: Self
        """
        pixel_format = PixelFormat.from_pil(self.target_image.mode)
        if outline_color is not None:
            outline_color = Color(outline_color).to_format(pixel_format)
        if (radius is None and size is None) or (
            size is not None and radius is not None
        ):
            raise ValueError("You need to either provide the size or the radius")
        if radius is not None:
            size = (
                Size2D(radius * 2, radius * 2)
                if isinstance(radius, (float, int))
                else Size2D(radius[0] * 2, radius[1] * 2)
            )
        else:
            size = Size2D(size)
        if self.transformations_applied:
            coord = self.transform(coord)
            size = self.transform_size(size)
        half_width, half_height = size.width / 2, size.height / 2
        coords = [
            coord[0] - half_width,
            coord[1] - half_height,
            coord[0] + half_width,
            coord[1] + half_height,
        ]
        pixel_format = PixelFormat.from_pil(self.target_image.mode)
        if color is not None:
            color = Color(color).to_format(pixel_format)
        self.image_draw.ellipse(
            xy=coords, fill=color, outline=outline_color, width=outline_width
        )
        return self

    def text(
        self,
        pos: Pos2DTypes,
        text: str,
        color: ColorTypes = Colors.BLACK,
        font: Font = None,
        h_align: HTextAlignmentTypes = HTextAlignment.LEFT,
        v_align: VTextAlignmentTypes = VTextAlignment.TOP,
        center: bool | None = None,
        line_spacing: int = 0,
        stroke_width: int = 0,
        stroke_color: ColorTypes | None = None,
        anchor: Anchor2DTypes = Anchor2D.TOP_LEFT,
        _show_formatting: bool = False,
    ) -> Canvas:
        """
        Renders a simple text using given parameters into the target image.

        :param pos: The text's position in x, y coordinates
        :param text: The text to be drawn
        :param color: The text's color
        :param font: The font to be used.
        :param line_spacing: The spacing between each line in pixels
        :param h_align: The text's horizontal alignment.

            Note that the text will be horizontally aligned to the right of
            pos. If you want to center a text to the left and right of ``pos``
            you can either pass the argument center=true or set
            h_align to HTextAlignment.CENTER and anchor to Anchor2D.CENTER.
        :param v_align: The text's vertical alignment. (line-wise)
            Can NOT be used to center a multi-line text.
        :param stroke_width: The stroke width in pixels. Only has effect
            if stroke_color is not None
        :param center: If set to true the text will be horizontally and
            vertically centered around pos.
        :param stroke_color: The stroke color
        :param anchor: The positioning anchor relative to which the text
            shall be positioned. Can be used to center a multiline
            vertically.
        :param _show_formatting: Defines if the formatting such as
            ascend and descent shall be visualized
        :return: Self
        """
        if font is None:
            font = self.get_default_font()
        if self.framework != ImsFramework.PIL:
            raise NotImplementedError
        if center is not None and center:
            h_align = HTextAlignment.CENTER
            anchor = Anchor2D.CENTER
        if isinstance(h_align, str):
            h_align = HTextAlignment(h_align)
        if isinstance(v_align, str):
            v_align = VTextAlignment(v_align)
        if isinstance(anchor, str):
            anchor = Anchor2D(anchor)
        y_offset = font.get_y_offset(v_align)
        base_xy = Pos2D(pos)
        lines = []
        row_widths = []
        text_size = font.get_text_size(text, out_lines=lines, out_widths=row_widths)
        if anchor != Anchor2D.TOP_LEFT:
            anchor.shift_position(base_xy, text_size, round_shift=True)
        color = (
            Color(color).to_int_rgba()
            if not isinstance(color, Color)
            else color.to_int_rgba()
        )
        stroke_color = (
            Color(stroke_color).to_int_rgba() if stroke_color is not None else None
        )
        pil_font = font.get_handle()
        org_pos = pos
        for index, row in enumerate(lines):
            row_spacing = font.row_height + line_spacing
            pos = Pos2D(base_xy.x, base_xy.y + y_offset + index * row_spacing)
            if h_align == HTextAlignment.CENTER:
                pos.x = pos.x + text_size.width // 2 - row_widths[index] // 2
            elif h_align == HTextAlignment.RIGHT:
                pos.x = pos.x + text_size.width - row_widths[index]
            xy = self.transform(pos)
            if _show_formatting:
                self.rect(
                    pos=xy,
                    size=(row_widths[index], font.row_height),
                    color=None,
                    outline_width=1,
                    outline_color=Colors.GREEN,
                )
            self.image_draw.text(
                xy=(xy[0], xy[1]),
                text=row,
                font=pil_font,
                align="left",
                fill=color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
            )
        if _show_formatting:
            org_pos = Pos2D(org_pos)
            self.rect(
                pos=(org_pos.x - 3, org_pos.y - 3), size=(6, 6), color=Colors.FUCHSIA
            )
        return self


__all__ = [
    "Canvas",
    "Color",
    "Colors",
    "Bounding2D",
    "HTextAlignment",
    "VTextAlignment",
]
