"""
Implements the class :class:`ClassServiceEntry` which represents a single
class being hosted via a :class:`WebStagClassService`.
"""

from __future__ import annotations

import types

from scistag.common import StagLock
from scistag.webstag.server import WebRequest, WebResponse

MISSING_FALLBACK_NAME = "_missing_"
"Name of the fallback method to be called if no method could be found"


class WebClassServiceEntry:
    """
    Defines the class entry for a single class which is published via http.

    It converts the http request parameters to object method parameters, calls
    the method if it is available and afterwards bundles the method's results
    to a http response again.
    """

    def __init__(
        self,
        class_type: type,
        multithread: bool = False,
        parameters: dict | None = None,
    ):
        """
        :param class_type: The type of the class to be instantiated
        :param multithread: Defines if the class is multithread secure and
            can be used in parallel
        :param parameters: The parameters to be passed to the object's
            constructor

            Note that these value will be kept and passed on upon first use
            of the object's services.
        """
        if parameters is None:
            parameters = {}
        self.class_type = class_type
        "The type of the class to construct for this service"
        self.parameters = parameters
        "The parameters to be passed to the object's initializer"
        self._init_lock = StagLock()
        "Lock for the first initialization of an object"
        self.access_lock = StagLock()
        "Lock for the execution of the object (if not multi-threading capable)"
        self.prepared = False
        "Flag if this service is setup "
        self.main_object = None
        "The object instance - will be created upon first use of the service"
        self.multithread = multithread
        "Defines if the service can be access from multiple threads"
        self.methods: dict[str, types.MethodType] = {}
        "The methods the object implements"

    def prepare(self):
        """
        Prepares the service and evaluate all available methods
        """
        with self._init_lock:
            if self.prepared:
                return
            self.main_object = self.class_type(**self.parameters)
            for field in dir(self.main_object):
                attr = getattr(self.main_object, field)
                if isinstance(attr, types.MethodType):
                    name = attr.__name__
                    if name.startswith("_") and name != MISSING_FALLBACK_NAME:
                        continue
                    if name.startswith("get_"):
                        name = name[4:]
                        if not hasattr(attr, "wsflags"):
                            attr.__dict__["ws_flags"] = {}
                        attr.__dict__["ws_flags"]["methods"] = {"GET"}
                    external_name_split = name.split("_")
                    elements = [external_name_split[0]] + [
                        element.title() for element in external_name_split[1:]
                    ]
                    external_name = "".join(elements)
                    self.methods[external_name] = attr
                    if external_name == "index":
                        self.methods[""] = attr

    def execute(self, request: WebRequest) -> WebResponse:
        """
        Executes the object's method by unwrapping all input parameters to
            the function's parameter list and vice versa all function results
            back to content returnable via http.

        :param request: The http request details
        :return: The http response
        """
        self.prepare()
        path = request.relative_path
        path_elements = path.split("/")
        if len(path_elements) > 1:
            path = path_elements[0]
            path_elements = path_elements[1:]
        else:
            path_elements = []
        if path in self.methods or MISSING_FALLBACK_NAME in self.methods:
            method = self.methods.get(path, MISSING_FALLBACK_NAME)
            parameters = {}
            for key, element in request.parameters.items():
                parameters[key] = element
            try:
                if self.multithread:  # no lock needed?
                    result = method(*path_elements, **parameters)
                else:
                    with self.access_lock:  # lock!
                        result = method(*path_elements, **parameters)
            except TypeError:
                return WebResponse(body="Invalid parameters provided", status=400)
            if result is None:
                return WebResponse(body="OK")
            if isinstance(result, tuple) and len(result) >= 2:
                assert isinstance(result[1], int)  # Verify HTTP code
                return WebResponse(body=result[0], status=result[1])
            if isinstance(result, WebResponse):
                return result
            return WebResponse(body=result)
        return WebResponse(body="Method not found", status=404)
