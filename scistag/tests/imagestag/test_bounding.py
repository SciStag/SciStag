"""
Implements the tests for Size2D, Pos2D and Bounding2D
"""

import pytest

from scistag.imagestag.bounding import Bounding2D
from scistag.imagestag import Size2D, Pos2D
from . import skip_imagestag


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_size2d():
    """
    Tests the Size2D class
    :return:
    """
    size = Size2D(width=36, height=58)
    assert size.width == 36 and size.height == 58
    assert size == Size2D(36, 58)
    assert size == Size2D(36.0, 58.0)
    with pytest.raises(ValueError):
        Size2D(36.0)
    assert isinstance(size.width, float) and isinstance(size.height, float)
    size = Size2D((36, 58))
    assert size.width == 36 and size.height == 58
    assert isinstance(size.width, float) and isinstance(size.height, float)
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        Size2D(width=45)
    size = Size2D(Size2D((36, 58)))
    assert str(size) == "Size2D(36.0,58.0)"
    assert size.width == 36 and size.height == 58
    assert isinstance(size.width, float) and isinstance(size.height, float)
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        Size2D((45, 68, 79))
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        Size2D("str")
    assert Size2D(0, 0).is_empty()


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_size2d_advanced():
    """
    Test comparison and conversion methods
    """
    size = Size2D(width=36, height=58)
    assert size.to_tuple() == (36, 58)
    other_size = Size2D(width=45, height=68)
    equal_size = Size2D(width=36, height=58)
    assert other_size != size
    assert equal_size == size
    assert size == (36, 58)
    assert size != (38, 58)
    int_tuple = size.to_int_tuple()
    assert int_tuple == (36, 58)
    assert isinstance(int_tuple[0], int) and isinstance(int_tuple[1], int)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_pos2d():
    """
    Tests the Pos2D class
    """
    pos = Pos2D(x=34, y=45)
    assert pos.x == 34 and pos.y == 45
    assert isinstance(pos.x, float) and isinstance(pos.y, float)
    pos = Pos2D((34, 45))
    assert str(pos) == "Pos2D(34.0,45.0)"
    assert pos == Pos2D(34, 45)
    assert pos == Pos2D(34.0, 45.0)
    with pytest.raises(ValueError):
        Pos2D(2.0)
    assert pos.x == 34 and pos.y == 45
    assert isinstance(pos.x, float) and isinstance(pos.y, float)
    pos = Pos2D(Pos2D((34, 45)))
    assert pos.x == 34 and pos.y == 45
    assert isinstance(pos.x, float) and isinstance(pos.y, float)
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        _ = Pos2D(Pos2D((34, 45, 38)))
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        _ = Pos2D(x=68)
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        _ = Pos2D("invalid")


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_pos2d_advanced():
    """
    Test comparison and conversion methods
    """
    pos = Pos2D(Pos2D((34, 45)))
    assert pos.to_tuple() == (34, 45)
    int_tuple = pos.to_int_tuple()
    assert int_tuple == (34, 45)
    assert isinstance(int_tuple[0], int) and isinstance(int_tuple[1], int)
    other_pos = Pos2D((36, 68))
    equal_pos = Pos2D((34, 45))
    assert pos == (34, 45)
    assert pos != (36, 36)
    assert equal_pos == pos
    assert other_pos != pos


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_bounding_basics():
    """
    Tests the Bounding2D class
    """
    # ul lr 1d tuple
    bounding = Bounding2D((45, 50, 100, 100))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (100, 100)
    assert str(bounding) == "Bounding2D(45.0,50.0,100.0,100.0)"
    # ul size 2d tuple
    bounding = Bounding2D(((45, 50), (100, 100)))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (145, 150)
    # ul lr explicit
    bounding = Bounding2D(pos=Pos2D((45, 50)), lr=Pos2D((100, 100)))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (100, 100)
    # ul size explicit
    bounding = Bounding2D(pos=Pos2D((45, 50)), size=Size2D((100, 100)))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (145, 150)
    # lr size explicit
    bounding = Bounding2D(lr=Pos2D((45, 50)), size=Size2D((100, 100)))
    assert bounding.pos.to_tuple() == (-55, -50)
    assert bounding.lr.to_tuple() == (45, 50)
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        bounding = Bounding2D((45, 50, 100, 100, 86))
    with pytest.raises(ValueError):  # missing size/ul
        bounding = Bounding2D(lr=Pos2D((45, 50)))
    with pytest.raises(ValueError):  # missing size/lr
        bounding = Bounding2D(pos=Pos2D((45, 50)))
    with pytest.raises(TypeError):  # invalid type
        # noinspection PyTypeChecker
        bounding = Bounding2D("Error")
    # pos + size
    bounding = Bounding2D((Pos2D((45, 50)), Size2D((100, 100))))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (145, 150)


@pytest.mark.skipif(skip_imagestag, reason="ImageStag tests disabled")
def test_bounding_advanced():
    """
    Tests comparison and conversion methods
    """
    # pos + pos
    bounding = Bounding2D((Pos2D((45, 50)), Pos2D((100, 100))))
    assert bounding.pos.to_tuple() == (45, 50)
    assert bounding.lr.to_tuple() == (100, 100)
    assert bounding.get_size_tuple() == (55.0, 50.0)
    assert bounding.get_int_size_tuple() == (55, 50)
    assert bounding.get_size().to_tuple() == (55, 50)
    assert isinstance(bounding.get_size(), Size2D)
    assert bounding.width() == 55
    assert bounding.height() == 50
    bounding_copy = Bounding2D(bounding)
    assert bounding_copy.pos.to_tuple() == (45, 50)
    assert bounding_copy.lr.to_tuple() == (100, 100)
    # equal
    assert bounding_copy == bounding
    diff_bounding = Bounding2D((Pos2D((145, 50)), Pos2D((100, 100))))
    assert bounding == (45, 50, 100, 100)
    assert bounding != (49, 50, 100, 100)
    # unequal
    assert bounding != diff_bounding
    diff_bounding2 = Bounding2D((Pos2D((45, 50)), Pos2D((140, 100))))
    assert bounding != diff_bounding2
    # copy
    assert bounding == bounding.copy()
    # conversion methods
    bounding = Bounding2D((Pos2D((45, 50)), Pos2D((100, 100))))
    assert bounding.to_coord_size_tuple() == (45, 50, 55, 50)
    assert bounding.to_nested_coord_size_tuple() == ((45, 50), (55, 50))
    assert bounding.to_coord_tuple() == (45, 50, 100, 100)
    assert bounding.to_nested_coord_tuple() == ((45, 50), (100, 100))
    assert Bounding2D(((50, 50), (0, 0))).is_empty()
