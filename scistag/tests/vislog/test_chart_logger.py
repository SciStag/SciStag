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
    path = FilePath.absolute_comb("data/mermaid_sample.mmd")
    assert vl.chart.embed(path)
    assert not vl.chart.embed(FilePath.absolute_comb("data/mermaid_samplex.mmd"))
    assert vl.chart.embed(path, watch=False)
    # provoke wrong type
    with pytest.raises(TypeError):
        vl.chart.embed(b"123")
    # provoke wrong extension
    with pytest.raises(ValueError):
        vl.chart.embed("data/mermaid_sample.xxd")
    vl.chart.embed("data/mermaid_sample.xxd", extension=".mmd")
    vl.test.assert_cp_diff("b6e0eeb31c866e812149008ddfa69227")
