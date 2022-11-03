"""
Implements VisualLogMock - a replacement for a VisualLogBuilder object for
platforms which are not capable of loading of the full SciStag library
such as MicroPython.

Tries to wrap all commands as far as reasonable to basic outputs to stdout,
e.g. .log, .text, .title etc.
"""


class VisualLogMock:
    """
    VisualLogMock is a replacement for the VisualLogBuilder class
    of the SciStag Python package to easily port an application using
    VirtualLog for logging to platforms which are not capable of
    loading of the full SciStag library such as MicroPython.

    Tries to wrap all common commands to a simple log to stdout operation
    as good as possible.

    ..  code-block:python

        try:
            from scistag.logstag import VisualLog, VisualLogBuilder
            VisualLog.setup_mocks()
        except ModuleNotFoundError:
            from visual_log_mock import VisualLog, VisualLogBuilder
    """

    def __init__(self, log_to_std_out=True):
        """
        :param log_to_std_out: Defines if all simple logging shall be directed
            to stdout.
        """
        self.title = self.text
        "Replacement for :meth:`VisualLogBuilder.title`"
        self.sub = self.text
        "Replacement for :meth:`VisualLogBuilder.sub`"
        self.sub_x3 = self.text
        "Replacement for :meth:`VisualLogBuilder.sub_x3`"
        self.sub_x4 = self.text
        "Replacement for :meth:`VisualLogBuilder.sub_x4`"
        self.sub_test = self.text
        "Replacement for :meth:`VisualLogBuilder.sbu_test`"
        self.md = self.text
        "Replacement for :meth:`VisualLogBuilder.md`"
        self.html = self.text
        "Replacement for :meth:`VisualLogBuilder.html`"
        self.log_to_stdout = log_to_std_out
        "Defines if the simple output shall be directed to stdout"

    def image(self, *_, **__) -> "VisualLogMock":
        return self

    def figure(self, *_, **__) -> "VisualLogMock":
        return self

    def table(self, data, *_, **__) -> "VisualLogMock":
        for row in data:
            for index, col in enumerate(row):
                if self.log_to_stdout:
                    print(col, end=" | ")
            if self.log_to_stdout:
                print("")
        return self

    def log(self, *args, **_) -> "VisualLogMock":
        """
        Logs text to stdout

        :param args: Positional arguments
        :param kwargs: Keyword arguments
        """
        args = [str(element) for element in args]
        if self.log_to_stdout:
            print(" ".join(args))
        return self

    def text(self, text: str, *args, **kwargs):
        """
        Replacement for :meth:`VisualLogBuilder.text` and all similar
        functions. Suppresses all parameters except the text.

        :param text: The text to be logged
        :return: self
        """
        return self.log(text)

    def line_break(self):
        """
        Inserts a simple line break
        """
        self.text("")

    def page_break(self):
        """
        Inserts a page break
        """
        self.text("\n_________________________________________________________________________________\n")

    def finalize(self, *_, **__):
        """
        Finalizes the log
        """

    @staticmethod
    def setup_mocks(target_path: str = "./"):
        """
        Stores the VisualLogMock class in the defined directory so it can
        easily be imported. Call this once in a new project.

        :param target_path: The path at which the Python files shall be stored.
        """
        out_name = f"{target_path}/visual_log_mock.py"
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
    def is_simple_log(self) -> bool:
        """
        Returns if this builder is a log with limited functionality.

        :return: True if it is a mock
        """
        return True


VisualLog = VisualLogMock
VisualLogBuilder = VisualLogMock
