"""
Jinja2 import helper. Verifies if the package is available and provides access
to it.

Jinja2 is a template parser which can (next to other formats) generate
configurable html snippets such as used in :class:`VisualLog`.
"""

try:
    import jinja2

    _jinja2_available = True
    "Defines if jinja could be loaded"
except ModuleNotFoundError:
    jinja2 = None
    _jinja2_available = False
    "Defines if jinja could be loaded"


def jinja_available():
    """
    Returns if Jinja is available

    :return: True if the Jinja package can be used
    """
    return _jinja2_available
