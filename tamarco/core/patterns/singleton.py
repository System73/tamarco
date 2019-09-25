class Singleton(type):
    """Singleton pattern implementation.

    This pattern restricts the instantiation of a class to one object.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call cls as a function. It checks if the instance already exists.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            object: Instance from the class that uses this pattern.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
