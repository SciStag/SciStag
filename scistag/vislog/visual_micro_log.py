"""
Implements VisualMicroLock - a replacement for the LogBuilder logging
interface of the SciStag package for platforms which are not capable of loading
of the full library such as MicroPython .

Tries to wrap all commands as far as reasonable to basic outputs to stdout,
e.g. .log, .text, .title etc.

This file is part of the SciStag Python package and licensed under the terms
of the MIT License.

Copyright (C) 2022 Michael Ikemann

For more details see https://github.com/scistag/scistag
"""


class VisualMicroLock:
    """
    VisualMicroLock is a replacement for the LogBuilder class
    of the SciStag Python package to easily port an application using
    VirtualLog for logging to platforms which are not capable of
    loading of the full SciStag library such as MicroPython.

    Tries to wrap all common commands to a simple log to stdout operation
    as good as possible.

    ..  code-block:python

        try:
            from scistag.vislog import VisualLog, LogBuilder
            VisualLog.setup_mocks()
        except ModuleNotFoundError:
            from visual_log_mock import VisualLog, LogBuilder
    """

    def __init__(self, log_to_std_out=True):
        """
        :param log_to_std_out: Defines if all simple logging shall be directed
            to stdout.
        """
        self.title = self.text
        "Replacement for :meth:`LogBuilder.title`"
        self.sub = self.text
        "Replacement for :meth:`LogBuilder.sub`"
        self.sub_x3 = self.text
        "Replacement for :meth:`LogBuilder.sub_x3`"
        self.sub_x4 = self.text
        "Replacement for :meth:`LogBuilder.sub_x4`"
        self.sub_test = self.text
        "Replacement for :meth:`LogBuilder.sub_test`"
        self.md = self.text
        "Replacement for :meth:`LogBuilder.md`"
        self.html = self.text
        "Replacement for :meth:`LogBuilder.html`"
        self.log_to_stdout = log_to_std_out
        "Defines if the simple output shall be directed to stdout"
        self.print_method = lambda text, end=None: print(text, end=end)
        "Defines the print method to be used"
        self.log = MicroLogHelper(self)

    def image(self, *_, **__) -> "VisualMicroLock":
        raise NotImplementedError("Not supported yet")

    def figure(self, *_, **__) -> "VisualMicroLock":
        raise NotImplementedError("Not supported yet")

    def table(self, data, *_, **__) -> "VisualMicroLock":
        """
        Adds a table to the log.

        :param data: A list of rows of which each row contains the same
            count of columns. The content has to be convertible to a string.
        :param _:
        :param __:
        :return:
        """
        for row in data:
            self.print_method("| ", end="")
            for index, col in enumerate(row):
                if self.log_to_stdout:
                    self.print_method(str(col), end=" | ")
            if self.log_to_stdout:
                self.print_method("")
        return self

    def text(self, text: str, *args, **kwargs):
        """
        Replacement for :meth:`LogBuilder.text` and all similar
        functions. Suppresses all parameters except the text.

        :param text: The text to be logged
        :return: self
        """
        return self.print_method(text)

    def br(self):
        """
        Inserts a simple line break
        """
        self.text("")
        return self

    def page_break(self):
        """
        Inserts a page break
        """
        self.text(f"\n{'_' * 40}\n")
        return self

    def finalize(self, *_, **__):
        """
        Finalizes the log
        """

    @staticmethod
    def setup_micro_lock(target_path: str = "./"):
        """
        Stores the VisualMicroLock class in the defined directory so it can
        easily be imported. Call this once in a new project.

        :param target_path: The path at which the Python files shall be stored.
        """
        out_name = f"{target_path}/visual_micro_log.py"
        with open(__file__, "r") as src_file:
            content = src_file.read()
        import os

        if os.path.exists(out_name):
            with open(out_name, "r") as old_mock_file:
                if content == old_mock_file.read():
                    return  # already up to date
        with open(out_name, "w") as mock_file:
            mock_file.write(content)

    @property
    def is_micro(self) -> bool:
        """
        Returns if this builder is a log with limited functionality for
        MicroPython.

        :return: True if it is a minimalistic lock
        """
        return True


class MicroLogHelper:
    """
    Helper class handling all common text logs such as info, debug etc.
    """

    def __init__(self, tar: "VisualMicroLock"):
        """
        :param tar: The logging target
        """
        self.target = tar
        "The target log"
        self.add = self.__call__

    def __call__(self, *args, **_) -> "VisualMicroLock":
        """
        Logs text to stdout

        :param args: The elements to log. Will be separated by space.
        """
        args = [str(element) for element in args]
        if self.target.log_to_stdout:
            self.target.print_method(" ".join(args))
        return self.target

    def info(self, *args, **_) -> "VisualMicroLock":
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        """
        self.add("[INFO]    ", *args)
        return self.target

    def debug(self, *args, **_) -> "VisualMicroLock":
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        """
        self.add("[DEBUG]   ", *args)
        return self.target

    def warning(self, *args, **_) -> "VisualMicroLock":
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        """
        self.add("[WARNING] ", *args)
        return self.target

    def error(self, *args, **_) -> "VisualMicroLock":
        """
        Logs an info text

        :param args: The elements to log. Will be separated by space.
        """
        self.add("[ERROR]   ", *args)
        return self.target

    def critical(self, *args, **_) -> "VisualMicroLock":
        """
        Logs a critical error

        :param args: The elements to log. Will be separated by space.
        """
        self.add("[CRITICAL]", *args)
        return self.target
