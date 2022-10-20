"""
Module which defines the helper class of Bundle which can convert a dictionary,
list or tuple of objects to a single bytes stream and vice versa for easy
inter-process and server data exchange.
"""

from .numpy_bundler import NumpyBundler

__all__ = ["NumpyBundler"]
