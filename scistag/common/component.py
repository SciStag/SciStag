"""
Implements the :class:`Component` class - the base class for all intelligent
components such as Widgets ans Slides.
"""


class Component:
    """
    The Component class integrates the functionality for intelligent property
    handling and dynamic data loading and unloading.

    It lays the foundation for the :class:`scistag.slidestag.widget.Widget`
    class which needs to automatically react to the change to single properties
    to minimize the need of using methods to do so while keeping the memory
    footprint of applications such as SlideStag as low as possible even when
    many users are using a service at the same time.

    * See :meth:`handle_load` for details about the dynamic loading of data on
        demand.
    * See :attr:`properties` for details about the property handling.
    """

    def __init__(self):
        self.properties = {}
        """
        Stores this classes' properties and their behavior.
        
        They define which properties automatically call a setter function when 
        being changed, which properties are
        read-only, their type etc.
        
        To for example define a property ``x`` which shall automatically call 
        it's change handler ``set_x`` when being changed just declare it as 
        common member variable, add it to this variable as key and declare 
        the ``set_x`` method. When ever you want to change it's value directly 
        via ``myComponent.x = newValue`` the ``set_x`` function will be called. 
        To prevent recursion this function then has to store the value directly 
        to the object's dictionary via `self.__dict__['x'] = new_value`.
        
        To define read-only properties set theirs "readOnly" flag such as 
        ``self.properties['x'] = {"readOnly": True}`` 
        
        For further details see :const:`Component.PROPERTIES`.        
        """
        self._cache = {}
        """
        A cache for temporary data storage and objects with a life time bound to
        this component's usage state.
         
        A cache which whose content shall only live between a handle_load() and
        handle_unload(). This can be used to store data only while a component 
        is being used, a Widget is visible etc. See :meth:`handle_load`.
        """
        self.loaded = False
        "Defines if the component was correctly loaded"
        self._is_loading = False
        """
        Flag which tells if the component is currently being loaded and if new 
        values added to the cache via ``self["objectName"]`` shall be flagged as 
        volatile.
        
        During the execution of the :meth:`load` function and their event 
        handlers such as :meth:`Widget.handle_load()` this value is set to true. 
        When new Widgets are added during this time or new values are added to 
        the cache, e.g. via  my_component["data"] = load_data() they are flagged 
        as volatile.
        
        After the execution of unload() all volatile entries will be deleted 
        from the cache and all widgets added as child will be automatically 
        removed again. 
        """
        self._volatile_cache_entries = set()
        """
        Stores which cache entries shall be deleted upon the execution of 
        :meth:`unload`.
        
        If a cache entry is added while ``_is_loading`` is set to True it will 
        be added to this set. Upon the execution of ``unload()`` all elements 
        named in this list will be removed from the :attr:`_cache`.
        
        In addition you may add object member variables via 
        :meth:`add_volatile_member` which do not get removed but automatically 
        cleared upon execution of unload. 
        """

    def load(self):
        """
        Call this before you start using a component for the first time. The
        ``scistag.slidestag.widget.Widget`` class does this automatically
        for all of it's children when a Widget becomes visible.
        """
        if self.loaded:
            raise RuntimeError("Tried to load component twice")
        self._is_loading = True
        self.handle_load()
        if not self.loaded:
            raise RuntimeError(
                "loaded flag of component not correctly set to True. "
                "Did you forget to call super().handle_load()?")

    def unload(self):
        """
        Call this this to unload all data from your component.
        """
        if not self.loaded:
            raise RuntimeError(
                "Tried to unload component which was not loaded before")
        self.handle_unload()
        if self.loaded:
            raise RuntimeError(
                "loaded flag of component not correctly set to False. "
                "Did you forget to call super().handle_unload()?")
        for element in self._volatile_cache_entries:
            element: str
            if element.startswith("."):  # clear volatile members
                member_name = element[1:]
                if member_name in self.__dict__:
                    self.__dict__[member_name] = None
            elif element in self._cache:  # delete volatile cache entries
                del self._cache[element]

    def get_is_loading(self) -> bool:
        """
        Returns if the component is currently being loaded
        :return: True if ``load`` is currently being executed for this
        component.
        """
        return self._is_loading

    def handle_load(self):
        """
        Event handling function for dynamically loading data on demand.

        SciStag's ``load`` and ``unload`` mechanism shall help minimizing the
        memory foot print of the application using it. If you have temporary
        data, for example a database which is just used while a component is
        used, a Slide or an ImageView while they are visible please overwrite
        this function, call it's ancestor and then store your data in the
        "cache".

        You can do so by using the bracket operator like ``self['db'] =
        pd.read_csv(...)``, check if data is
        available via ``if 'db' in self: ...`` and access it via ``my_db =
        self['db']`` accordingly.

        All data stored this way will automatically get cleared and removed from
        the cache when the `unload` function
        is called, e.g. when the Slide or Widget disappears or when you call it
        for your custom component.

        If you want to use member variables for storing your temporary data you
        can do so by calling
        :meth:`add_volatile_member` and passing their name. Upon unloading
        ``None`` will be assigned to all
        registered variables.

        **Note**: When overwriting this method call ``super().handle_load()``
        at the beginning of yours.
        """
        self.loaded = True

    def handle_unload(self):
        """
        Event handler for unloading elements previously loaded in your
        handle_load function.

        **Note**: When overwriting this method call ``super().handle_unload()``
        at **end** beginning of yours.
        """
        self.loaded = False

    def add_volatile_member(self, name: str) -> None:
        """
        Adds a member to the volatile cache entry variable list so it can
        automatically be cleared upon unloading of this component.

        When the component is unloaded (e.g. because a Widget or a Slide
        disappears) all members are automatically set to None to prevent that
        these objects are kept alive.

        :param name: The name of the member variable to be added to the volatile
        list.
        """
        self._volatile_cache_entries.add("." + name)

    def __setattr__(self, key, value) -> None:
        """
        Customizes the setter behavior of the attributes of Component class
        objects.

        If a property is defined in :attr:`properties` and a setter function
        with the name ``set_{key}`` exists it is automatically called instead of
        setting the value directly. If a property is flagged as "readOnly" and
        the user tries to modify this property a ValueException is raised.

        :param key: The key of the (potential) property
        :param value: The new value
        """
        properties = self.__dict__.get("properties", None)
        if properties is not None and key in properties:
            setter = getattr(self, f"set_{key}", None)
            if setter is not None:
                setter(value)
                return
            if self.properties[key].get("readOnly", False):
                raise ValueError("Tried to modify a read-only property")
        super().__setattr__(key, value)

    def __setitem__(self, key: str, value):
        """
        Adds an item to the cache or updates it.

        If a value is added (for the first time) during the execution of the
        component's ``load()`` or ``handle_load`` method it is flagged as
        volatile and will be automatically removed again upon the
        execution of ``unload()`` / ``handle_unload()``.

        :param key: The item's name
        :param value: The value to assign
        """
        assert len(key) > 0
        if not key[0].isalpha():
            raise ValueError("Keys has to start with a character")
        # flag of volatile if added during loading process
        if key not in self._cache and self._is_loading:
            self._volatile_cache_entries.add(key)
        self._cache[key] = value

    def __getitem__(self, item):
        """
        Returns a value from the cache.

        If the element does not exist a ValueError exception will be raised.

        :param item: The item's name.
        :return: The item's value
        """
        if item in self._cache:
            return self._cache[item]
        else:
            raise ValueError("Cache item not found")

    def __delitem__(self, key):
        """
        Deletes an element from the cache.

        If the element does not exist a ValueError exception will be raised.

        :param key: The element's name
        """
        if key not in self._cache:
            raise ValueError(f"The value {key} is not defined in the cache")
        del self._cache[key]

    def __contains__(self, item) -> bool:
        """
        Returns if an element exists in the cache.

        :param item: The item's name
        :return: True if the item exists.
        """
        return item in self._cache

    PROPERTIES = {}
    """
    The Component class' base properties as dictionary
    
    Every dictionary entry should have the following structure:
    
    * **info**: A short information describing the property's data
    * (optional) **type**: The property's type, either a string or a Python type
    * (optional) **readOnly**: Defines if the property may only be read.
        False by default
    
    A class derived from :class:`Component` should always extend it's ancestor
    class' PROPERTIES class attribute:
         
    ``PROPERTIES = {"myNewAttribute": {"info": "Example for a new attribute", 
    "type": int}} | Component.PROPERTIES``
    
    The PROPERTY class attribute should be assigned to every object's `property`
    object attribute at the end of it's constructor:
    
    ``self.properties = self.PROPERTIES``
    
    See :class:`scistag.slidestag.widget.Widget` for an extended example of it's
    usage.
    """
