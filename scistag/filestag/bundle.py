"""
Helps to bundle a list of common data types such as bytes, dictionaries
and numpy arrays in a zip file.
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

from pydantic import BaseModel

from scistag.common.classes import ClassHelper
from scistag.common.mt.stag_lock import StagLock
from scistag.filestag.memory_zip import MemoryZip

IS_TUPLE_FLAG = "is_tuple"
"""
A flag which is attached to a list property if it was originally a tuple and
need to be backconverted upon reading.
"""

BI_SIMPLE_ELEMENT_FLAG = "__bi_"
"""
Additional entry which can be stored in the simple_elements list to further 
specify details about a simple element if required
"""

TUPLE = "tuple"
"Defines the input/output type tuple"
LIST = "list"
"Defines the input/output type list"
SINGLE = "single"
"Defines the input/output type single variable"
DICT = "dict"
"Defines the input/output type dict"

BUNDLE_INFO_NAME = "__bundle_info.json"
"Filename of the bundle info within the zip archive"


class BundleElementInfo(BaseModel):
    """
    Defines a single bundle element
    """

    version: int = 1
    "The protocol version"
    data_type: Optional[str] = None
    """
    The object's data type. Only needs to be provided if the data type
    is advanced, e.g. not "just" an integer or string, otherwise the
    type is derived from data.
    """
    properties: Optional[dict] = None
    "Optional advanced properties"


_simple_types = [str, float, int, bool, dict, list, tuple]
"The simple data types which do not need an own file to be stored in"


class BundleInfo(BaseModel):
    """
    Defines the bundle information
    """

    source_type: Literal["dict", "tuple", "list", "single"]
    "The list of keys in their original order"
    keys: list[str]
    "The source type"
    adv_elements: dict[str, BundleElementInfo]
    "The advanced elements and their descriptor"
    simple_elements: dict[str, Any]
    "The simple elements which can make use of direct key value storage"
    version: int = 1
    "The protocol version"
    recursive: bool = False
    """
    Defines if the elements of the first level e.g. dictionaries and lists
    may contain further, bundled advanced types such as np.arrays.
    """


@dataclass
class BundlingOptions:
    """
    Options for bundling the data
    """

    recursive = False
    "Defines if the data shall be bundled recursive (not supported yet)"


@dataclass
class UnpackOptions:
    """
    Options for bundling the data
    """

    recursive = False
    "Defines if the data shall be bundled recursive (not supported yet)"


BundleToBytesCallback = Callable[[Any, BundlingOptions], tuple[str, bytes]]
"""
Function definition for plugins which help converting data types of various
kinds to bytes.
"""

UnpackFromBytesCallback = Callable[[bytes, UnpackOptions], Any]
"""
Helper function for converting data back from bytes to their original type
"""


class Bundle:
    """
    The bundle class is able to store a list, a tuple or a dictionary in a
    zip file. In case of a dictionary only the "first" level can be used
    for the storage of "advanced" data types such as images, DataFrames, numpy
    arrays etc.

    With help of the Bundle class function parameters can easily be passed
    between different processes, clients and servers without the need to
    pickle them and in consequence without being bound to fully compatible
    module versions by using common interchange formats such as parquet files
    or json files.
    """

    _access_lock = StagLock()
    "Configuration access lock"
    _base_types_registered = False
    "Defines if the base types were registered"
    _bundlers: dict[str, BundleToBytesCallback] = {}
    """
    Registered functions to convert an of type key to it's bytes representation
    """
    _unpackers: dict[str, UnpackFromBytesCallback] = {}
    """
    Registered functions to convert an object from a known type and it's 
    bytes representation back to it's original form such as a dictionary, numpy
    array or pandas DataFrame
    """

    @classmethod
    def bundle(
        cls,
        elements: dict[str, Any] | list[Any] | tuple,
        compression: int | None = None,
    ) -> bytes:
        """
        Stores a dictionary, a list or a tuple in a zip file in memory and
        returns its bytes string representation which can then for
        example be passed to another process, client or server and extracted
        there or just be dumped to a database or a disk.

        :param elements: The elements to be stored. Supported data types are
        (w/o extensions which may be registered) dictionaries, lists, tuples,
        strings, floats, booleans, Pandas DataFrames, DataSeries, numpy
        arrays and byte strings.
        :param compression: The compression level (from 0 to 99) (fast to small)
        :return: The bytes dump of the zip archive.
        """
        cls._ensure_base_types()
        options = BundlingOptions()
        if compression is None:
            compression = 10
        comp_level = min(max((compression // 10), 0), 9)
        comp_method = zipfile.ZIP_STORED if comp_level == 0 else zipfile.ZIP_DEFLATED
        with MemoryZip(compresslevel=comp_level, compression=comp_method) as mem_zip:
            source_type = (
                DICT
                if isinstance(elements, dict)
                else LIST
                if isinstance(elements, list)
                else TUPLE
                if isinstance(elements, tuple)
                else SINGLE
            )
            if source_type is SINGLE:
                elements = [elements]
            keys = []
            simple = {}
            advanced = {}
            if not isinstance(elements, dict):  # convert to dict if necessary
                new_elements = {}
                for index, data in enumerate(list(elements)):
                    new_elements[f"__{index:04d}__"] = data
                elements = new_elements
            for key, element in elements.items():
                keys.append(key)
                if type(element) in _simple_types:
                    # store basic types directly
                    simple[key] = element
                    if isinstance(element, tuple):  # remember original type
                        simple[BI_SIMPLE_ELEMENT_FLAG + key] = {IS_TUPLE_FLAG: True}
                    continue
                data_type, byte_data = cls.to_bytes(element, options=options)
                advanced[key] = BundleElementInfo(data_type=data_type)
                mem_zip.writestr(key, byte_data)
            bundle_info = BundleInfo(
                source_type=source_type,
                keys=keys,
                simple_elements=simple,
                adv_elements=advanced,
            )
            mem_zip.writestr(
                BUNDLE_INFO_NAME, json.dumps(bundle_info.model_dump_json()).encode("utf-8")
            )
        return mem_zip.to_bytes()

    @classmethod
    def unpack(cls, data: bytes) -> dict[str, Any] | list[Any] | tuple:
        """
        Unpacks a previously bundled data package to it's original form

        :param data: The data to unpack (as returned by :meth:`bundle`)
        :return: The dictionary, tuple or list containing the bundled objects
        """
        if data is None:
            raise ValueError("data is None")
        cls._ensure_base_types()
        options = UnpackOptions()
        with MemoryZip(data) as mem_zip:
            if BUNDLE_INFO_NAME not in mem_zip.NameToInfo:
                raise AssertionError("Could not find bundle info")
            data = mem_zip.read(BUNDLE_INFO_NAME).decode("utf-8")
            data = json.loads(data)
            bundle_info: BundleInfo = BundleInfo.model_validate_json(data)
            result = {}
            # reconstruct all objects
            result_elements = []
            simple = bundle_info.simple_elements
            adv = bundle_info.adv_elements
            for key in bundle_info.keys:
                if key in simple:
                    data = simple[key]
                    if isinstance(data, list):
                        add_info_name = BI_SIMPLE_ELEMENT_FLAG + key
                        # check special flags, e.g. list to tuple conversion
                        if add_info_name in simple:
                            if simple[add_info_name].get(IS_TUPLE_FLAG, False):
                                data = tuple(data)
                    result[key] = data
                    result_elements.append(data)
                else:
                    byte_stream = mem_zip.read(key)
                    rec_object = cls.from_bytes(
                        data_type=adv[key].data_type, data=byte_stream, options=options
                    )
                    result[key] = rec_object
                    result_elements.append(rec_object)
            st = bundle_info.source_type
            if st == DICT:  # just a dict? we're done
                return result
            if st == LIST:
                return result_elements
            if st == SINGLE:
                return result_elements[0]
            if st == TUPLE:
                return tuple(result_elements)
            raise NotImplementedError(f"The return type {st} is not supported")

    @classmethod
    def to_bytes(cls, element: Any, options: BundlingOptions) -> tuple[str, bytes]:
        """
        Converts an element to its storable bytes representation

        :param element: The element to convert to bytes
        :param options: Advanced bundling options
        :return: The data type to be stored in the bundle and the bytes string
        """
        el_type = ClassHelper.get_full_class_name(element)
        bundler = None
        with cls._access_lock:
            if el_type in cls._bundlers:
                bundler = cls._bundlers[el_type]

            if bundler is None:
                if el_type in cls._bundlers:
                    bundler = cls._bundlers[el_type]
            if bundler is None:
                raise NotImplementedError(
                    f"No bundler found for data type {str(el_type)}"
                )
        return bundler(element, options)

    @classmethod
    def from_bytes(cls, data_type: str, data: bytes, options: UnpackOptions) -> Any:
        """
        Converts an object from it's byte representation back to its
        normal form.

        :param data_type: The data type as returned from to_bytes
        :param data: The data
        :param options: Advanced unpacking options
        :return: The reconstructed object
        """
        with cls._access_lock:
            if data_type not in cls._unpackers:
                return NotImplementedError(
                    f"No unpacker found for data type {data_type}"
                )
            unpacker = cls._unpackers[data_type]
        return unpacker(data, options)

    @classmethod
    def register_bundler(cls, data_type: str, callback: BundleToBytesCallback):
        """
        Registers a new bundling helper function

        :param data_type: The data type as unique string to look out for
        :param callback: The function be called to bundle the data
        """
        with cls._access_lock:
            cls._bundlers[data_type] = callback

    @classmethod
    def register_unpacker(cls, data_type: str, callback: UnpackFromBytesCallback):
        """
        Registers a new unpacking helper function

        :param data_type: The data type as string to look out for (as
            stored in the dictionary of the bundled data and returned by
            the corresponding BundleToBytesCallback)
        :param callback: The function be called to unpack the data
        """
        with cls._access_lock:
            cls._unpackers[data_type] = callback

    @classmethod
    def is_type_supported(cls, element) -> bool:
        """
        Returns if the object may be bundled.

        Does not deep dive into the object but just scans the highest level.

        :param element: The element you would like to bundle, e.g. to transfer it
        :return: True if it's possible to bundle the object
        """
        if isinstance(element, (int, str, float, bool, bytes, list, tuple, dict)):
            return True
        with cls._access_lock:
            fcn = ClassHelper.get_full_class_name(element)
            return fcn in cls._bundlers

    @classmethod
    def _ensure_base_types(cls):
        """
        Ensures that all base types are registered
        """
        with cls._access_lock:
            if not cls._base_types_registered:
                cls._base_types_registered = True
                _register_base_types()


def _register_base_types():
    """
    Registers the base types which can be bundled
    """
    # bytes packing and unpacking
    Bundle.register_bundler("bytes", lambda data, options: ("bytes", data))
    Bundle.register_unpacker("bytes", lambda data, options: data)
    from .bundlers.numpy_bundler import NumpyBundler
    from .bundlers.dataframe_bundler import DataFrameBundler, DataSeriesBundler

    # Numpy array
    Bundle.register_bundler(NumpyBundler.NP_CLASS_NAME, NumpyBundler.bundle)
    Bundle.register_unpacker(NumpyBundler.NP_CLASS_NAME, NumpyBundler.unpack)
    # Pandas DataFrame
    Bundle.register_bundler(DataFrameBundler.DF_CLASS_NAME, DataFrameBundler.bundle)
    Bundle.register_unpacker(DataFrameBundler.DF_CLASS_NAME, DataFrameBundler.unpack)
    Bundle.register_unpacker(
        "DataFrameBundler", DataFrameBundler.unpack  # for backwards compatibility
    )
    # Pandas Series
    Bundle.register_bundler(
        DataSeriesBundler.SERIES_CLASS_NAME, DataSeriesBundler.bundle
    )
    Bundle.register_unpacker(
        DataSeriesBundler.SERIES_CLASS_NAME, DataSeriesBundler.unpack
    )
