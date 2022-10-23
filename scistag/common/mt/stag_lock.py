"""
Implements the :class:`StagLock` class which replaces the standard RLock
for threading and configured case by case.
"""
from __future__ import annotations

from threading import RLock


class StagLock:
    """
    Replacement for the standard multithreading. Can be configured for
    different use cases. Behaves like a standard RLock by default.

    Usage: ``with my_lock() as lock:...``
    """

    def __init__(self, thread_lock=True):
        """
        :param thread_lock: Defines if a thread lock shall be used
        """
        self.thread_lock: RLock | None = RLock() if thread_lock else None

    def acquire(self):
        """
        Acquires this lock and prevents other users from accessing data it
        protects.
        """
        if self.thread_lock is not None:
            self.thread_lock.acquire()

    def release(self):
        """
        Releases the lock
        """
        if self.thread_lock is not None:
            self.thread_lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
