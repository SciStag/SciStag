"""
Tests the basic markdown functionality
"""
import pytest

from . import vl
from ...filestag import FilePath
from ...vislog import VisualLog


def test_markdown():
    """
    Tests the basic markdown functionality
    """
    vl.test.begin("Testing markdown logging")
    vl.test.checkpoint("log.markdown.basic")
    vl.md("**Single line markdown**")
    vl.md(
        """
    
    * How about some
    * multi-line markdown? 
    """
    )
    vl.test.assert_cp_diff("cab9b56dc7c3b2c50d88dfc754decb4d")

    log = VisualLog(continuous_write=True)
    log.default_builder.md.embed(b"EmbeddedData")
    assert b"EmbeddedData" in log.default_page.get_body()
    log.default_builder.md.embed(FilePath.absolute_comb("embedded.md"))
    assert b"This markdown file will be embedded." in log.default_page.get_body()
    with pytest.raises(ValueError):
        log.default_builder.md.embed(FilePath.absolute_comb("Not existing file"))
