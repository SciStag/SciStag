"""
Tests the VisualMicroLog's function
"""
import os
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import pytest

from scistag.vislog import VisualLog

tar_dir = os.path.dirname(__file__)


def test_micro_log(tmp_path):
    """
    Tests the micro log basics
    """

    ml_path = str(tmp_path) + "/"

    VisualLog.setup_micro_log(f"{ml_path}")
    VisualLog.setup_micro_log(f"{ml_path}")
    assert os.path.exists(f"{ml_path}/visual_micro_log.py")

    from scistag.vislog.visual_micro_log import VisualMicroLock

    for turn_index in range(2):
        micro_lock = VisualMicroLock(log_to_std_out=turn_index == 0)
        std_out = StringIO()
        with redirect_stdout(std_out):
            with mock.patch("builtins.print") as pmock:
                micro_lock.log("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.log.info("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.log.error("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.log.warning("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.log.debug("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.log.critical("Test")
                assert pmock.called or (turn_index == 1 and not pmock.called)

            with mock.patch("builtins.print") as pmock:
                micro_lock.table([[123, 456], [758, 910]])
                with pytest.raises(NotImplementedError):
                    micro_lock.figure()
                with pytest.raises(NotImplementedError):
                    micro_lock.image()
                assert pmock.called

        text = ""

        def add_text(new_text, end="\n"):
            nonlocal text
            text += new_text + end

        micro_lock.print_method = add_text
        with mock.patch("builtins.print") as pmock:
            micro_lock.br()
            micro_lock.page_break()
            micro_lock.title("Title")
            micro_lock.sub("Subtitlex1")
            micro_lock.sub_x4("Subtitlex4")
            micro_lock.sub_x3("Subtitlex3")

        assert text.startswith("\n")
        assert "________" in text
        assert "Title" in text
        assert "Subtitlex1" in text
        assert "Subtitlex4" in text
        assert "Subtitlex3" in text
        assert micro_lock.is_micro
