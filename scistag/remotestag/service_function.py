from __future__ import annotations
import abc

import numpy as np


class RemoteFunction:
    """
    Base class for a remote callable function
    """

    RESULT_VALUE = "_resultValue"
    "Result value identifier"
    INPUT_VALUE = "_value"
    "The input value"

    def __init__(self, service: "RemoteService", function_name: str):
        """
        Initializer
        :param service: The service to which this function shall be added
        :param function_name:
        """
        self.service = service
        service_identifier = service.get_identifier()
        self.full_identifier = f"{service_identifier}.{function_name}"
        self.service.register_function(self)

    def wrap(self,
             result_value: str | int | bool | float | bytes | np.ndarray):
        """
        Returns a dictionary wrapping a single result value
        :param result_value: The simple result value
        :return: The dictionary to be stored in the task's result
        """
        return {self.RESULT_VALUE: result_value}

    def unwrap(self, input_dict: dict) -> \
        str | int | bool | float | bytes | np.ndarray | dict:
        """
        Returns a dictionary wrapping a single result value
        :param input_dict: A dictionary
        :return: The single value in the dictionary if wrapped, otherwise the dictionary
        """
        if self.INPUT_VALUE in input_dict:
            return input_dict[self.INPUT_VALUE]
        return input_dict

    @abc.abstractmethod
    def run(self, parameters: dict) -> dict:
        """
        Overwrite this with the code you want to execute
        :param parameters: The input parameters
        :return: The result
        """
        return {}

    def get_full_identifier(self) -> str:
        """
        Returns the function's full identifier
        :return: The identifier including the domain
        """
        return self.full_identifier
