"""
Implements a simple browser application to show a web page as an application
"""
from __future__ import annotations

from scistag.imagestag import Size2D

"""PySide6 WebEngineWidgets Example"""

import sys

DEFAULT_URL = "https://github.com/SciStag/SciStag#readme"

from PySide6.QtWidgets import (QApplication, QMainWindow)
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QApplication, QMainWindow)
from PySide6.QtWebEngineWidgets import QWebEngineView


class CuteBrowserWindow(QMainWindow):

    def __init__(self, initial_url: str = DEFAULT_URL):
        super().__init__()
        self.initial_url = initial_url
        self.setWindowTitle('PySide6 WebEngineWidgets Example')
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        self.web_view.load(QUrl(self.initial_url))
        self.web_view.page().titleChanged.connect(self.setWindowTitle)


class CuteBrowserApp:

    def __init__(self, initial_url: str = DEFAULT_URL,
                 initial_size: Size2D | None = None):
        self.app = QApplication()
        self.main_window = CuteBrowserWindow(initial_url)
        max_space = self.main_window.screen().availableGeometry()
        if initial_size is None:
            initial_size = Size2D(1280,
                                  1024)
        self.main_window.resize(*initial_size.to_int_tuple())
        self.main_window.show()

    def run(self):
        self.app.exec()


if __name__ == "__main__":
    app = CuteBrowserApp()
    app.run()
