"""
Teste the LogBuilder base class
"""
from scistag.vislog.common.log_builder_base import LogBuilderBase


def test_log_builder_basics():
    """
    Tests the log builder basics
    """

    class LbSub(LogBuilderBase):
        def __init__(self):
            super().__init__()
            self.test_bnd = self.clref(3)
            assert self.test_bnd == 3

    sub_test = LbSub()
