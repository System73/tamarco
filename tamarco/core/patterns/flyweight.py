import uuid


class Flyweight(type):
    """Metaclass that implements the Flyweight pattern.

    It is like a Singleton but only for the instances with the same key.
    The key is first parameter that you pass to the class when you create the object.

    This class is conceived for the internal use of the Tamarco metrics library.

    Example::

        >>> class Metric(metaclass=Flyweight):
        >>>     def __init__(self, metric_id):
        >>>         self.metric_id = metric_id
        >>>
        >>> http_requests_1 = Metric('http_requests')
        >>> http_requests_2 = Metric('http_requests')
        >>>
        >>> http_requests_1 == http_requests_2
        True
    """

    def __init__(cls, name, bases, dct):
        """Initialize the Flyweight class. The class can be call with one argument or three:

            >>> class Flyweight(object)
            >>> class Flyweight(name, bases, dict)

        With one argument, returns the type of an object. The return value is a type object and generally
        the same object as returned by object.__class__. With three arguments, returns a new type object.

        Args:
            name (Union[object, str]): when `name`is a str, is the class name and becomes the __name__ attribute.
            bases (tuple): itemizes the base classes and becomes the __bases__ attribute.
            dct (dict): is the namespace containing definitions for class body and is copied to a standard
                dictionary to become the __dict__ attribute.
        """
        cls.__instances = {}
        type.__init__(cls, name, bases, dct)

    def __call__(cls, key, *args, **kw):
        """Call cls as a function. It checks if the `key` instance already exists.

        Args:
            key (string): instance name.
            *args: Variable length argument list.
            **kw: Arbitrary keyword arguments.

        Returns:
            object: new instance is the key does not exist in the instances dictionary, or the instance
            already created with that key.
        """
        instance = cls.__instances.get(key)
        if instance is None:
            instance = type.__call__(cls, key, *args, **kw)
            cls.__instances[key] = instance
        return instance


class FlyweightWithLabels(Flyweight):
    """Metaclass that extends the pattern of the Flyweight pattern with labels.

    This class is conceived for the internal use of the Tamarco metrics library.

    Example::

        >>> class Metric(metaclass=FlyweightWithLabels):
        >>>     def __init__(self, metric_id, labels=None):
        >>>         self.metric_id = metric_id
        >>>         self.labels = labels if labels else {}
        >>>
        >>> requests_http_get_1 = Metric('request', labels={'protocol': 'http', 'method': 'get'})
        >>> requests_http_post_1 = Metric('request', labels={'protocol': 'http', 'method': 'post'})
        >>>
        >>> requests_http_get_2 = Metric('request', labels={'protocol': 'http', 'method': 'get'})
        >>> requests_http_post_2 = Metric('request', labels={'protocol': 'http', 'method': 'post'})
        >>>
        >>> requests_http_get_1 == requests_http_get_2
        True
        >>> requests_http_post_1 == requests_http_post_2
        True
    """

    def __init__(cls, name, bases, dct):
        """Initialize the FlyweightWithLabels class.

        Args:
            name (Union[object, str]): when `name`is a str, is the class name and becomes the __name__ attribute.
            bases (tuple): itemizes the base classes and becomes the __bases__ attribute.
            dct (dict): is the namespace containing definitions for class body and is copied to a standard
                dictionary to become the __dict__ attribute.
        """
        cls.__extended_instances = {}
        cls.__extended_instances_labels = {}
        Flyweight.__init__(cls, name, bases, dct)

    def __call__(cls, key, *args, **kw):
        """Call cls as a function. It checks if the `key` instance already exists.

        Args:
            key (string): instance name.
            *args: Variable length argument list.
            **kw: Arbitrary keyword arguments.

        Returns:
            object: new instance is the key with, its labels, does not exist in the instances dictionary,
            or the instance already created with that key and labels.
        """
        labels = kw.get("labels")
        if not labels:
            instance = Flyweight.__call__(cls, key, *args, **kw)
            return instance
        else:
            assert isinstance(labels, dict), "The labels should be a dictionary"
            extended_instances = cls.__extended_instances_labels.setdefault(key, {})
            for iter_label_id, iter_labels in extended_instances.items():
                if iter_labels == labels:
                    return cls.__extended_instances[iter_label_id]
            else:
                label_id = str(uuid.uuid4())
                extended_instance = type.__call__(cls, key, *args, **kw)
                cls.__extended_instances[label_id] = extended_instance
                cls.__extended_instances_labels[key][label_id] = labels
                return extended_instance
