"""
Defines the class :class:`ManagedThread` which enhances the basic Thread
class by some comfort functions such as soft and hard interruption of it's
execution.
"""

from __future__ import annotations
from threading import Thread, Event

from scistag.common.mt.stag_lock import StagLock


class ManagedThread(Thread):
    """
    Advanced thread class to make multithreading even easier.

    You can either override it's run_loop to run an infinite thead which
    executes until :meth:`terminate` was called or as for classic threads
    just write your own run method.
    """

    _managed_threads: list[ManagedThread] = []
    "List of all running threads"
    _mt_access_lock = StagLock()
    "Access lock to shared, global class variables"

    def __init__(self, name: str):
        super(ManagedThread, self).__init__()
        self.terminate_event = Event()
        "Event to be flagged when the thread shall terminate"
        self._access_lock = StagLock()
        "The lock to access the thread's data"
        self.thread_name = name
        "The thread's name (as visible in the debugger)"

    def start(self) -> None:
        """
        Starts the thread
        """
        with self._mt_access_lock:
            if self not in self._managed_threads:
                self._managed_threads.append(self)
        super().start()

    @classmethod
    def get_active_threads(cls) -> list[ManagedThread]:
        """
        Returns a list of all running, managed threads

        :return: The list of active threads
        """
        with cls._mt_access_lock:
            return list(cls._managed_threads)

    def run_loop(self):
        """
        Override this method with your own task handling method.
        """
        pass

    def run(self) -> None:
        """
        Executes run_loop until :meth:`terminate` is called from another thread.
        """
        try:
            if self.terminate_event.isSet():
                return
            while not self.terminate_event.isSet():
                self.run_loop()
        except KeyboardInterrupt:
            pass
        self.unregister_thread()

    def unregister_thread(self):
        """
        Removes this thread from the global registry
        """
        with self._mt_access_lock:  # unregister
            if self in self._managed_threads:
                self._managed_threads.remove(self)

    def terminate(self):
        """
        Signals the termination flag.

        Signals the termination event. If you have other events, e.g for your
        task list, override this method and trigger them from here as well.
        """
        self.terminate_event.set()

    @classmethod
    def force_kill_thread(cls, thread: Thread) -> bool:
        """
        Tries to kill a thread by raising an exception.

        :param thread: The thread which we try to kill.
        :return: True on success
        """
        try:
            cls.raise_exception_async(thread.ident, KeyboardInterrupt)
            return True
        except (SystemError, ValueError, TypeError):
            return False

    def force_kill(self) -> bool:
        """
        Throws an interrupt exception on the thread to request its termination.

        Warning: This should really be the absolute last solution to get rid
        of a thread, e.g. an infinite running Flask server.
        For all other threads use :meth:`terminate` and :meth:`join`.

        :return: True on success.
        """
        return self.force_kill_thread(self)

    @staticmethod
    def raise_exception_async(ident, exception_class):
        """
        Raises an exception in another thread, e.g. to kill it such as
        interrupting a Flask server's endless loop.

        :param ident: The thread's ident (e.g. thread.ident)
        :param exception_class: The type of the exception to raise, e.g.
            KeyboardException.
        """
        import inspect
        import ctypes

        if not inspect.isclass(exception_class):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(ident), ctypes.py_object(exception_class)
        )
        if res == 0:
            raise ValueError("Invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(ident), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
