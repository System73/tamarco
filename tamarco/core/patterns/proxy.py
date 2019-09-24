class Proxy:
    """Proxy pattern to be used as a pointer. When the value of _obj changes, the reference to
    the proxy remains.
    """

    __slots__ = ["_obj", "__weakref__"]

    def __init__(self, obj):
        """Initialize the Proxy class.

        Args:
            obj (object): New object to be used in the proxy.
        """
        object.__setattr__(self, "_obj", obj)

    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        """Get the value from the _obj attribute `name`.

        Args:
            name (string): Attribute name.

        Returns:
            Attribute value.
        """
        return getattr(object.__getattribute__(self, "_obj"), name)

    def __delattr__(self, name):
        """Delete the attribute `name` from the _obj object.

        Args:
            name (string): Attribute name.
        """
        delattr(object.__getattribute__(self, "_obj"), name)

    def __setattr__(self, name, value):
        """Set a value to the _obj attribute `name`.

        Args:
            name (string): Attribute name.
            value: Attribute value.
        """
        setattr(object.__getattribute__(self, "_obj"), name, value)

    def __bool__(self):
        """Convert an object to boolean.

        Returns:
            bool: Returns True when the evaluation of the _obj object is true, False otherwise.
        """
        return bool(object.__getattribute__(self, "_obj"))

    def __str__(self):
        """Compute the "informal" or nicely printable string representation of the _obj object.

        Returns:
            str: String representation of the _obj object.
        """
        return str(object.__getattribute__(self, "_obj"))

    def __repr__(self):
        """Compute the "official" string representation of the _obj object.

        Returns:
            str: String representation of the _obj object.
        """
        return repr(object.__getattribute__(self, "_obj"))

    #
    # factories
    #
    _special_names = [
        "__abs__",
        "__add__",
        "__and__",
        "__call__",
        "__cmp__",
        "__coerce__",
        "__contains__",
        "__delitem__",
        "__delslice__",
        "__div__",
        "__divmod__",
        "__eq__",
        "__float__",
        "__floordiv__",
        "__ge__",
        "__getitem__",
        "__getslice__",
        "__gt__",
        "__hash__",
        "__hex__",
        "__iadd__",
        "__iand__",
        "__idiv__",
        "__idivmod__",
        "__ifloordiv__",
        "__ilshift__",
        "__imod__",
        "__imul__",
        "__int__",
        "__invert__",
        "__ior__",
        "__ipow__",
        "__irshift__",
        "__isub__",
        "__iter__",
        "__itruediv__",
        "__ixor__",
        "__le__",
        "__len__",
        "__long__",
        "__lshift__",
        "__lt__",
        "__mod__",
        "__mul__",
        "__ne__",
        "__neg__",
        "__oct__",
        "__or__",
        "__pos__",
        "__pow__",
        "__radd__",
        "__rand__",
        "__rdiv__",
        "__rdivmod__",
        "__reduce__",
        "__reduce_ex__",
        "__repr__",
        "__reversed__",
        "__rfloorfiv__",
        "__rlshift__",
        "__rmod__",
        "__rmul__",
        "__ror__",
        "__rpow__",
        "__rrshift__",
        "__rshift__",
        "__rsub__",
        "__rtruediv__",
        "__rxor__",
        "__setitem__",
        "__setslice__",
        "__sub__",
        "__truediv__",
        "__xor__",
        "next",
    ]

    @staticmethod
    def make_method(name):
        """Create a new method to getting the value of the attribute `name`.

        Args:
            name (string): Attribute name.

        Returns:
            function: New __getattribute__ method to get a value from the _obj object.
        """

        def method(self, *args, **kw):
            return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)

        return method

    @classmethod
    def _create_class_proxy(cls, the_class):
        """Create a proxy for the given class.

        Args:
            the_class (class): Class type in which we want to use the proxy.

        Returns:
            object: New proxy instance referencing the `the_class` class.
        """
        namespace = {}
        for name in cls._special_names:
            if hasattr(the_class, name):
                namespace[name] = cls.make_method(name)
        return type(f"{cls.__name__}({the_class.__name__})", (cls,), namespace)

    def __new__(cls, obj, *args, **kwargs):
        """Create an proxy instance referencing `obj`.

        (obj, *args, **kwargs) are passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.

        _class_proxy_cache is unique per deriving class (each deriving class must hold its own cache).

        Args:
            obj (object): Instance of the class in which we want to use the proxy.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            object: New proxy instance referencing `obj`.
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            the_class = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = the_class = cls._create_class_proxy(obj.__class__)
        instance = object.__new__(the_class)
        the_class.__init__(instance, obj, *args, **kwargs)
        return instance
