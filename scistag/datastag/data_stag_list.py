from __future__ import annotations
from .data_stag_element import DataStagElement


class DataStagList(DataStagElement):
    """
    Defines a dynamic data stag list
    """

    def __init__(self, vault: "DataStagVault"):
        """
        The data vault
        :param vault: The owning vault
        """
        super().__init__(vault=vault)
        self.simple = False  # Complex data type
        self.list_elements: list[DataStagElement] = []
        "List of all elements"
        self.objects_with_timeout = False
        "Defines if the list contains any element with timeout"

    def collect_garbage(self, time_s: float):
        """
        Removes all outdated elements
        :param time_s: The current server time
        """
        if not self.objects_with_timeout:
            return 0
        deleted_count = 0
        for index, element in enumerate(reversed(self.list_elements)):
            element: DataStagElement
            if (
                    element.deprecation_time is not None
                    and time_s >= element.deprecation_time
            ):
                del self.list_elements[-(index + 1 - deleted_count)]
                deleted_count += 1
        if len(self.list_elements) == 0:
            self.objects_with_timeout = False
        return deleted_count

    def get_elements(self, start: int, end: int | None, time_s: float | None = None):
        """
        Returns all elements in the range start to end
        :param start: The first index
        :param end: The stop index
        :param time_s: The current server time
        """
        result = []
        deprecated = []
        if self.objects_with_timeout:
            for index, element in enumerate(self.list_elements):
                if (
                        element.deprecation_time is not None
                        and time_s is not None
                        and time_s >= element.deprecation_time
                ):
                    deprecated.append(index)  # remember for later deletion
                    continue
                result.append(element.get_value())
        else:
            result = [element.get_value() for element in self.list_elements]
        for element in reversed(deprecated):  # remove deprecated elements
            del self.list_elements[element]
        if len(self.list_elements) == 0:
            self.objects_with_timeout = False
        if end is None:
            return result[start:]
        else:
            return result[start:end]

    def add_elements(
            self,
            elements: list[DataStagElement],
            deprecation_time: float | None = None,
            index: int = -1,
    ) -> int:
        """
        Adds an element at the end of the list

        :param elements: The new elements
        :param deprecation_time: If set it defines when the element will deprecate
        :param index: Defines where the element shall be inserted
        """
        self.objects_with_timeout = (
                self.objects_with_timeout or deprecation_time is not None
        )
        if index == -1 or index >= len(self.list_elements):
            self.list_elements.extend(elements)
        else:
            if index == 0:
                self.list_elements = elements + self.list_elements
            else:
                self.list_elements = (
                        self.list_elements[0:index] + elements + self.list_elements[
                                                                 index:]
                )
        return len(self.list_elements)

    def pop_element(
            self, index=-1, deprecation_time: float | None = None
    ) -> DataStagElement | None:
        """
        Tries to remove a single element from the list

        :param index: The element's index
        :param deprecation_time: The current server time
        :return: The element if it was valid
        """
        if index < 0 and abs(index) <= len(self.list_elements):
            index = len(self.list_elements) + index
        if index < 0 or index >= len(self.list_elements):
            return None
        element = self.list_elements[index]
        del self.list_elements[index]
        if (
                deprecation_time is not None
                and element.deprecation_time is not None
                and deprecation_time >= element.deprecation_time
        ):
            return None
        return element
