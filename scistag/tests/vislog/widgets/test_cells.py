"""
Tests the different cell features of a LogBuilder
"""
from .. import vl

from scistag.vislog import LogBuilder, cell, section, data, stream, once


class MyLog(LogBuilder):
    @once
    def load_data(self):
        self["data"] = 111
        self.text("once_text")  # should not be ignored

    @data
    def we_are_loading_data(self):
        self["data"] = self["data"] * 2
        self.text("data_text")  # should not be ignored

    @stream(requires=["data"], output=["data"])
    def just_a_stream(self):
        self["data"] = self["data"] * 2
        self.text("stream_text")  # should not be ignored

    @cell
    def first(self):
        self.text(f"Hello world {self['data']}")

    @section
    def second(self):
        self.text("Hello second")

    @section("section with name")
    def second(self):
        self.text("Hello second")


def test_adv_cells():
    """
    Tests the usage of advanced cells
    """
    vl.test.checkpoint("insert_builder")
    vl.add(MyLog, share="sessionId")
    vl.test.assert_cp_diff("bda84837c9079fe82e03f09aa0ab9c09")
    vl.flush()
