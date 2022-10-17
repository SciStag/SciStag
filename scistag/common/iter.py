"""
Helpful functions for working with iterators
"""


def limit_iter(iterator, count: int = -1):
    """
    Limit number of iterated elements from an iterable.

    :param iterator: The iterable
    :param count: The maximum count. -1 = unlimited
    """
    while count != 0:
        try:
            yield next(iterator)
        except StopIteration:
            return
        count -= 1
