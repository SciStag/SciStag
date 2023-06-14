"""
Tests the logging of figures via pyplot
"""
import numpy as np

from . import vl
from sys import platform


def test_pyplot_logging():
    """
    Test the pyplot logging methods
    """
    hash_val = (
        "4973de155aa77f2bd17c8f19a160166a"
        if platform == "darwin"
        else "0a1977203f6576cc5ce8b41e0772427e"
    )
    # note minimal visualization differences between M1 Mac ons AMD64
    with vl.pyplot(assertion_name="testplot", assertion_hash=hash_val) as plt:
        t = np.arange(0.0, 5.0, 0.2)
        plt.plot(t, t, "r--", t, t**2, "bs", t, t**3, "g^")
    with vl.pyplot() as plt:
        data = {
            "a": np.arange(50),
            "c": np.random.randint(0, 50, 50),
            "d": np.random.randn(50),
        }
        data["b"] = data["a"] + 10 * np.random.randn(50)
        data["d"] = np.abs(data["d"]) * 100

        plt.scatter("a", "b", c="c", s="d", data=data)
        plt.xlabel("entry a")
        plt.ylabel("entry b")
