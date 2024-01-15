"""
Implements the selector widget which lets the user choose from a set of values
"""
from __future__ import annotations
from typing import Any, Union

from pydantic import BaseModel

from scistag.vislog import LogBuilder
from scistag.vislog.widgets.value_widget import LValueWidget
from scistag.vislog.widgets.base_events import LValueChangedCallable, LValueChangedEvent


class LSelect(LValueWidget):
    """
    The LSelect widget allows the selection of one value of a set of values represented
    by a <select> control in HTML, also known as Combobox in other UI frameworks.
    """

    class Element(BaseModel):
        """
        Defines a single element of an LSelect widget
        """

        text: str
        """The text to be displayed"""
        data: Union[Any, None] = None
        """The data"""
        default: bool = False
        """Defines if this shall be the default element"""
        disabled: bool = False
        """Defines if this value is disabled"""
        index: int = -1
        """The element's index. Will be auto-assigned"""
        value: Union[str, None] = None
        """A unique value key, should be alphanumeric. Will be auto-assigned if None"""
        html_class: Union[str, None] = None
        """The html class to be used"""
        html_style: Union[str, None] = None
        """Additional style flags"""

    def __init__(
        self,
        builder: LogBuilder,
        elements: list[Element | dict | str, tuple[str, str]],
        name: str = "",
        on_change: Union[LValueChangedCallable, None] = None,
        target: str | None = None,
        default_index: int = -1,
        insert: bool = True,
        html_class: Union[str, None] = None,
        html_style: Union[str, None] = None,
    ):
        """
        :param builder: The builder object
        :param elements: The elements to be added. Either fully described as
            Element, as dictionary containing all non-default properties,
            only the caption text or a text, value tuple.
        :param name: The control's unique name
        :param on_change: Called when ever the element's value was modified
        :param target: Cache target key. If defined all updates to the slider's value
            will be stored in the cache variable defined
        :param default_index: The initial selected index (if not otherwise defined in
            the element list)
        :param html_class: The html class to be used for this widget
        :param html_style: Additional html style flags to be applied
        :param insert: Defines if the widget shall be inserted asap. True by default.
        """
        super().__init__(
            builder=builder,
            name=name,
            target=target,
            on_change=on_change,
            value="",
            html_class=html_class,
            html_style=html_style,
        )

        def setup(element):
            if isinstance(element, dict):
                return self.Element.model_validate(element)
            elif isinstance(element, str):
                return self.Element(text=element)
            if isinstance(element, tuple):
                return self.Element(text=element[0], value=element[1])
            return element

        self.elements = [setup(cur) for cur in elements]
        """The elements which can be selected"""

        self._selected: LSelect.Element | None = None
        """The current index"""
        if default_index != -1 and 0 <= default_index < len(elements):
            for index, element in enumerate(self.elements):
                element.default = index == default_index
            self._selected = self.elements[default_index]
        else:
            self._selected = None if len(self.elements) == 0 else self.elements[0]

        self.value_dict: dict[str, LSelect.Element] = {}
        """Mapping from value to Element"""

        if insert:
            self.write()

    def write(self):
        script = f"""vl_handle_value_changed('{self.identifier}', this.value);"""

        add_flags = self._get_add_html_code()
        self.builder.add_html(
            f'<select id="{self.identifier}" oninput="{script}"{add_flags}>'
        )
        for index, cur in enumerate(self.elements):
            add_flags = ""
            cur.index = index
            if cur.default:
                add_flags += " selected"
                self._selected = cur
            if cur.disabled:
                add_flags += "disabled"
            if cur.html_class is not None:
                add_flags += f' class="{cur.html_class}"'
            if cur.html_style is not None:
                add_flags += f' style="{cur.html_style}"'
            if cur.value is None:
                value_name = f"element{index}"
                cur.value = value_name
            self.builder.add_html(f'<option value="{cur.value}"{add_flags}>')
            self.builder.add_html(cur.text)
            self.builder.add_html(f"</option>\n")
            self.value_dict[cur.value] = cur
        self.builder.add_html(f"</select>")
        if self._selected is not None:
            self.sync_value(self._selected.value, trigger_event=False)

    @property
    def selected(self) -> Element | None:
        """
        Returns the currently selected element

        :return: The selected element. None if None is selected
        """
        return self._selected

    @property
    def value(self) -> Element | None:
        """
        The current value
        """
        return "" if self.selected is None else self.selected.value

    def sync_value(self, new_value: str | None, trigger_event: bool = True):
        """
        Updates the value after modifications on client side

        :param new_value: The new value
        :param trigger_event: Defines if an event may be triggered
        """
        if self._value == new_value:
            return
        if new_value == "" or new_value is None:
            self._selected = None
        for cur in self.elements:
            if cur.value == new_value:
                self._selected = cur
                break
        super().sync_value(new_value, trigger_event)

    def element_by_value(self, value: str) -> Element | None:
        """
        Returns an element by its name

        :param value: The value to search for
        :return: The corresponding selected element, otherwise None
        """
        return self.value_dict.get(value, None)

    def __getitem__(self, item):
        return self.element_by_value(item)

    def __contains__(self, item):
        return item in self.value_dict

    def __len__(self):
        return len(self.elements)

    def get_value(self) -> str:
        return self.selected.value if self.selected is not None else ""
