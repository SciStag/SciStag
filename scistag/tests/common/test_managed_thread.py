"""
Tests the class ManagedThread
"""
import time
from threading import Event, Thread

import pytest

from scistag.common.mt import ManagedThread


class TimeoutThread(ManagedThread):

    def __init__(self):
        super().__init__(name="TimeoutThread")
        self.start_time = time.time()

    def run_loop(self) -> None:
        if time.time() - self.start_time > 0.2:
            self.terminate()


class AsyncExceptionThread(ManagedThread):

    def __init__(self):
        super().__init__(name="AsyncExceptionThread")
        self.start_time = time.time()
        self.caught = False
        self.start_event = Event()

    def run(self) -> None:
        try:
            self.start_event.set()
            super().run()
        except NotImplementedError:
            self.caught = True


def test_managed_thread():
    """
    Tests the basic functionality
    """
    mt = TimeoutThread()
    mt.start()
    mt.join()
    mt = AsyncExceptionThread()
    mt.start()
    assert len(ManagedThread.get_active_threads()) >= 1
    mt.start_event.wait()
    with pytest.raises(TypeError):
        mt.raise_exception_async(mt.ident, "123")
    while not mt.caught:
        try:
            mt.raise_exception_async(mt.ident, NotImplementedError)
        except ValueError:
            break
    mt.terminate()
    mt.join()
    assert mt.caught
    with pytest.raises(ValueError):
        mt.raise_exception_async(1234, NotImplementedError)

    mt = ManagedThread("endless")
    mt.start()
    mt.force_kill()
    mt.join()

    mt = ManagedThread("prekilled")
    mt.terminate()
    mt.start()
    mt.force_kill()
    mt.join()

    assert not ManagedThread.force_kill_thread(Thread())

    from unittest import mock
    with mock.patch("ctypes.pythonapi.PyThreadState_SetAsyncExc",
                    new=lambda *x, **y: 2) as patch:
        with pytest.raises(SystemError):
            ManagedThread.raise_exception_async(123, ValueError)
