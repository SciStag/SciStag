"""
Tests the different cell features of a LogBuilder
"""
from .. import vl

from scistag.vislog import LogBuilder, cell, section, data, stream, once


class MyLog(LogBuilder):
    @once(groups="data", output="data")
    def load_data(self):
        self["data"] = 111
        self.text("once_text")  # should not be ignored

    @data(groups={"data"}, output=["data"])
    def we_are_loading_data(self):
        self["data"] = self["data"] * 2
        self.text("data_text")  # should not be ignored

    @stream(requires=["data"], output=["data"])
    def just_a_stream(self):
        self["data"] = self["data"] * 2
        self.text("stream_text")  # should not be ignored

    @cell(uses="data", requires="data")
    def first(self):
        self.text(f"Hello world {self['data']}")

    @section(uses=["data"])
    def second_text(self):
        self.text("Hello second")

    @section("section with name", capture_stdout=True)
    def sub_section(self):
        self.text("Hello section with printed text")
        print("Some printed text which will be added too")

    @cell(page="second", tab="main")
    def sub_sub_section(self):
        self.text("Hello second")
        self.cell.add(section="sub_section")

    @data(requires="data>0")
    def stats_cell(self):
        if self.stats_cell.cell.statistics_update_interval_s != 0.0:
            self.stats_cell.cell.statistics_update_interval_s = 0
            self.stats_cell.invalidate()
            self.stats_cell.cell.handle_loop()
        self.stats_cell.cell.log_statistics()
        assert not self.load_data.cell.can_build

    @data(requires="someList>0")
    def should_not_be_called(self):
        pass

    @data(requires="someObject")
    def should_not_be_called_2(self):
        pass


def test_adv_cells():
    """
    Tests the usage of advanced cells
    """
    vl.test.checkpoint("insert_builder")
    vl.add(MyLog, share="sessionId")
    vl.test.assert_cp_diff("080d9cd349ebf23837d07d2c1882dfde")
    vl.flush()
