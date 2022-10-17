"""
Implements the class :class:`FilePath` - a helper class for file path
iteration, extension detection etc.
"""
from __future__ import annotations

import inspect
import os.path


class FilePath:
    """
    Helper class for handling file paths - such as detecting the path or the
    extension of  a file.
    """

    @staticmethod
    def dirname(filename: str) -> str:
        """
        Returns the directory name of a file

        As of now just a wrapper of os.path.dirname().

        :param filename: The file's name
        :return: The directory the file is within
        """
        return os.path.dirname(filename)

    @staticmethod
    def norm_path(path: str) -> str:
        """
        Normalizes a path, e.g. integrates relative path definitions such as ..
        and . into the path.

        As of now just a wrapper of os.path.normpath().

        :param path: The path, e.g. /home/user/data/../documents
        :return: The "cleaned" path, e.g. The path, e.g. /home/user/documents
        """
        return os.path.normpath(path)

    @staticmethod
    def exists(path: str) -> bool:
        """
        Returns if given path exists

        As of now just a wrapper of os.path.exists().

        :param path: The path name
        :return: True if it exists
        """
        return os.path.exists(path)

    @staticmethod
    def base_name(path: str) -> str:
        """
        Returns the path's base name (e.g the filename)

        As of now just a wrapper of os.path.basename().

        :param path: The path
        :return: The element within the path, e.g. the file name
        """
        return os.path.basename(path)

    @classmethod
    def script_filename(cls, level=1) -> str:
        """
        Returns the file name of the calling method

        :param level: The stack level relative to this function,
            for internal use only. (+1 = caller, +2 = caller's caller etc.)
        :return: The absolute filename of the script file
        """
        return inspect.stack()[level].filename

    @classmethod
    def script_path(cls, level=1) -> str:
        """
        Returns the file name of the calling method

        :param level: The stack level relative to this function,
            for internal use only. (+1 = caller, +2 = caller's caller etc.)
        :return: The absolute filename of the script file
        """
        return cls.dirname(inspect.stack()[level].filename)

    @classmethod
    def absolute(cls, path: str):
        """
        Returns the absolute path for given relative path (relative to the
        current getcwd() path.

        As of now just a wrapper of os.path.abspath().

        :param path: The relative path e.g. "./../data"
        :return: The absolute path, e.g. "/home/user/scripts/data"
        """
        return os.path.abspath(path)

    @classmethod
    def absolute_comb(cls, rel_path: str, absolute_path: str | None = None):
        """
        Returns the absolute, normalized path of a relative path object
        combined with an absolute path object.

        What makes this function pretty handy is that if no path is given the
        calling script's path or Jupyter notebook's path will be used so
        relative includes can be easily located.

        :param rel_path: The (relative) path of which we want to determine the
            absolute path of
        :param absolute_path: The path at which we orient - has to be absolute.
            If no path is passed the calling function or the location of the
            executing Jupyter notebook will be used.
        :return: The absolute path
        """
        if absolute_path is None:
            absolute_path = cls.script_path(level=2)
        return cls.norm_path(os.path.join(absolute_path, rel_path))

    @classmethod
    def split_ext(cls, filename: str) -> tuple[str, str]:
        """
        Returns the extension and file component of given file path

        As of now just a wrapper of os.path.split_ext().

        :param filename: The filename
        :return: Tuple of filename and the file extension
            (e.g. ("image", ".png")
        """
        return tuple(os.path.splitext(filename))
