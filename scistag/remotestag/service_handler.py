from __future__ import annotations
from threading import RLock
from .service_worker import RemoteWorker
from .service import RemoteService, RemoteParameterTypes
from .service_task import RemoteTask


class RemoteServiceHandler:
    """
    Orchestrates the single services and their associated execution resources
    """

    default_handler: "RemoteServiceHandler" = None
    "The singleton default handler"

    def __init__(self):
        self._lock = RLock()
        self._workers: list[RemoteWorker] = []
        self._worker_count = 8
        self._services: dict[str, RemoteService] = {}
        self._started = False
        self._call_counter = 0
        "Call id counter"
        self._todo = []
        "Tasks to be executed"
        self._in_progress = []
        "Tasks in progress"

    def register_service(self, service: RemoteService) -> bool:
        """
        Registers a new service
        :param service: The new service
        """
        identifier = service.get_identifier()
        with self._lock:
            if self._started:
                raise Exception(
                    "Can not register new services once the service handler was started.")
            if identifier in self._services:
                return False
            self._services[identifier] = service
        return True

    def start(self) -> bool:
        """
        Initiates the handler
        :return: True on success
        """
        with self._lock:
            if self._started:
                return False
            self._started = True
        self.__start_workers()
        return True

    def stop(self) -> bool:
        """
        Stops the handler
        :return: True on success
        """
        with self._lock:
            if not self._started:
                raise Exception("RemoteServiceHandler not started yet")
            self._started = False
        self.__stop_workers()
        return True

    def get_todo(self) -> int:
        """
        Returns the count of tasks waiting on the to do list
        :return: The count of tasks which did not start yet
        """
        with self._lock:
            return len(self._todo)

    def get_in_progress(self) -> int:
        """
        Returns the count of tasks which are in progress
        :return: The count of tasks in progress
        """
        with self._lock:
            return len(self._in_progress)

    def execute_async(self, identifier: str, parameters: RemoteParameterTypes,
                      timeout_s: float = -1.0) -> RemoteTask:
        """
        Initiates the asynchronous execution of a function
        :param identifier: The function's identifier
        :param parameters: The function parameters
        :param timeout_s: The timeout in seconds. Very recommended in case you access this service from the web.
        :return: The task to retrieve the result with
        """
        if not isinstance(parameters, dict):
            parameters = {RemoteService.INPUT_VALUE: parameters}
        service_found = None
        for service in self._services.values():  # verify that function is available
            service: RemoteService
            if service.provides_function(identifier):
                service_found = service
                break
        if service_found is None:
            raise Exception("Method not configured")
        with self._lock:
            self._call_counter += 1
            new_id = self._call_counter
            task = RemoteTask(new_id, service=service_found,
                              target_function=identifier, parameters=parameters,
                              timeout_s=timeout_s)
            self._todo.append(task)
        identifier = service_found.get_identifier()
        for worker in self._workers:
            if worker.supports_identifier(identifier):
                worker.wake_up()
        return task

    def get_task(self, identifier_set) -> RemoteTask | None:
        """
        Tries to find a suitable task for the list of supported services.
        Moves the task internal from to do to in progress
        :param identifier_set: The supported services
        :return: A new task if one is available.
        """
        with self._lock:
            for task in self._todo:
                task: RemoteTask
                identifier = task.get_service().get_identifier()
                if identifier in identifier_set:
                    self._todo.remove(task)
                    self._in_progress.append(task)
                    return task
        return None

    def flag_as_done(self, task: RemoteTask):
        """
        Flags a task as done
        :param task: The task to flag as done
        """
        with self._lock:
            if task in self._in_progress:
                self._in_progress.remove(task)

    def __start_workers(self):
        """
        Winds up all worker threads
        """
        single_threaded_identifiers = []
        multi_threaded_identifiers = []
        for identifier, service in self._services.items():
            is_single_threaded = service.get_single_threaded()
            if is_single_threaded:
                single_threaded_identifiers.append(identifier)
            else:
                multi_threaded_identifiers.append(identifier)
        for identifier in single_threaded_identifiers:
            new_worker = RemoteWorker(self, [identifier])
            self._workers.append(new_worker)
            new_worker.start()
        if len(multi_threaded_identifiers) != 0:
            for _ in range(self._worker_count):
                new_worker = RemoteWorker(self, multi_threaded_identifiers)
                self._workers.append(new_worker)
                new_worker.start()

    def __stop_workers(self):
        """
        Stop and join all workers
        """
        for worker in self._workers:
            worker.terminate()
        for worker in self._workers:
            worker.join()

    @classmethod
    def get_default_handler(cls):
        """
        Returns the default remote handler
        """
        return cls.default_handler


remote_service_handler = RemoteServiceHandler()
RemoteServiceHandler.default_handler = remote_service_handler
