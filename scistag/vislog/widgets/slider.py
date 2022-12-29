"""
Implements the class :class:`LButton` which allows the user to add an
interaction button to a log.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.log_elements import HTMLCode
from scistag.vislog.options import LSliderOptions
from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.event import LEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import VisualLogBuilder

VALUE_CHANGE_EVENT_TYPE = "widget_value_change"
"Defines an event which is risen by a value change, e.g. of a slider or a combo box"


class LValueChangeEvent(LEvent):
    """
    An event which is triggered when the value of an object changed
    """

    def __init__(self, widget: LWidget, value, **params):
        """
        :param widget: The widget such as a LButton which was modified
        :param value: The new value
        :param params: Additional parameters
        """
        super().__init__(event_type=VALUE_CHANGE_EVENT_TYPE, widget=widget, **params)
        self.value = value

    value: int | float | str
    """The widget's new value"""


class LSlider(LWidget):
    """
    The LSlider defines a horizontal or vertical slider which lets you select a value
    in a defined range and with a defined stepping.
    """

    def __init__(
        self,
        builder: "VisualLogBuilder",
        value: float | int,
        min_value: float | int,
        max_value: float | int,
        stepping: float | int | None = None,
        on_change: Union[Callable, None] = None,
        name: str = "Slider",
        options: LSliderOptions | None = None,
        insert: bool = True,
        **kwargs,
    ):
        """
        :param builder: The log builder to which the button shall be added
        :param value: Initial value
        :param min_value: Minimum value
        :param max_value: Maximum value
        :param stepping: Value stepping.

            If not defined integer value step with 1 and float values continuously.
        :param on_change: Called when ever the slider was modified
        :param name: The slider's unique name, for easier debugging
        :param style: The slider's style
        :param insert: Defines if the element shall be inserted into the log
        :param kwargs: Additional arguments will override the corresponding settings
            in the :class:`LSliderOptions`.
        """
        super().__init__(name=name, builder=builder)
        self._value = value
        "The slider's initial value"
        self.min_value = min_value
        "The minimum value the slider can be moved to"
        self.max_value = max_value
        "The maximum value the slider can be moved to"
        self.stepping = stepping
        "The slider's stepping size"
        self.on_change = on_change
        """The event to be called when the slider's value was modified"""
        self.options: LSliderOptions = (
            options if options is not None else LSliderOptions()
        )
        """The slider's options.
        
        Note that modifications to the style after the widget's creation do usually 
        not affect the widget anymore as it was already written to the log"""
        self.apply_options(kwargs)
        self.html_value_code: HTMLCode = HTMLCode("")
        """
        Contains the HTML code which visualizes the value. If style.show_value
        is set to "custom" this can be used to customize the position at which the
        slider's value shall be visualized such as in another table column or row.
        
        See :class:`LSliderGroup` for an example implementation.
        """
        if insert:
            self.insert_into_page()

    def write(self):
        script = f"""vl_handle_value_changed('{self.name}', this.value);"""
        out_name = self.name + "_out"
        if self.options.show_value == "custom" or self.options.show_value:
            script += (
                f"document.getElementById('{out_name}').value = '{self.options.value_prefix}'+("
                f"parseFloat((this.value*{self.options.value_scaling})."
                f"toFixed({self.options.value_max_digits}))+'{self.options.value_postfix}')"
            )
        if self.options.vertical:
            v_width = self.options.vertical_width
            v_height = self.options.vertical_height
            style = (
                f"height:{v_height}; width:{v_width}; "
                f"-webkit-appearance: slider-vertical; "
            )
        else:
            h_width = self.options.horizontal_width
            h_height = self.options.horizontal_height
            style = f"width:{h_width}; height:{h_height};"
            style += "vertical-align: middle;"
        html = ""
        if not self.options.vertical:
            html += "<span style='vertical-align: middle'>"
        html += (
            f'<input id="{self.name}" type="range" value="{self._value}" '
            f'step="{self.stepping}" min="{self.min_value}" '
            f'max="{self.max_value}" '
            f'style="{style}" '
            f'oninput="{script}" />'
        )
        value_html = ""
        if self.options.show_value:
            scaled_value = self._value * self.options.value_scaling
            scaled_value = f"{scaled_value:0.{self.options.value_max_digits}f}"
            scaled_value = scaled_value.rstrip("0").rstrip(".")
            if len(scaled_value) == 0:
                scaled_value = "0"
            value = (
                f"{self.options.value_prefix}{scaled_value}{self.options.value_postfix}"
            )
            if self.options.value_edit_field:
                edit_style = "width: 44pt;"
                if self.options.value_bold:
                    edit_style += "font-weight: bold;"
                value_html = (
                    f'<input type="number" id="{out_name}" '
                    f'style="{edit_style}"'
                    f'step="{self.stepping}" min="{self.min_value}" '
                    f'max="{self.max_value}" '
                    f'value="{self.value}"'
                    f'oninput="document.'
                    f"getElementById('{self.name}').value=this.value\" />"
                )
            else:
                value_html = f"<output id='{out_name}'>{value}</output>"
            if self.options.value_bold:
                value_html = "<b>" + value_html + "</b>"
            if self.options.show_value == "custom":
                self.html_value_code = value_html
                html += "</span>"
            elif not self.options.vertical:
                html += " " + value_html
                html += "</span>"
        if self.options.vertical:
            if len(value_html) > 0:
                self.builder.table(
                    [[HTMLCode(html)], [HTMLCode(f"{value_html}")]],
                    seamless=True,
                )
            else:
                self.builder.html(html)
        else:
            self.builder.html(html)
            if self.options.vertical and len(value_html) > 0:
                self.builder.html(f"{value_html}")

    def handle_event(self, event: "LEvent"):
        if event.event_type == VALUE_CHANGE_EVENT_TYPE:
            self.call_event_handler(self.on_change, event)
        super().handle_event(event)

    @property
    def value(self) -> int | float:
        """
        The current value
        """
        return self._value

    @value.setter
    def value(self, new_val: float | int):
        val_range = self.max_value - self.min_value
        if val_range == 0.0:
            return
        tolerance = val_range / 1000.0
        if isinstance(self._value, float):
            new_val = float(new_val)
            if abs(self._value - new_val) < tolerance:
                return
        else:
            new_val = int(round(float(new_val)))
            if self._value == new_val:
                return
        self._value = new_val
        change_event = LValueChangeEvent(widget=self, value=new_val)
        self.raise_event(change_event)

    def get_value(self) -> int | float | bool | None:
        return self._value
