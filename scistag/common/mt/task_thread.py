"""
Implements the class :class:`TaskThread` which provides a basic skeleton for
a thread which is woken up on demand to execute a task.
"""

from __future__ import annotations

from threading import Event
from typing import Any

from scistag.common.mt.managed_thread import ManagedThread


class TaskThread(ManagedThread):
    """
    Helper class to create threads which shall
    """

    def __init__(self, name: str):
        """
        :param name: The thread's name as shown in the debugger
        """
        super(TaskThread, self).__init__(name)
        self._task_event = Event()
        "The event handler which shall be triggered for each event arriving"
        self._tasks: list = []
        "The list of tasks to execute"
        self._turn_time = 1.0
        "The event outbreak time, fallback is an event trigger should fail"

    def add_task(self, task: Any):
        """
        Adds a task to be executed

        :param task: The task to be executed via run_task
        """
        with self._access_lock:
            self._tasks.append(task)

    def run_task(self, task: Any):
        """
        Runs a task added via :meth:`add_task`.

        :param task: The task to execute
        """
        pass

    def run_loop(self):
        """
        Override this method with your own task handling method.
        """
        self._task_event.wait(0.1)
        if self._task_event.is_set():
            self._task_event.clear()
        with self._access_lock:
            task = self._tasks.pop() if len(self._tasks) else None
        if task is not None:
            self.run_task(task)

    def terminate(self):
        super().terminate()
        if self._task_event is not None:
            self._task_event.set()
