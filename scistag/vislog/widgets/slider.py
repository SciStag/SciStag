"""
Implements the class :class:`LButton` which allows the user to add an
interaction button to a log.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Union

from scistag.vislog.log_elements import HTMLCode
from scistag.vislog.options import LSliderOptions
from scistag.vislog.widgets.base_events import LValueChangedEvent
from scistag.vislog.widgets.log_widget import LWidget
from scistag.vislog.widgets.event import LEvent

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class LSlider(LWidget):
    """
    The LSlider defines a horizontal or vertical slider which lets you select a value
    in a defined range and with a defined stepping.
    """

    def __init__(
        self,
        builder: "LogBuilder",
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
            html, value_html = self._setup_value_display(html, out_name)
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

    def _setup_value_display(self, html, out_name):
        """
        Setups an element which always visualizes the slider's current value, either
        as a simple text or as an editable field.

        :param html: The current html code for the widget
        :param out_name: The widget's name in the DOM
        :return: The html code of the whole widget, the html code of the value display
        """
        scaled_value = self._value * self.options.value_scaling
        scaled_value = f"{scaled_value:0.{self.options.value_max_digits}f}"
        scaled_value = scaled_value.rstrip("0").rstrip(".")
        if len(scaled_value) == 0:
            scaled_value = "0"
        value = f"{self.options.value_prefix}{scaled_value}{self.options.value_postfix}"
        if self.options.value_edit_field:
            value_html = self._setup_edit_field(out_name)
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
        return html, value_html

    def _setup_edit_field(self, out_name):
        """
        Setups an edit field in which the number can be entered via keyboard

        :param out_name: The output name of the main field
        :return: The html code for the edit field
        """
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
        return value_html

    def handle_event(self, event: "LEvent"):
        if isinstance(event, LValueChangedEvent):
            self.call_event_handler(self.on_change, event)
        super().handle_event(event)

    @property
    def value(self) -> int | float:
        """
        The current value
        """
        return self._value

    def sync_value(self, new_value: float | int):
        """
        Updates the value after modifications on client side

        :param new_value: The new value
        """
        val_range = self.max_value - self.min_value
        if val_range == 0.0:
            return
        tolerance = val_range / 1000.0
        if isinstance(self._value, float):
            new_value = float(new_value)
            if abs(self._value - new_value) < tolerance:
                return
        else:
            new_value = int(round(float(new_value)))
            if self._value == new_value:
                return
        self._value = new_value
        change_event = LValueChangedEvent(widget=self, value=new_value)
        self.raise_event(change_event)

    def get_value(self) -> int | float | bool | None:
        return self._value
