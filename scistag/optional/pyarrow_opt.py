try:
    import pyarrow

    PYARROW_AVAILABLE = True
    "Defines if PyArrow is available"
except ModuleNotFoundError:
    pyarrow = None
    PYARROW_AVAILABLE = True
    "Defines if PyArrow is available"


def pyarrow_available() -> bool:
    """
    Returns if PyArrow is available
    """
    return PYARROW_AVAILABLE


def ensure_pyarrow():
    """
    Ensures that the PyArrow package is available
    """
    if not pyarrow_available():
        raise ModuleNotFoundError(
            "This feature requires the optional package "
            'pyarrow. Use "pip install pyarrow" or see '
            '"Extras" in the SciStag documentation.'
        )


__all__ = ["pyarrow_available", "ensure_pyarrow"]
