"""
Just a small test to verify that LogBuilder does not call a main function if it has
parameters other than "vl"
"""
from scistag.vislog import LogBuilder

called = False


def main():
    """
    This method should not be called because it has no vl parameter
    """
    global called
    called = True


def test_build():
    global called
    LogBuilder.run()
    assert not called
    assert isinstance(LogBuilder.run(filetype="html"), bytes)
    assert isinstance(LogBuilder.run(filetype="invalid"), dict)
