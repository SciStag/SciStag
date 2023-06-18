"""
Tests the different cell features of a LogBuilder
"""
from unittest import mock

from .. import vl

from scistag.vislog import LogBuilder, cell, section, data, stream, once, VisualLog


class MyLog(LogBuilder):
    @once
    def init(self):
        self.visible_groups.add("data")
        self.hidden_groups.add("hidden")

    @once(groups=["data"], output="data")
    def load_data(self):
        self["data"] = 111
        self.text("once_text")  # should not be ignored
        self.set_page("first", "start")

    @data(groups={"data"}, output=["data"])
    def we_are_loading_data(self):
        self["data"] = self["data"] * 2
        self.text("data_text")  # should not be ignored

    @stream(groups="data", requires=["data"], output=["data"])
    def just_a_stream(self):
        self["data"] = self["data"] * 2
        self.text("stream_text")  # should not be ignored

    @cell(uses="data", requires="data")
    def first(self):
        self.text(f"Hello world {self['data']}")

    @section(uses=["data"])
    def second_text(self):
        self.text("Hello second")

    @cell(section_name="123")
    def second_text(self):
        self.text("Hello auto-section")
        self["shouldExist"] = "test"

    @cell(requires="shouldExist==test")
    def test_equals(self):
        self.text("Equals fulfilled")

    @cell(requires="shouldExist==xest")
    def test_equals_not_match(self):
        self.text("Equals not fulfilled")

    @cell(uses=["shouldExist", "data"])
    def uses_two(self):
        self.text("Uses two")

    @section("section with name", capture_stdout=True)
    def sub_section(self):
        self.text("Hello section with printed text")
        print("Some printed text which will be added too")

    @cell(page="first", tab="start")
    def just_page(self):
        self.text("First page")

    @cell(page="first", groups=["default", "hidden"])
    def just_page_hidden(self):
        self.text("Hidden page")

    @cell(page="first", groups=["default", "visible"])
    def just_page_visible(self):
        self.text("Visible page with group")

    @cell(page="first", groups=["other"])
    def just_page_not_included(self):
        self.text("Visible page with group but not included")

    @cell(page="first", tab="subtab")
    def page_wrong_tab(self):
        self.text("First page")

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
    vl.test.assert_cp_diff("d0d36d21494adbe4da8a2500e3aec936")
    vl.flush()
