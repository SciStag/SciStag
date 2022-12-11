"""
Implements the :class:`Component` class - the base class for all intelligent
components such as Widgets and Slides.
"""
import os
from typing import Any

from scistag.common.cache import Cache


class Component(Cache):
    """
    The Component class integrates the functionality for intelligent property
    handling and dynamic data loading and unloading.

    It lays the foundation for the :class:`scistag.slidestag.widget.Widget`
    class which needs to automatically react to the change to single properties
    to minimize the need of using methods to do so while keeping the memory
    footprint of applications such as SlideStag as low as possible even when
    many users are using a service at the same time.

    * See :attr:`properties` for details about the property handling.
    """

    def __init__(self, cache_dir: str = None):
        super().__init__()
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
        
        :param cache_dir: The directory in which temporary computing results
            can be stored on disk.        
        """

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
