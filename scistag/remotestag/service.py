from __future__ import annotations
from typing import Callable, Union
from threading import RLock
from .service_function import RemoteFunction

RemoteCallback = Callable[[dict], dict]
"Defines a callable service function"
RemoteParameterTypes = Union[dict, str, float, bool, int, bytes]
"""
Defines the valid parameter types to be passed into a function.
Single parameters get wrapped into a dict with a single key named _value
"""
RemoteReturnTypes = Union[dict, str, float, bool, int, bytes]
"""
Defines the valid return types. Single values will be stored in the single 
key _resultValue in a dictionary
"""


class RemoteService:
    """
    Defines a service hosted on this machine. A service consists of one or
    multiple services sharing the same data.
    """

    INPUT_VALUE = "_value"
    "Key for single input value in the parameter dictionary"
    RESULT_VALUE = "_resultValue"
    "Key for the result value in the dictionary"

    def __init__(self, identifier: str, multithreading: bool = True):
        """
        :param identifier: The service's unique identifier in the form
            com.company.ai.inference.yolov2.

            A service's name is not allowed to be contained within another
            service's name.
        :param multithreading: Defines if this data can be accessed from multiple
            threads or is using thread local data (such as many ML libraries).
        """
        self._identifier = identifier
        "The service's identifier"
        self._multithreading = multithreading
        "Defines if the service is multithreading capable"
        self._functions: dict[str, Union[RemoteFunction, RemoteCallback]] = {}
        "Set of all registered functions"
        self._lock = RLock()
        "Data access lock"
        self._started = False
        "Defines the service was already stared"

    def provides_function(self, identifier: str) -> bool:
        """
        Returns if the function is known

        :param identifier: The function identifier
        :return: True on success
        """
        return identifier in self._functions.keys()

    def get_identifier(self) -> str:
        """
        Returns the service's identifier

        :return: The identifier string
        """
        return self._identifier

    def get_single_threaded(self) -> bool:
        """
        Returns True if this service does NOT support multithreading and
        needs it's own worker thread

        :return: True if not multithreading capable
        """
        return not self._multithreading

    def register_function(self, function: RemoteFunction) -> bool:
        """
        Registers a new function. Functions can only be registered before the
        service was started.

        :param function: The function to register
        :return True on success:
        """
        with self._lock:
            if self._started:
                raise Exception(
                    "Service already started, can not register additional functions.")
            function_identifier = function.get_full_identifier()
            if function_identifier in self._functions:
                return False
            self._functions[function_identifier] = function
            return True

    def register_callback(self, name: str, callback: RemoteCallback) -> bool:
        """
        Registers a new function. Functions can only be registered before the
        service was started.

        :param name: The function's name
        :param callback: The callback function to be called
        :return True on success:
        """
        with self._lock:
            if self._started:
                raise Exception(
                    "Service already started, can not register additional functions.")
            name = f"{self._identifier}.{name}"
            if name in self._functions:
                return False
            self._functions[name] = callback
            return True

    def run_task(self, function_name: str, parameters: RemoteParameterTypes,
                 unwrap=False) -> RemoteReturnTypes:
        """
        Executes a task

        :param function_name: The function's name
        :param parameters: The function's parameters. Either as base type for a
            single parameter or as dictionary
        :param unwrap: Defines if a single value result shall not be wrapped
            into a dictionary
        :return: The function's results
        """
        if not isinstance(parameters, dict):
            parameters = {self.INPUT_VALUE: parameters}
        function = None
        with self._lock:
            if not self._started:
                self.initialize()
                self._started = True
            if self._identifier not in function_name:
                function_name = f"{self._identifier}.{function_name}"
            if function_name in self._functions:
                function = self._functions[function_name]
        if function is None:
            return {"error": f"Unknown function: {function_name}"}
        if isinstance(function, RemoteFunction):
            function: RemoteFunction
            result = function.run(parameters)
        else:
            function: RemoteCallback
            result = function(parameters)
        if not isinstance(result, dict):
            result = {"_resultValue": result}
        return result if not unwrap else self.unwrap(result)

    @classmethod
    def unwrap(cls, result: dict) -> RemoteReturnTypes:
        """
        Unwraps a potentially single value result

        :param result: The original function result
        :return: The single value if there is just one element, otherwise
            the dictionary
        """
        if cls.RESULT_VALUE in result and len(result) == 1:
            return result[cls.RESULT_VALUE]
        return result

    def initialize(self):
        """
        Overwrite this method with your initialization code.

        If this service is thread bound it's guaranteed to be executed on the
         later execution thread.
        """

    def deinitialize(self):
        """
        Overwrite this method with your deinitialization code.

        If this service is thread bound it's guaranteed to be
        executed on the execution thread.
        """
