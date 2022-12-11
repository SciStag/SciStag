from __future__ import annotations
from threading import Thread, Event, RLock
from .service_task import RemoteTask


class RemoteWorker(Thread):
    """
    Defines a worker which processes the remote tasks through one or multiple attached services
    """

    def __init__(self, service_handler: "RemoteServiceHandler", identifiers: list[str]):
        """
        Initializer

        :param service_handler: The owner which created us
        :param identifiers: The domains this worker is able to handle
        """
        super().__init__()
        self._terminate = False
        "Defines if the thread shall be terminated"
        self._lock = RLock()
        "Access lock"
        self._service_handler = service_handler
        "Our owner"
        self._trigger_event = Event()
        "Wake up event"
        self._identifiers = identifiers
        "Mask of supported identifiers"
        self._identifier_set = set(self._identifiers)
        "Set of supported identifiers"

    def supports_identifier(self, identifier: str) -> bool:
        """
        Returns if this worker supports given identifier
        :param identifier: The service identifier
        :return: True if supported
        """
        return identifier in self._identifier_set

    def wake_up(self):
        """
        Wakes this thread up, e.g. if a new matching task did arrive
        """
        self._trigger_event.set()

    def terminate(self):
        """
        Tells the thead to terminate
        """
        with self._lock:
            self._trigger_event.set()
            self._terminate = True

    def run(self) -> None:
        """
        Thread execution function
        """
        while not self._terminate:
            self._trigger_event.wait(0.1)
            self._trigger_event.clear()
            task = self._service_handler.get_task(self._identifiers)
            if task is not None:  # try to get a new task and execute it
                task: RemoteTask
                service = task.get_service()
                result = service.run_task(
                    task.get_target_function(), task.get_parameters()
                )
                task.assign_result(result)
                self._service_handler.flag_as_done(task)
        self._service_handler = None
