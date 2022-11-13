"""
Tests the logging of figures via pyplot
"""
import numpy as np

from . import vl


def test_pyplot_logging():
    """
    Test the pyplot logging methods
    """
    with vl.pyplot(assertion_name="testplot",
                   assertion_hash="62d17ca65c9cf6e97e5ba5d3575976da") as plt:
        t = np.arange(0., 5., 0.2)
        plt.plot(t, t, 'r--', t, t ** 2, 'bs', t, t ** 3, 'g^')
    with vl.pyplot() as plt:
        data = {'a': np.arange(50),
                'c': np.random.randint(0, 50, 50),
                'd': np.random.randn(50)}
        data['b'] = data['a'] + 10 * np.random.randn(50)
        data['d'] = np.abs(data['d']) * 100

        plt.scatter('a', 'b', c='c', s='d', data=data)
        plt.xlabel('entry a')
        plt.ylabel('entry b')
