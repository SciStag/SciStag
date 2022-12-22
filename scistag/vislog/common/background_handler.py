"""
:class:`BackgroundHandler` runs the execution logic of a VisualLog
based application in a background thread so a UI application such as Qt may
use the main thread.
"""

from scistag.common.mt import ManagedThread
from scistag.vislog import VisualLog


class BackgroundHandler(ManagedThread):
    """
    Executes the updating logic of a VisualLog app in the background
    """

    def __init__(self, log: VisualLog):
        """
        :param log: The log to update in the background thread
        """
        super().__init__("vislogbgthread")
        self.log = log

    def run_loop(self):
        self.log._run_log_mt(True, wait=True)
        self.terminate()
