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
    vl.test.assert_cp_diff("1a3db2a3308e2426c9a4a98bc0425f0a")
