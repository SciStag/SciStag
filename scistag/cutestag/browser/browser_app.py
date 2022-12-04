"""
Implements a simple browser application to show a web page as an application
"""
from __future__ import annotations

import os
from threading import Thread

import PySide6

from scistag.common.mt import ManagedThread
from scistag.imagestag import Size2D

"""PySide6 WebEngineWidgets Example"""

import sys

DEFAULT_URL = "https://github.com/SciStag/SciStag#readme"
_UNIT_TESTING = "PYTEST_CURRENT_TEST" in os.environ

from PySide6.QtWidgets import (QApplication, QMainWindow)
from PySide6.QtCore import QUrl, QLoggingCategory
from PySide6.QtWidgets import (QApplication, QMainWindow)
from PySide6.QtWebEngineWidgets import QWebEngineView


class CuteBrowserWindow(QMainWindow):
    """
    The browser main window
    """

    def __init__(self, initial_url: str = DEFAULT_URL):
        """
        :param initial_url: The initial url to open as start screen
        """
        super().__init__()
        self.initial_url = initial_url
        self.setWindowTitle('PySide6 WebEngineWidgets Example')
        web_engine_context_log = QLoggingCategory("qt.webenginecontext")
        web_engine_context_log.setFilterRules("*.info=false")
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        self.web_view.load(QUrl(self.initial_url))
        self.web_view.page().titleChanged.connect(self.setWindowTitle)


class CuteBrowserApp:
    """
    A simple browser application displaying a website in a window of a
    pre-defined size
    """

    def __init__(self, initial_url: str = DEFAULT_URL,
                 initial_size: Size2D | None = None,
                 simple: bool = False):
        """
        :param initial_url: The start page's URL
        :param initial_size: The initial window size in pixels
        :param simple: If defined all standard browser elements will be hidden
        """
        self.app = QApplication()
        self.thread: Thread | None = None
        self.main_window = CuteBrowserWindow(initial_url)
        max_space = self.main_window.screen().availableGeometry()
        if initial_size is None:
            initial_size = Size2D(1280,
                                  1024)
        if initial_size.width > max_space.width():
            initial_size.width = max_space.width()
        if initial_size.height > max_space.height():
            initial_size.width = max_space.height()
        self.main_window.resize(*initial_size.to_int_tuple())
        self.main_window.show()

    def run(self):
        """
        Starts the application
        """
        self.app.exec()

    def run_in_background(self):
        """
        Runs the application in the background
        """
        self.thread = _CuteAppRunnerThread(self.app)
        self.thread.start()


class _CuteAppRunnerThread(ManagedThread):
    """
    Helper class to run an application in a background thread
    """

    def __init__(self, app: QApplication):
        """
        :param app: The application to run
        """
        super().__init__("CuteApp")
        self.app = app

    def run_loop(self):
        if not _UNIT_TESTING:
            self.app.exec()
        self.terminate()


if __name__ == "__main__":
    def test_run():
        app = CuteBrowserApp()
        app.run()


    test_run()
