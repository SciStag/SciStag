"""
Tests the logging of charts such as a Mermaid flow chart
"""
import pytest

from . import vl
from ...filestag import FileStag, FilePath


def test_direct_logging():
    """
    Tests direct logging of charts
    """
    vl.test.checkpoint("Direct graph logging")
    vl.chart.mmd("graph TD\nTDX-->Y")
    vl.test.assert_cp_diff("df6ceb10d363027c0bd82ebb97f06fb7")
    path = FilePath.absolute_comb("data/mermaid_sample.mmd")
    vl.test.checkpoint("Logging from file")
    assert vl.chart.embed(path)
    assert not vl.chart.embed(FilePath.absolute_comb("data/mermaid_samplex.mmd"))
    vl.test.assert_cp_diff("7eadd73c22351cf9496d968de134e0df")
    assert vl.chart.embed(path, watch=False)
    # provoke wrong type
    with pytest.raises(TypeError):
        vl.chart.embed(b"123")
    # provoke wrong extension
    with pytest.raises(ValueError):
        vl.chart.embed("data/mermaid_sample.xxd")
    vl.chart.embed("data/mermaid_sample.xxd", extension=".mmd")
