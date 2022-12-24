"""
Helper module for time specific methods
"""
import time


def sleep_min(min_time: float):
    """
    Extended sleep function as workaround for Window's quite randomized sleeping
    behavior in some situations.

    :param min_time: The minimum required sleep time in seconds
    """
    assert min_time >= 0
    start_time = time.time()
    time.sleep(min_time)
    while time.time() < start_time + min_time:
        time.sleep(min_time / 10.0)
