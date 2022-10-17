from __future__ import annotations
import time
from threading import RLock, Event
from .service import RemoteService
from .service import RemoteReturnTypes

RemoteTaskId = int
"Task execution ID type"


class RemoteTask:
    """
    This function handles the execution of a remotely executed function
    """

    ERROR = "_error"  # Error identifier

    def __init__(self, task_id: RemoteTaskId, service: RemoteService,
                 target_function: str, parameters: dict,
                 timeout_s: float = -1.0):
        """
        :param task_id: The task's unique id
        :param target_function: The function to execute
        :param parameters: The parameters to pass into the function
        :param timeout_s: The timeout in seconds after which this task
            automatically gets cancelled.
        """
        self._task_id = task_id
        "The task's unique id"
        self._service = service
        "The service which provides the function"
        self._target_function: str = target_function
        "The identifier of the function to call"
        self._access_lock = RLock()
        "Data access lock"
        self._event = Event()
        "The even to be triggered to wake up sleeping receivers"
        self._parameters: dict = parameters
        "The function's parameters"
        self._result: dict | None = None
        "The function's result"
        self._sleep_interval = 0.0
        "Interval of sleep"
        self.timeout_s = timeout_s
        "The timeout time"
        self._deprecation_time = -1.0 if self.timeout_s == -1.0 else time.time() + timeout_s

    def get_service(self) -> RemoteService:
        """
        Returns the service being required for this task

        :return: The service
        """
        return self._service

    def get_id(self) -> RemoteTaskId:
        """
        Returns the task's unique ID

        :return: Unique task ID
        """
        return self._task_id

    def get_target_function(self) -> str:
        """
        Returns the target function

        :return: The function's identifier
        """
        return self._target_function

    def get_parameters(self):
        """
        Returns the parameters passed into the function

        :return: The parameters
        """
        return self._parameters

    def get_result(self) -> dict | None:
        """
        Returns the task's result

        :return: The result data (if it's available already)
        """
        with self._access_lock:
            return self._result

    def get_error(self) -> str | None:
        """
        Returns the error string if an error occurred

        :return: The error string
        """
        with self._access_lock:
            if self._result is None:
                return None
            if self.ERROR in self._result:
                return self._result[self.ERROR]
            return None

    def get_deprecation_time(self) -> float:
        """
        Returns the time when this task becomes invalid

        :return: The deprecation time (see time.time()). If -1 the task does not deprecate.
        """
        return self._deprecation_time

    def assign_result(self, result):
        """
        Assigns the result to the task

        :param result: The task's result
        """
        with self._access_lock:
            self._result = result
        self._event.set()

    def assign_error(self, error: str):
        """
        Assigns an error to the result

        :param error: The error string
        """
        with self._access_lock:
            self._result = {self.ERROR: error}
        self._event.set()

    def wait(self, timeout_s=-1) -> bool:
        """
        Waits for the finishing of the execution up to a given timeout

        :param timeout_s: The maximum waiting time in seconds
        :return: True if the data is available
        """
        start_time = time.time()
        done = False
        while True:
            if self._event.wait(self._sleep_interval):
                self._event.clear()
            with self._access_lock:
                if self._result is not None:
                    done = True
                    break
            cur_time = time.time()
            if timeout_s != -1 and cur_time > start_time + timeout_s:
                return done
        return done

    def unwrap(self) -> RemoteReturnTypes | None:
        """
        Unwraps the result dictionary to a single value if it just contains a
        single value

        :return: A dictionary in case of multiple return values otherwise the
            single value
        """
        with self._access_lock:
            if self._result is None:
                return None
            if len(self._result) == 1 and RemoteService.RESULT_VALUE in self._result:
                return self._result[RemoteService.RESULT_VALUE]
            return self._result
