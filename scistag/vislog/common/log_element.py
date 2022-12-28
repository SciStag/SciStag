"""
Defines LogElement, a nestable data container storing the data of each log
component in a hierarchical manner.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class LogElementReference:
    """
    Defines a log element's reference to linearly handled all elements and sub elements.

    See :meth:`LogElement.list_recursive`
    """

    name: str
    """The element's relative name"""
    path: str
    """The element's absolute name path, separated by dots"""
    element: "LogElement"
    """The referred element"""


class LogElement:
    """
    Defines a single data element within the log.

    Each dynamic element in the target document, e.g. a html component, is
    presented by its own LogElement.

    Each data element of the log can be updated individually. When the page is
    rendered the data of all elements is concatenated.

    An element can also contain nested elements.
    """

    def __init__(
        self,
        name: str,
        output_formats: list[str],
        parent: LogElement | None = None,
    ):
        """
        :param name: The element's globally unique name
        :param output_formats: The output formats which shall be supported
        :param parent: The parent element
        """
        self.name = name
        """The element's globally unique name"""
        self.parent: LogElement | None = parent
        """The element's parent element"""
        self.last_direct_change_time: float = time.time()
        """Timestamp when the element itself was directly extended the last time"""
        self.last_child_update_time: float = self.last_direct_change_time
        """Timestamp when an embedded sub-element was updated the last time"""
        self.direct_modifications: int = 0
        """Count of direct modifications of this cell"""
        self.total_modifications: int = 0
        """Count of direct and indirect modifications of this cell"""
        self.data: dict[str, list[bytes | LogElement]] = {
            element: [b""] for element in output_formats
        }
        """A dictionary storing the data for each output format type. 
        
        The data can be described as raw bytes string or via a nested sub element."""
        self.sub_elements: dict[str, LogElement] = {}
        """
        Dictionary of nested sub elements 
        """
        self.flags: dict = {}
        """
        Usage specific flags (such as the back-link to a widget)
        """

    def add_data(self, output_format: str, data: bytes):
        """
        Adds a single data element to the log

        :param output_format: The output format to which the data element shall be
            added
        :param data: The data to add
        """
        self.last_direct_change_time = time.time()
        self.direct_modifications += 1
        self.total_modifications += 1
        data_list = self.data[output_format]
        data_list[-1] += data
        if self.parent is not None:
            self.parent.handle_child_changed(self.last_direct_change_time)

    def add_sub_element(self, name: str) -> LogElement:
        """
        Adds a new, nested element which can be updated indivdually

        :param name: The sub element's name
        :return: The element handle
        """
        new_element = LogElement(name, list(self.data.keys()), parent=self)
        self.last_direct_change_time = time.time()
        self.last_child_update_time = self.last_direct_change_time
        self.direct_modifications += 1
        self.total_modifications += 1
        if self.parent is not None:
            self.parent.handle_child_changed(self.last_direct_change_time)
        for output_format in self.data.keys():
            self.data[output_format].append(new_element)
            self.data[output_format].append(b"")
        self.sub_elements[name] = new_element
        return new_element

    def build(self, output_format: str) -> bytes:
        """
        Combines all data elements to the full data bytes string

        :param output_format: The output format to retrieve
        :return: The data
        """
        output = b""
        for element in self.data[output_format]:
            if isinstance(element, LogElement):
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
        self.total_modifications += 1
        if self.parent is not None:
            self.parent.handle_child_changed(update_time)

    def clear(self):
        """
        Clears the whole element and all sub elements
        """
        self.direct_modifications += 1
        self.total_modifications += 1
        self.last_direct_change_time = time.time()
        self.last_child_update_time = self.last_direct_change_time
        self.data: dict[str, list[bytes | LogElement]] = {
            element: [b""] for element in self.data.keys()
        }
        self.flags = {}

    def clone(self, parent=None) -> LogElement:
        """
        Creates a copy of this element and all sub elements

        :return: A copy of this element
        """
        new_element = LogElement(self.name, output_formats=list(self.data.keys()))
        new_element.parent = parent
        new_element.last_direct_change_time = self.last_direct_change_time
        new_element.last_child_update_time = self.last_child_update_time
        new_element.total_modifications = self.total_modifications
        new_element.direct_modifications = self.direct_modifications
        new_element.flags = dict(self.flags)
        for cur_sub_name, cur_sub in self.sub_elements.items():
            sub_clone = cur_sub.clone(parent=self)
            new_element.sub_elements[cur_sub_name] = sub_clone
        for key, data_list in self.data.items():
            for element in data_list:
                if isinstance(element, LogElement):
                    new_element.data[key].append(new_element.sub_elements[element.name])
                else:
                    new_element.data[key].append(element)
        return new_element

    def list_elements_recursive(
        self, path: str = "", target: list[LogElementReference] | None = None
    ) -> list[LogElementReference]:
        """
        Creates a linear list of this element and all its sub elements in hierarchical
        order.

        This can be used (for example) to find the newest modifications in the element
        tree.

        :param path: The absolute path name. Starts with and empty string and is
            extended to a concatenated list of elements, separated by dots.
        :param target: The list to which the new elements shall be stored.
        :return: The final list
        """
        if target is not None:
            if len(path) == 0:
                target.clear()
        else:
            target = []
        target.append(
            LogElementReference(name=self.name, path=path + self.name, element=self)
        )
        for _, value in self.sub_elements.items():
            value.list_elements_recursive(path=path + self.name + ".", target=target)
        return target

    def __contains__(self, item):
        """
        Defines if given sub element exists

        :param item: The element's name
        :return: True if the sub element with given name does exist
        """
        return item in self.sub_elements

    def __getitem__(self, item) -> LogElement:
        """
        Returns given sub element.

        Raises KeyError if the element does not exist.

        :param item: The element's name
        :return: The element
        """
        return self.sub_elements[item]
