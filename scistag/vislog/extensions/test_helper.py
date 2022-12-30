"""
Defines the class :class:`TestHelper` which helps creating
regression tests using a VisualLog by either verifying MD5 hash constants or
storing reference data on disk and comparing to it.
"""

from __future__ import annotations

import hashlib
import io

import numpy as np
import pandas as pd
from typing import TYPE_CHECKING
from matplotlib import pyplot as plt

from scistag.imagestag import Image, Canvas
from scistag.plotstag import Figure, Plot
from scistag.filestag import FileStag, FilePath
from scistag.vislog.extensions.builder_extension import BuilderExtension

if TYPE_CHECKING:
    from scistag.vislog.visual_log_builder import LogBuilder


class TestHelper(BuilderExtension):
    """
    Defines helper functions to write VisualLog based regression and unit tests
    """

    def __init__(self, builder: "LogBuilder"):
        """
        :param builder: The actual logging writer object we use to write
            the document
        """
        super().__init__(builder)
        self.checkpoint_backups = []
        "Data from the last checkpoints"

    def assert_figure(
        self,
        name: str,
        figure: plt.Figure | plt.Axes | Figure | Plot,
        hash_val: str,
        alt_text: str | None = None,
    ):
        """
        Adds a figure to the log and verifies its content to a checksum

        :param name: The figure's name
        :param figure: The figure to log
        :param alt_text: An alternative text to display if the figure can
            not be displayed.
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        """
        image_data = io.BytesIO()
        self.builder.figure(
            figure=figure, name=name, alt_text=alt_text, _out_image_data=image_data
        )
        assert len(image_data.getvalue()) > 0
        result_hash_val = hashlib.md5(image_data.getvalue()).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def assert_image(
        self,
        name: str,
        source: Image | Canvas,
        hash_val: str,
        scaling: float = 1.0,
        alt_text: str | None = None,
    ):
        """
        Assert an image object and verifies it's hash value matches the object's
        hash.

        :param name: The name of the object
        :param source: The data to log
        :param hash_val: The hash value to compare to (a checksum of all
            pixels). The correct will be logged via an assertion upon failure
            and can then be copies & pasted.
        :param scaling: The factor by which the image shall be scaled
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        """
        result_hash_val = self.log_and_hash_image(
            name=name, data=source, scaling=scaling, alt_text=alt_text
        )
        self.hash_check_log(result_hash_val, hash_val)

    def log_and_hash_image(
        self,
        name: str,
        data: Image | Canvas,
        alt_text: str | None = None,
        scaling: float = 1.0,
    ) -> str:
        """
        Writes the image to disk for manual verification (if enabled in the
        test_config) and returns it's hash.

        :param name: The name of the test.
            Will result in a file named logs/TEST_DIR/test_name.png
        :param data: The image object
        :param alt_text: An alternative text to display if the image can
            not be displayed.
        :param scaling: The factor by which the image shall be scaled
        :return: The image's hash for consistency checks
        """
        if isinstance(data, Canvas):
            data = data.to_image()
        self.builder.image(source=data, name=name, alt_text=alt_text, scaling=scaling)
        return data.get_hash()

    def assert_text(self, name: str, text: str, hash_val: str):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param text: The text data
        :param hash_val: The assumed hash value
        """
        _ = name
        result_hash_val = hashlib.md5(text.encode("utf-8")).hexdigest()
        self.builder.text(text)
        self.hash_check_log(result_hash_val, hash_val)

    def assert_df(
        self,
        name: str,
        df: pd.DataFrame,
        dump: bool = False,
        hash_val: str | None = None,
    ):
        """
        Asserts the integrity of a dataframe

        :param name: The name
        :param df: The data frame's part to verify
        :param dump: Defines if the data frame shall be dumped to disk.
            To this once for a new data frame to create a reference
        :param hash_val: If specified the dataframe will get dumped as csv
            of which the hash value is compared to the one passed.
        """
        if hash_val is not None:
            output = io.BytesIO()
            df.to_csv(output, lineterminator="\n")
            result_hash_val = hashlib.md5(output.getvalue()).hexdigest()
            if result_hash_val != hash_val:
                self.page_session.write_to_disk()
                raise AssertionError(
                    "Hash mismatch - "
                    f"Found: {result_hash_val} - "
                    f"Assumed: {hash_val}"
                )
            return
        if dump:
            output = io.BytesIO()
            df.to_parquet(output, engine="pyarrow")
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        comp_df = pd.read_parquet(io.BytesIO(comp_data), engine="pyarrow")
        if not comp_df.equals(df):
            raise AssertionError(f"Data mismatch between {name} and it's reference")

    def assert_np(
        self,
        name: str,
        data: np.ndarray,
        variance_abs: float | None = None,
        dump: bool = False,
        rounded: int = None,
        hash_val: bool | None = None,
    ):
        """
        Asserts a nunpy array for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param variance_abs: The maximum, absolute variance to the original,
            0.0 by default.
        :param dump: Defines if the current dump shall be overwritten.
            Set this once to true when you on purpose changed the data and
             verified it.
        :param rounded: Pass this if you want to hash floating point
            arrays where a rounded integer precision is enough.

            rounded defines how many digits behind the comma are relevant,
            so 0 rounds to full ints, +1 rounds to 0.1, +2 rounds to 0.01
            etc. pp.
        :param hash_val: The hash value to use as orientation.

            Do not use this for floating point data types due to
            platform dependent (slight) data discrepancies.
        """
        if rounded is not None:
            data = (data * (10**rounded)).astype(np.int64)
        if hash_val is not None:
            if data.dtype == float:
                raise NotImplementedError("Hashing not supported for float" "matrices")
            bytes_val = data.tobytes()
            result_hash_val = hashlib.md5(bytes_val).hexdigest()
            if result_hash_val != hash_val:
                self.page_session.write_to_disk()
                raise AssertionError(
                    "Hash mismatch - "
                    f"Found: {result_hash_val} - "
                    f"Assumed: {hash_val}"
                )
            return
        if dump:
            output = io.BytesIO()
            # noinspection PyTypeChecker
            np.save(output, data)
            self.save_ref(name, output.getvalue())
            print(f"Warning - Updating test reference of {name}")
        comp_data = self.load_ref(name)
        if comp_data is None:
            raise AssertionError(f"No reference data provided for {name}")
        # noinspection PyTypeChecker
        np_array = np.load(io.BytesIO(comp_data))
        if variance_abs == 0.0 or variance_abs is None:
            if np.all(np_array == data):
                return
        else:
            if np.all(np.abs(np_array - data) <= variance_abs):
                return
        raise AssertionError(f"Data mismatch between {name} and it's reference")

    def assert_val(
        self,
        name: str,
        data: dict | list | str | Image | Figure | pd.DataFrame,
        hash_val: str | None = None,
    ):
        """
        Asserts a text for validity and logs it

        :param name: The assertion's name
        :param data: The data
        :param hash_val: The assumed hash value (not required for data w/
            reference)
        """
        # image
        if isinstance(data, Image):
            self.assert_image(name, data, hash_val=hash_val)
            return
        # figure
        if isinstance(data, Figure):
            self.assert_figure(name, data, hash_val=hash_val)
            return
        # pandas data frame
        if isinstance(data, pd.DataFrame):
            self.assert_df(name, data)
            return
        # numpy array
        if isinstance(data, np.ndarray):
            self.assert_np(name, data, hash_val=hash_val)
            return
        if isinstance(data, str):
            self.assert_text(name, data, hash_val=hash_val)
            return
            # dict or list
        if isinstance(data, (list, dict, str)):
            self.builder.collection(data)  # no beautiful logging supported yet
            import json

            data = json.dumps(data).encode("utf-8")
        if data is None or not isinstance(data, bytes):
            raise NotImplementedError("Data type not supported")
        result_hash_val = hashlib.md5(data).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def save_ref(self, name: str, data: bytes):
        """
        Saves a new data reference

        :param name: The reference's unique name
        :param data: The data to store
        """
        hashed_name = self.builder.get_hashed_filename(name)
        FilePath.make_dirs(self.builder.target_log.ref_dir, exist_ok=True)
        hash_fn = self.builder.target_log.ref_dir + "/" + hashed_name + ".dmp"
        FileStag.save(hash_fn, data)

    def load_ref(self, name: str) -> bytes | None:
        """
        Loads the data reference

        :param name: The reference's unique name
        :return: The data. None if no reference could be found
        """
        hashed_name = self.builder.get_hashed_filename(name)
        hash_fn = self.builder.target_log.ref_dir + "/" + hashed_name + ".dmp"
        if FileStag.exists(hash_fn):
            return FileStag.load(hash_fn)
        return None

    def hash_check_log(self, value, assumed):
        """
        Verifies a hash and adds the outcome of a hash check to the output

        :param value: The hash value
        :param assumed: The assumed value
        """
        if value != assumed:
            self.builder.log(
                f"⚠️Hash validation failed!\nValue: " f"{value}\nAssumed: {assumed}",
                level="error",
            )
            self.builder.target_log.default_page.write_to_disk()
            raise AssertionError(
                "Hash mismatch - " f"Found: {value}\n" f"Assumed: {assumed}"
            )
        else:
            self.builder.log(f"{assumed} ✔")

    def checkpoint(self, checkpoint_name: str):
        """
        Creates a checkpoint of the current data
        """
        self.checkpoint_backups.append(
            {
                "name": checkpoint_name,
                "lengths": [
                    len(self.target_log.default_page._logs.build(key))
                    for key in sorted(self.builder.target_log.log_formats)
                ],
            }
        )

    def assert_cp_diff(self, hash_val: str):
        """
        Computes a hash value from the difference of the single output
        targets (html, md, txt) and the new state and compares it to a
        provided value.

        :param hash_val: The hash value to compare to. Upon failure verify
            the different manually and copy & paste the hash value once
            the result was verified.
        """
        last_checkpoint = self.checkpoint_backups.pop()
        lengths = last_checkpoint["lengths"]
        difference = b""
        index = 0
        keys = []
        for key in sorted(self.builder.target_log.log_formats):
            length = lengths[index]
            data = self.target_log.default_page._logs.build(key)
            index += 1
            if not isinstance(data, bytes):
                continue
            difference = difference + data[length:]
            keys.append(key)
        assert sorted(list(keys)) == sorted(list(self.builder.target_log.log_formats))
        result_hash_val = hashlib.md5(difference).hexdigest()
        self.hash_check_log(result_hash_val, hash_val)

    def begin(self, text: str) -> "LogBuilder":
        """
        Defines the beginning of a test
        :param text: The name to log
        :return: The log builder
        """
        self.builder.sub(text, level=3)
        return self.builder
