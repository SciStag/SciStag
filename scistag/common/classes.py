"""
Helper method for classes
"""


class ClassHelper:
    """
    Provides helper methods for dealing with classes
    """

    @staticmethod
    def get_full_class_name(element) -> str:
        """
        Returns the full qualified class name of an object or a class for
        comparison, e.g. when importing and exporting object data.

        :param element: The element or class object
        :return: The element's or classes unique name
        """
        if not isinstance(element, type):
            element = element.__class__
        module = element.__module__
        if module == '__builtin__':
            return element.__qualname__
        return module + '.' + element.__qualname__


__all__ = ["ClassHelper"]
