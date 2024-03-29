import hashlib
import os

from scistag.vislog.options.extension_options import MERMAID_EXTENSION
from scistag.vislog.visual_log import VisualLog


class VisualTestLog(VisualLog):
    """
    Helper class for the visualization of unit test results
    """

    def __init__(self, test_filename: str, log_images: bool = True, **params):
        """
        :param test_filename: The name of the test file.
            From this the VisualTestLog automatically extracts the relative
             target path and test name
        :param log_images: Defines if images shall be logged to disk
        :param params: Advanced parameters, see :class:`VisualLog`
        """
        base_dir = os.path.dirname(__file__)
        cur_dir = os.path.dirname(test_filename)
        assert cur_dir in test_filename
        rel_path = os.path.dirname(test_filename)[len(base_dir) + 1 :]
        target_dir = cur_dir + "/logs/"
        formats_out = params.pop("formats_out", {"html"})
        options = self.setup_options("disk", title=f"test {rel_path}")
        options.output.target_dir = target_dir
        options.output.formats_out = formats_out
        options.output.ref_dir = cur_dir + "/refdata"
        options.style.image.log_images = log_images
        options.extensions.add(MERMAID_EXTENSION)
        super().__init__(options=options, **params)
