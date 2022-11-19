"""
Benchmarks the loading performance of the single modules such as ensuring
that slow/large modules such as matplotlib or pandas as lazy loaded.
"""

import importlib
import time


def test_loading_time():
    """
    Benchmarks the loading time of single libraries
    """
    start_time = time.time()
    importlib.import_module("scistag.imagestag")
    end_time = time.time()
    time_diff = end_time - start_time
    assert time_diff < 0.05
    print(time_diff)
    start_time = time.time()
    importlib.import_module("scistag.vislog")
    end_time = time.time()
    time_diff = end_time - start_time
    assert time_diff < 0.05
    print(time_diff)
