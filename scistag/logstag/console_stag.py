"""
Defines an interface to visualize data in the console and receive key inputs
"""

from __future__ import annotations
from os import system, name


class Console:
    """
    Helper class for logging data to the console
    """

    def __init__(self):
        self.print = print
        self.progressive = False
        """        
        Defines if the console is progressive, so should list new entries
        line by line w/o ever clearing the full terminal
        """

    def clear(self):
        """
        Clears the console (if non-progressive)
        """
        assert not self.progressive
        self.print("\033[H\033[J", end="")

    def print(self, text: str, linebreak: str | None = None):
        """
        Prints a new line

        :param text: The text to be printed
        :param linebreak: The type of linebreak to use
        """
        if linebreak is not None:
            self.print(text, end=linebreak)
        else:
            self.print(text)
