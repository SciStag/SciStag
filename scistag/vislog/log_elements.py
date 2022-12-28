"""
Defines helper class to log custom elements to a log such as HTML or Makrdown
"""


class HTMLCode:
    """
    Helper class to explicitly identify a string as html code so functions such as
    :meth:`VisualLogBuilder.add` can identify it accordingly.
    """

    def __init__(self, code: str):
        """
        :param code: The HTML code
        """
        self.code = code

    def to_html(self):
        """
        Converts the object to html

        :return: The html code
        """
        return self.code

    def __str__(self):
        return self.code


class MDCode:
    """
    Helper class to explicitly identify a string as Markdown code so functions such as
    :meth:`VisualLogBuilder.add` can identify it accordingly.
    """

    def __init__(self, code: str):
        """
        :param code: The HTML code
        """
        self.code = code

    def to_md(self):
        """
        Converts the object to markdown

        :return: The markdown code
        """
        return self.code

    def __str__(self):
        return self.code
