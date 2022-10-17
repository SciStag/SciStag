import hashlib
import os

from scistag.logstag.visual_log.visual_log import VisualLog


class VisualTestLog(VisualLog):
    """
    Helper class for the visualization of unit test results
    """

    def __init__(self,
                 test_filename: str,
                 log_images: bool = True,
                 **params):
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
        rel_path = os.path.dirname(test_filename)[len(base_dir) + 1:]
        target_dir = cur_dir + "/logs/"
        self.cp_backups = []
        "Data from the last checkpoints"
        formats_out = params.pop("formats_out", {"html"})
        super().__init__(target_dir=target_dir,
                         title=f"test {rel_path}",
                         formats_out=formats_out,
                         ref_dir=cur_dir + "/refdata",
                         log_to_disk=log_images,
                         clear_target_dir=False,
                         **params)
        self.log_images = log_images

    def checkpoint(self):
        """
        Creates a checkpoint of the current data
        """
        self.cp_backups.append(
            [len(b"".join(value)) for key, value in self._logs.items()])

    def assert_cp_diff(self, hash_val: str):
        """
        Computes a hash value from the difference of the single output
        targets (html, md, txt) and the new state and compares it to a
        provided value.

        :param hash_val: The hash value to compare to. Upon failure verify
            the different manually and copy & paste the hash value once
            the result was verified.
        """
        lengths = self.cp_backups.pop()
        difference = b''
        index = 0
        keys = []
        for key, value in self._logs.items():
            length = lengths[index]
            data = b"".join(value)
            index += 1
            if not isinstance(data, bytes):
                continue
            difference = difference + data[length:]
            keys.append(key)
        assert sorted(list(keys)) == sorted(list(self._log_formats))
        result_hash_val = hashlib.md5(difference).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)
