"""
Defines VisualLogElement, a nestable data container storing the data of each log
component in a hierarchical manner.
"""
from __future__ import annotations

import time


class VisualLogElement:
    """
    Defines a single data element within the log.

    Each dynamic element in the target document, e.g. a html component, is
    presented by its own VisualLogElement.

    Each data element of the log can be updated individually. When the page is
    rendered the data of all elements is concatenated.

    An element can also contain nested elements.
    """

    def __init__(
        self,
        name: str,
        output_formats: list[str],
        parent: VisualLogElement | None = None,
    ):
        """
        :param name: The element's globally unique name
        :param output_formats: The output formats which shall be supported
        :param parent: The parent element
        """
        self.name = name
        """The element's globally unique name"""
        self.parent: VisualLogElement | None = parent
        """The element's parent element"""
        self.last_direct_change_time: float = time.time()
        """Timestamp when the element itself was directly extended the last time"""
        self.last_child_update_time: float = self.last_direct_change_time
        """Timestamp when an embedded sub-element was updated the last time"""
        self.data: dict[str, list[bytes | VisualLogElement]] = {
            element: [b""] for element in output_formats
        }
        """A dictionary storing the data for each output format type. 
        
        The data can be described as raw bytes string or via a nested sub element."""

    def add_data(self, output_format: str, data: bytes):
        """
        Adds a single data element to the log

        :param output_format: The output format to which the data element shall be
            added
        :param data: The data to add
        """
        if not isinstance(data, bytes):
            breakpoint()
        self.last_direct_change_time = time.time()
        data_list = self.data[output_format]
        data_list[-1] += data
        if self.parent is not None:
            self.parent.handle_child_changed(self.last_direct_change_time)

    def add_sub_element(self, name: str) -> VisualLogElement:
        """
        Adds a new, nested element which can be updated indivdually

        :param name: The sub element's name
        :return: The element handle
        """
        new_element = VisualLogElement(name, list(self.data.keys()), parent=self)
        self.last_direct_change_time = time.time()
        self.last_child_update_time = self.last_direct_change_time
        if self.parent is not None:
            self.parent.handle_child_changed(self.last_direct_change_time)
        for output_format in self.data.keys():
            self.data[output_format].append(new_element)
            self.data[output_format].append(b"")
        return new_element

    def build(self, output_format: str) -> bytes:
        """
        Combines all data elements to the full data bytes string

        :param output_format: The output format to retrieve
        :return: The data
        """
        output = b""
        for element in self.data[output_format]:
            if isinstance(element, VisualLogElement):
                data = element.build(output_format)
            else:
                data = element
            output += data
        return output

    def handle_child_changed(self, update_time: float):
        """
        Is called whenever a child's content was modified

        :param update_time: The current time
        """
        self.last_child_update_time = update_time
        if self.parent is not None:
            self.parent.handle_child_changed(update_time)

    def clear(self):
        """
        Clears the whole element and all sub elements
        """
        self.data: dict[str, list[bytes | VisualLogElement]] = {
            element: [b""] for element in self.data.keys()
        }
