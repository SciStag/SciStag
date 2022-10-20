"""
Implements the class :class:`WebStagClassService` which allows publishing a
Python class as web service with minimal effort.
"""

from __future__ import annotations

from scistag.common import StagLock
from scistag.webstag.server.class_service_entry import WebClassServiceEntry
from scistag.webstag.server import WebRequest, WebStagService, WebResponse


class WebClassService(WebStagService):
    """
    The WebStagClassService allows publishing a simple Python class as web
    service.

    * If not passed otherwise in :meth:`add_class` the service's route will
      be the lower camel-case variant of the class' name, the same applies to
      all member functions.

      e.g. MyTestClass.print_hello_world will be published as
      /myTestClass/helloWorld.
    * Functions beginning with a ``get_`` will automatically be interpreted as
      getter functions and published as such. The ``get_` name component will
      automatically be stripped upon publishing.

      Example. MyClass.get_item_count -> /myClass/itemCount.
    """

    def __init__(self, service_name: str, url_prefix: str, support_flask=False):
        """
        :param service_name: The name under which the service is registered.
            Just has to be unique.
        :param url_prefix: The url_prefix under which the service will be
            registered.

            e.g. "myService" will be hosted under the url
            myService/myClass/myMethod.
        :param support_flask: Defines if the service shall be configured for
            flask
        """
        WebStagService.__init__(self, service_name=service_name,
                                bp_reg_params={"url_prefix": url_prefix})
        self._access_lock = StagLock()
        self._classes: dict[str, WebClassServiceEntry] = {}
        if support_flask:
            self.setup_wrapper_blueprint()

    def add_class(self, class_type, service_name: str | None = None,
                  multithread: bool = False, parameters: dict | None = None):
        """
        Registers a new class type

        :param class_type: The class to register.

            A singleton object of the class will be created upon first use.
        :param service_name: The name under which the service shall be
            reached
        :param multithread: Defines if the created object is
            multi-thread secure. If it's not than the service will not
            allow more than one caller at the same time.
        :param parameters: The parameters to be passed to the object's
            constructor.

            Note that these value will be kept and passed on upon first use
            of the object's services.
        """
        if service_name is None:
            service_name = class_type.__name__
            if len(service_name) > 1:
                service_name = service_name[0].lower() + service_name[1:]
        with self._access_lock:
            if service_name in self._classes:
                raise AssertionError(f"Service {service_name} already exists")
            self._classes[service_name] = \
                WebClassServiceEntry(class_type,
                                     multithread=multithread,
                                     parameters=parameters)

    def handle_unified_request(self, request: WebRequest) -> WebResponse:
        elements = request.relative_path.split("/")
        base_element = 1  # the first element identifying the service
        root_element = elements[0]
        with self._access_lock:
            # always prefer a registered class name over a method name
            # if no class could be found but a zero-length named class
            # was registered, try let the class handle it
            if root_element not in self._classes and "" in self._classes:
                base_element = 0
                root_element = ""
        class_entry = None
        with self._access_lock:
            if root_element in self._classes:
                class_entry = self._classes[root_element]
        if class_entry is not None:
            request.relative_path = "/".join(elements[base_element:])
            result = class_entry.execute(request)
            return result
        return WebResponse(body="Not found :(", status=404)
