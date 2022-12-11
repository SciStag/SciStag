"""
Provides helper functions for the general application lifecycle management
"""
from __future__ import annotations

import inspect
import sys


class StagApp:
    """
    Provides helper functions for the life cycle management of an application
    """

    @staticmethod
    def get_main_file() -> str | None:
        """
        Returns the file name of the Python script's main entry point (if
        there is one). If Python is executed e.g. in Jupyter Notebook it
        will return None.

        :return: The file name of the main entry point if there is one, None
            otherwise.
        """
        if "__main__" in sys.modules:
            main_mod = sys.modules["__main__"]
            if hasattr(main_mod, "__file__"):
                return main_mod.__file__
        return None

    @classmethod
    def is_main(cls, stack_level: int = 1) -> bool:
        """
        Returns if the file from which this method is called is Python's main
        entry point.

        :param stack_level: Defines at which level of the stack this function
            shall look at. 1 = Callee, 2 = Caller's callee etc.
        """
        main_file = cls.get_main_file()
        if main_file is not None and inspect.stack()[stack_level].filename == main_file:
            return True
        return False
