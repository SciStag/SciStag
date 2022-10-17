"""
Tests the text alignment classes
"""
import pytest

from scistag.imagestag.text_alignment_definitions import (HTextAlignment,
                                                          VTextAlignment)
from . import skip_imagestag

@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_halignment():
    """
    Tests the horizontal alignment
    """
    align = HTextAlignment(HTextAlignment.LEFT)
    assert align == HTextAlignment.LEFT == 0
    assert align == HTextAlignment("l")
    with pytest.raises(ValueError):
        HTextAlignment("topCRAFT")


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_valignment():
    """
    Tests the vertical alignment
    """
    align = VTextAlignment(VTextAlignment.TOP)
    assert align == VTextAlignment.TOP == 0
    assert align == VTextAlignment("t")
    assert align == VTextAlignment("top")
    with pytest.raises(ValueError):
        VTextAlignment("krait")
