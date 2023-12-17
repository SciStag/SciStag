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
    vl.test.assert_cp_diff("7ae07cb9c8519793df03104dc072d4da")

    log = VisualLog()
    log.default_builder.md.embed(b"EmbeddedData")
    log.default_builder.flush()
    assert b"EmbeddedData" in log.default_page.get_body()
    log.default_builder.md.embed(FilePath.absolute_comb("embedded.md"))
    log.default_builder.flush()
    assert b"This markdown file will be embedded." in log.default_page.get_body()
    with pytest.raises(ValueError):
        log.default_builder.md.embed(FilePath.absolute_comb("Not existing file"))
