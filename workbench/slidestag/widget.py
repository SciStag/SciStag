from __future__ import annotations
from typing import Callable, Any, Union
from scistag.common import Component
from scistag.common.data_cache import DataCache
from scistag.imagestag import Color, Size2D, Pos2D
from scistag.imagestag.bounding import Bounding2D
from scistag.imagestag.pos2d import Pos2DTypes
from scistag.imagestag.size2d import Size2DTypes
from scistag.imagestag.canvas import Canvas
from scistag.slidestag.slide_theme import Theme
from scistag.slidestag.base_events import WidgetEventHandler, TapEvent, PaintEvent


class Widget(Component):
    """
    The Widget class is the base class for all visual control elements in SlideStag.
    """

    def __init__(
        self,
        parent: Widget | None = None,
        position: Pos2DTypes | None = None,
        size: Size2DTypes | None = None,
        alpha: float = 1.0,
        visible: bool = True,
        background_color: Color = None,
    ):
        """
        :param parent: The parent widget
        :param position: The position in pixels, relative to the upper left corner of it's parent. 0.0, 0.0 by default
        :param size: The size in pixels
        :param alpha: The visibility in percent (0 = invisible, 1.0 = fully opaque).
        :param visible: Defines if the view shall be visible in general
        :param background_color: The widget's background color. None by default
        """
        super().__init__()
        self.visible: bool = visible
        "Defines if the view is visible"
        self.alpha: float = alpha
        "Property. The view's alpha value (1.0 = 100% opaque)"
        self.position: Pos2D = (
            Pos2D(position) if position is not None else Pos2D(0.0, 0.0)
        )
        "Property. The view's position in pixels, relative to it's parent's upper left edge"
        self.size: Size2D = Size2D(size) if size is not None else Size2D(100.0, 100.0)
        "Property. The view's size in pixels"
        self.parent: Widget | None = None
        "Property (read-only). The widget's parent"
        self.background_color: Color | None = background_color
        "Property. The widget's background color"
        self.temp_cache = DataCache()
        "A temporary cache. It will be cleared upon unloading of the widget (after the execution of handle_unload).\
        Usage: slide.cache('myData', lambda: pd.read_csv('myData.csv'))"
        self.dpi_scaling = 1.0
        "Defines the widget's DPI scaling. 1.0 = 96 DPI"
        self.session = parent.session if parent is not None else None
        "Defines the session / execution context of this widget"
        self.theme = Theme(scaling=self.dpi_scaling)
        "The scaling factor which should be applied to all painting operations. See scale function"
        self.sensitive = True
        "Defines if this element can catch clicks or is just an overlay"
        self._children = []
        "List of all children"
        self._visible_children = []
        "List of all visible children"
        self._layout_update_required = True
        "FLag is an internal relayouting is required"
        self.on_paint = WidgetEventHandler(event_class=PaintEvent)
        "The paint event is triggered when ever the view shall be visualized"
        self.on_click = WidgetEventHandler(event_class=TapEvent)
        self.properties = self.PROPERTIES
        if parent is not None:
            parent.add_widget(self)

    PROPERTIES = {
        "position": {
            "info": "A widget's position in pixels, relative to it's parents upper left coordinate",
            "type": tuple[float, float],
        },
        "size": {"info": "A widget's size in pixels", "type": "Size2D"},
        "parent": {
            "info": "A widget's parent widget",
            "type": "AWidget",
            "readOnly": True,
        },
        "alpha": {"info": "Opacity in percent (0.0 .. 1.0)", "type": float},
        "visible": {"info": "Defines if the view is visible", "type": bool},
        "background_color": {
            "info": "The Widget's background color. Fills the image's background if defined.",
            "type": Union[Color, None],
        },
        "theme": {
            "info": "Defines the color scheme to be used",
            "type": Theme,
            "readOnly": True,
        },
        "dpi_scaling": {
            "info": "Defines the scaling factor to be applied",
            "type": float,
            "readOnly": True,
        },
        "session": {
            "info": "Defines the widget's user session",
            "type": "Session",
            "readOnly": True,
        },
    } | Component.PROPERTIES

    def handle_paint(self, event: PaintEvent) -> bool:
        """
        Is called when ever the view shall be painted

        :param event: The event
        :return: True if the execution shall continue
        """
        if self.background_color is not None:
            event.canvas.rect(
                pos=(0.0, 0.0), size=self.size, color=self.background_color
            )
        if not self.on_paint.execute(event):
            return False
        return True

    def handle_click(self, event: TapEvent) -> bool:
        """
        Is called when a mouse click or touch is executed

        :param event: The event
        :return: True if the execution shall continue
        """
        if not self.on_click.execute(event):
            return False
        return True

    def handle_load(self):
        """
        Called when the widget becomes visible and shall be loaded
        """
        super().handle_load()
        for element in self._visible_children:  # reload all now visible children
            element: "Widget"
            element.handle_load()

    def handle_unload(self):
        """
        Called when the widget becomes invisible and shall be unloaded
        """
        for element in self._visible_children:  # reload all now visible children
            element: "Widget"
            element.handle_unload()
        super().handle_unload()

    def handle_added_to_widget(self, parent: "Widget") -> None:
        """
        Is called when the Widget is added to another Widget as child

        :param parent: The parent widget
        """
        self.__dict__["parent"] = parent
        self.__dict__["dpi_scaling"] = parent.dpi_scaling
        self.__dict__["theme"] = parent.theme
        self.__dict__["session"] = parent.session

    def handle_removed(self) -> None:
        """
        Is called when the Widget is removed from a parent widget
        """
        if self.loaded:
            self.unload()
        self.__dict__["parent"] = None

    def add_widget(self, child: "Widget"):
        """
        Registers a child widget

        :param child: The new child
        """
        self.repaint()
        if child.parent is not None:
            raise RuntimeError("The widget already has a parent")
        self._children.append(child)
        child.handle_added_to_widget(self)
        if child.visible:
            self._visible_children.append(child)
            self._layout_update_required = True
            child.load()

    def remove_widget(self, child: "Widget") -> bool:
        """
        Removes a child widget

        :param child: The child to be removed
        :return: True if the child was found
        """
        self.repaint()
        self._layout_update_required = True
        found = False
        if child in self._children:
            found = True
            self._children.remove(child)
        was_visible = child in self._visible_children
        if was_visible:
            self._visible_children.remove(child)
        child.handle_removed()
        return found

    def set_size(self, size: Size2DTypes):
        """
        Sets the view's size

        :param size: The new size in pixels
        :return:
        """
        size = Size2D(size)
        if self.size == size:
            return
        self.__dict__["size"] = size
        self.request_layout_update()
        if self.parent is not None:
            self.parent.request_layout_update()

    def set_position(self, position: Pos2DTypes):
        """
        Sets the view's position

        :param position: The new position relative to the parent's upper left corner
        :return:
        """
        position = Pos2D(position)
        if self.position == position:
            return
        self.__dict__["position"] = position
        self.repaint()
        self.request_layout_update()
        if self.parent is not None:
            self.parent.request_layout_update()

    def get_bounding(self) -> Bounding2D:
        """
        Returns the Widget's bounding as Bounding2D

        :return: The bounding
        """
        return Bounding2D((self.position, self.size))

    def set_visible(self, state: bool = True):
        """
        Defines the new visibility state

        :param state: The new state
        """
        if self.visible == state:
            return
        self.__dict__["visible"] = state
        self.repaint()
        if self.parent is not None:
            self.parent._handle_visibility_changed(self)

    def set_alpha(self, alpha: float):
        """
        Sets the widget's opacity.

        :param alpha: The new opacity / alpha value. From 0.0 (invisible) to 1.0 (fully visible)
        """
        if self.__dict__["alpha"] == alpha:
            return
        if self.alpha == 0.0 and self.visible:
            self.set_visible(False)
        if self.alpha > 0.0 and not self.visible:
            self.set_visible(True)
        self.__dict__["alpha"] = alpha
        self.repaint()

    def to_top(self, child: Widget) -> None:
        """
        Moves this view to the top of the view hierarchy

        :param child: The child to move to the top
        """
        if child in self._visible_children:
            self._visible_children.remove(child)
            self._visible_children.append(child)
        self._children.remove(child)
        self._children.append(child)

    def to_bottom(self, child: Widget) -> None:
        """
        Moves this view to the bottom of the view hierarchy

        :param child: The child to move to the bottom
        """
        if child in self._visible_children:
            self._visible_children.remove(child)
            self._visible_children.insert(0, child)
        self._children.remove(child)
        self._children.insert(0, child)

    def _handle_visibility_changed(self, child: Widget) -> None:
        """
        Called when a child's visibility state has changed

        :param child: The element
        """
        if not child.visible:
            if child in self._visible_children:
                self._visible_children.remove(child)
            child.handle_unload()
            child.temp_cache.clear()
        else:
            if child not in self._visible_children:
                self._visible_children.append(child)
            child.handle_load()

    def request_layout_update(self) -> None:
        """
        Called when the layout shall be recalculated at the next painting cycle
        """
        self._layout_update_required = True

    def scale(self, value: int | float | tuple) -> int:
        """
        Computes the scaled base (point) size converted to effective pixel size
        for this element

        :param value: The size value, e.g. a base font size
        :return: The optimum size for this view
        """
        if isinstance(value, tuple):
            tuple([int(round(element * self.dpi_scaling)) for element in value])
        return int(round(value * self.dpi_scaling))

    def get_relative_coordinate(self, coordinate) -> tuple[Widget, float, float] | None:
        """
        Receives the widget hit and the coordinates within the widget

        :param coordinate: The relative coordinate
        :return: None if no widget was hit,
            otherwise Widget, RelativeX, Relative Y
        """
        coord = [coordinate[0], coordinate[1]]
        width, height = self.size.to_tuple()
        if coord[0] < 0 or coord[1] < 0 or coord[0] > width or coord[1] > height:
            return None
        for child in reversed(self._visible_children):  # prefer child covering us
            child: Widget
            child_coord = child.position
            relative_coordinate = [coord[0] - child_coord.x, coord[1] - child_coord.y]
            result = child.get_relative_coordinate(relative_coordinate)
            if result is not None:
                return result
        if not self.sensitive:  # skip if it can not be clicked itself
            return None
        return self, coord[0], coord[1]

    def set_paint_required(self):
        """
        Flags the view that a paint is required, e.g. because a child view was modified.

        In difference to :meth:`repaint` this method does not invalidate the view's own caches. If you want to
        enforce a full repaint of the view call :meth:`repaint`.
        """
        if self.parent:
            self.parent.set_paint_required()

    def repaint(self):
        """
        Flags this view that a full repaint is required. Parent view's get notified that a general repaint of the
        window is required.
        """
        self.set_paint_required()
        # TODO invalidate paint caches here etc.

    def invalidate_layout(self):
        """
        Flags the view that an update is required
        """
        self._layout_update_required = True

    def update_layout(self):
        """
        Updates the view's layout recursive
        """
        for child in self._children:
            child: Widget
            child.update_layout()

    def paint_recursive(self, paint_event: PaintEvent):
        """
        Paints the view hierarchy recursive

        :param paint_event: The repaint event
        """
        self.handle_paint(paint_event)
        canvas = paint_event.canvas
        for child in self._visible_children:
            child: Widget
            canvas.push_state()
            canvas.add_offset_shift(child.position)
            child.paint_recursive(paint_event)
            canvas.pop_state()

    def paint_recursive_int(self, canvas: Canvas, config: dict):
        """
        Triggers an recursive repaint

        :param canvas: The target canvas
        :param config: Advanced rendering settings
        """
        paint_event = PaintEvent(widget=self, canvas=canvas, config=config)
        self.paint_recursive(paint_event)

    def cache_data(
        self,
        identifier: str,
        builder: Callable[[object], Any],
        parameters: object | None = None,
    ) -> Any:
        """
        Tries to retrieve given element from cache.

        If the element is not stored in the cache it will be created
        using the builder callback which should await a single parameter and return a single value.
        If parameters (optional) is passed it will be verified if the parameters were modified.

        :param identifier: The identifier. Either a string or a dictionary with a configuration.
        :param builder: The function to call if the value does not exist
        :param parameters: If the data may dynamically change using the same identifier, pass it too
        :return: The data
        """
        return self.temp_cache.cache(
            identifier=identifier, builder=builder, parameters=parameters
        )


__all__ = ["Widget", "PaintEvent", "Color"]
