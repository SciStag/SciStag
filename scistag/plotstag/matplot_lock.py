from __future__ import annotations

import io
import matplotlib

from scistag.common import StagLock
import matplotlib.pyplot as plt

from scistag.imagestag import Image


class MPLock:
    """
    Helper class to make matplotlib usable in a multi-threaded environment.

    Usage:

    ..  code-block:: python

        with MPLock() as plt:
            plt.imshow(..)
    """

    access_lock = StagLock()
    """
    Shared access lock to prevent multiple thread using Matplotlib at the
    same time
    """

    def __init__(self, backend="Agg"):
        """
        :param backend: The backend to be used. Background rendering by default
        """

        self.backend: str | None = backend
        "The backend to be used"
        self.pl = None
        """
        Link to the module once valid
        """

    def __enter__(self):
        self.access_lock.acquire()
        self.plt = plt
        if self.backend is not None:
            plt.switch_backend(self.backend)
        return self.plt

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close('all')
        self.access_lock.release()
