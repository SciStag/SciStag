from __future__ import annotations
from .data_stag_common import StagDataTypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scistag.datastag.data_stag_vault import DataStagVault


class DataStagElement:
    """
    Root class of a single database element
    """

    def __init__(self, vault):
        """
        Initializer

        :param vault: The vault in which the element is stored
        """
        self.data = None
        self.vault: DataStagVault = vault  # The element's vault
        self.simple = True  # Simple data type?
        self.name: str | None = None  # The element's name
        self.parent: DataStagElement | None = None
        "The parent element (e.g. a list containing the element)"
        self.deprecation_time: float | None = None
        "Time when this element shall be destroyed"
        self.version_counter: int = 0
        "The element's update counter"

    def set_value(self, value: StagDataTypes, deprecation_time: float | None = None):
        """
        Sets the element's new value

        :param value: The value
        :param deprecation_time: The deprecation server time
        """
        self.data = value
        self.deprecation_time = deprecation_time
        self.version_counter += 1

    def get_value(self) -> StagDataTypes:
        """
        Returns the element's data

        :return: The data with it's original type
        """
        return self.data
