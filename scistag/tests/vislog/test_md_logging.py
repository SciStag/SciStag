"""
Tests the basic markdown functionality
"""

from . import vl


def test_markdown():
    """
    Tests the basic markdown functionality
    """
    vl.test.begin("Testing markdown logging")
    vl.test.checkpoint("log.markdown.basic")
    vl.md("**Single line markdown**")
    vl.md("""
    
    * How about some
    * multi-line markdown? 
    """)
    vl.test.assert_cp_diff("cab9b56dc7c3b2c50d88dfc754decb4d")
