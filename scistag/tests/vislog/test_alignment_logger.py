"""
Tests the alignment extension
"""
import pytest

from . import vl


def test_alignment():
    """
    Tests the alignment extension
    """
    vl.test.begin("Alignment")
    vl.test.checkpoint("alignments")
    vl.log("A")
    vl.log("B")
    vl.log("C")
    with vl.align():  # defaults to left
        vl.log("Left")
    with vl.align.left:
        vl.log("Left")
    with vl.align.right:
        vl.log("right")
    with vl.align.center:
        vl.log("center")
    with pytest.raises(ValueError):
        with vl.align("sausage"):
            vl.log("sausage")
    with vl.align.block_left:
        vl.table(["Table on the left", 123, 456])
    with vl.align.block_right:
        vl.table(["Table on the right", 123, 456])
    with vl.align.block_center:
        vl.table(["Table centered", 123, 456])
    with vl.align.center:
        vl.text("*" * 150)
    vl.test.assert_cp_diff("b9b4498070ac28de5e0abd10f8d51247")
