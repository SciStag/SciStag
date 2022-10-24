"""
Defines helper functions for working with lists
"""


def batch_list(lst, n):
    """
    Splits a list into batches of size n

    :param lst: The list to split into batches
    :param n: The count of elements per batch
    :return: The list of lists.

        Each element of list except the last one will be a list of size n.
        The last element will (potentially) contain a list with less than
        n elements containing the remaining elements.
    """
    if not isinstance(lst, list):
        lst = list(lst)
    return [lst[i:i + n] for i in range(0, len(lst), n)]
