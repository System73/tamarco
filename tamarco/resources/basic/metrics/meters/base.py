import asyncio
import time
from collections import namedtuple
from copy import copy
from functools import wraps

import inflection

from tamarco.core.patterns import FlyweightWithLabels
from tamarco.resources.basic.metrics.collector import MetricsCollector

Metric = namedtuple("Metric", ["id", "labels", "value", "units", "timestamp", "empty"])


def metric_factory(metric_id, value, units, timestamp, empty=False, labels=None):
    return Metric(
        id=metric_id, value=value, units=units, timestamp=timestamp, empty=empty, labels=labels if labels else {}
    )


class BaseMeter(metaclass=FlyweightWithLabels):
    """Common part of all the meters."""

    def __init__(self, metric_id, measurement_unit, labels=None, *args, **kwargs):
        self.metric_id = metric_id
        self.metric_type = inflection.underscore(self.__class__.__name__)
        self.labels = labels if labels else {}
        self.measurement_unit = measurement_unit
        self.init_args = args
        self.init_kwargs = kwargs
        MetricsCollector.register_metric(self)

    @property
    def timestamp(self):
        return time.time()

    def new_labels(self, labels):
        """Return another instance of the meter with other labels.
        Used for adding or updating labels on the fly.

        Examples:
            >>> http_meter = BaseMeter("http_requests", "requests", labels={'protocol': 'http'})
            >>>
            >>> def handle_http_404():
            >>>    error_meter = http_meter.new_labels({'status_code': 404})
        """
        updated_labels = copy(self.labels)
        updated_labels.update(labels)
        return self.__class__(
            key=self.metric_id,
            measurement_unit=self.measurement_unit,
            labels=updated_labels,
            *self.init_args,
            **self.init_kwargs
        )


class Timer:
    """Measures intervals of time.
    The instances of this class measure intervals of time and when calls the callback with the period of time in seconds
    Them can work as a decorator for functions or coroutines or as a context manager.
    This class is conceived for the internal use of the Tamarco metrics library.

    Example:
        >>> # This are going to print the elapsed time in this function every time it is called.
        >>> @Timer(callback=lambda time: print(f"The elapsed time is {time}"))
        >>> def some_task():
        >>>         time.sleep(1)
        >>>
        >>> some_task()
        >>>
        >>> # It also works with coroutines.
        >>> import asyncio
        >>>
        >>> @Timer(callback=lambda time: print(f"The elapsed time is {time}"))
        >>> async def some_task():
        >>>         await asyncio.sleep(1)
        >>>
        >>> asyncio.get_event_loop().run_until_complete(some_task())
        >>>
        >>> # And as a context manager
        >>> with Timer(callback=lambda time: print(f"The elapsed time is {time}")):
        >>>     time.sleep(1)

    """

    def __init__(self, callback):
        self.callback = callback
        self.time_start = None
        self.time_end = None

    def __enter__(self):
        """Allow the timer to behave as a context manager."""
        self.time_start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Allow the timer to behave as a context manager."""
        time_end = time.time()
        value = time_end - self.time_start
        self.callback(value)

    def __call__(self, func):
        """Allow the timer to behave as a decorator."""
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(*args, **kwargs):
                with self:
                    return await func(*args, **kwargs)

        else:

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)

            return wrapper
        return wrapper


class ExceptionMonitor:
    """Provides the ability to trigger an event_callback when an exception is captured.
    Work as a context manager and as a decorator.

    This class is conceived for the internal use of the Tamarco metrics library.

    Example:
        >>> exception_monitor = ExceptionMonitor(lambda : print('Exception !!'))
        >>>
        >>> with exception_monitor:
        >>>     raise Exception
        >>>
        >>> @exception_monitor
        >>> def exception_monitor():
        >>>    raise Exception
    """

    def __init__(self, event_callback):
        self.event_callback = event_callback

    def __call__(self, function):
        if asyncio.iscoroutinefunction(function):

            @wraps(function)
            async def wrapper(*args, **kwargs):
                try:
                    return await function(*args, **kwargs)
                except Exception:
                    self.event_callback()
                    raise

        else:

            @wraps(function)
            def wrapper(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except Exception:
                    self.event_callback()
                    raise

            return wrapper
        return wrapper

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.event_callback()


def spy_factory(wrapped_object, event_callback):
    """Return a wrapped object that triggers the event callback every time the object is called.

    Example:
        >>> SpyObject = spy_factory(object, lambda: print("A object is created"))
        >>> SpyObject() # This line also print the line "A object is created"

    Args:
        wrapped_object: Object to wrap.
        event_callback: Function to be called when the object is called.

    Returns:
        Wrapped object.
    """
    if asyncio.iscoroutinefunction(wrapped_object):

        @wraps(wrapped_object)
        async def wrapper(*args, **kwargs):
            event_callback()
            return await wrapped_object(*args, **kwargs)

    else:

        @wraps(wrapped_object)
        def wrapper(*args, **kwargs):
            event_callback()
            return wrapped_object(*args, **kwargs)

    return wrapper
