from copy import copy
from functools import wraps

from tamarco.resources.basic.metrics.meters.base import BaseMeter, ExceptionMonitor, metric_factory, spy_factory


class Counter(BaseMeter):
    """A counter is a cumulative metric that represents a single numerical value that only ever goes up.
    The counter reset when the server restart.
    A counter is typically used to count requests served, tasks completed, errors occurred, etc.
    Counters should not be used to expose current counts of items whose number can also go down,
    e.g. the number of currently running coroutines. Use gauges for this use case.

    Example:
        >>> cats_counter = Counter('cats', 'cat')
        >>> cats_meow_counter = Counter('meows', 'meow')
        >>> cats_jump_counter = Counter('jumps', 'jump')
        >>>
        >>> # For example, we can count the cats in our server
        >>>
        >>> class Cat:
        >>>     def __init__(self):
        >>>         cats_counter.inc()
        >>>
        >>>     # Works as a decorator
        >>>     @cats_meow_counter
        >>>     def meow(self):
        >>>         print('meow')
        >>>
        >>>     # Also as a decorator of coroutines
        >>>     @cats_jump_counter
        >>>     async def jump(self):
        >>>         print("\\n")

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    def current_value(self):
        """Returns the current value of the counter."""
        return self.counter

    def inc(self, value=1):
        """Increase the value of the counter, the default value is 1.

        Args:
            value: Number to increment.
        """
        assert (
            isinstance(value, int) or isinstance(value, float)
        ) and value >= 0, "Counter only operates with positive integers or floats"
        self.counter += value

    def count_exceptions(self):
        """It works as a decorator or as context manager.
        The exceptions aren't silenced.

        Example:
            >>> exceptions_counter = Counter("exceptions", 'exception')
            >>>
            >>> with exceptions_counter.count_exceptions():
            >>>     print('Counting exceptions in this context')
            >>>     ...
            >>>
            >>> http_errors = Counter("http_errors", 'error')
            >>>
            >>> @http_errors.count_exceptions()
            >>> async def http_handler(request):
            >>>     ...
        """
        return ExceptionMonitor(lambda: self.inc())

    def __call__(self, function):
        """
        Allow the Counter to work as a decorator of a function or a coroutine.

        Args:
            function: Function to decorate.

        Returns:
            Wrapped function that increases the counter in each call.
        """
        return spy_factory(function, lambda: self.inc())

    def _collect_metrics(self):
        return [metric_factory(self.metric_id, self.counter, self.measurement_unit, self.timestamp, labels=self.labels)]


class HTTPCounter(Counter):
    def __init__(self, metric_id, *args, **kwargs):
        kwargs.setdefault("measurement_unit", "requests")
        kwargs.setdefault("labels", {})["http_counter"] = "requests"
        super().__init__(metric_id, **kwargs)
        kwargs["labels"] = self._update_label(kwargs["labels"], {"exceptions": "uncaptured"})
        self.exception_counter = Counter(f"{metric_id}", *args, **kwargs)
        kwargs["labels"] = self._update_label(kwargs["labels"], {"http_counter": "errors"})
        self.errors_counter = Counter(f"{metric_id}", *args, **kwargs)

    @staticmethod
    def _update_label(labels, extra_label):
        copy_labels = copy(labels)
        copy_labels.update(extra_label)
        return copy_labels

    def __call__(self, function):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            self.inc()
            with self.exception_counter.count_exceptions():
                response_value = await function(*args, **kwargs)
            if hasattr(response_value, "status") and response_value.status >= 400:
                self.errors_counter.inc()
            return response_value

        return wrapper


class HeaderToLabel:
    """Used to map the headers of a http petition to a certain prometheus labels.
    The object needs to be passed to the HTTPCounterHeaderMap.
    """

    def __init__(self, header, label, default_header_value):
        """
        Args:
            header (str): Header of the http request to map.
            label (str): Label in prometheus where you want to count the headers.
            default_header_value (str): Default value if the header doesn't exist.
        """
        self.header = header
        self.label = label
        self.default_header_value = default_header_value


class HTTPCounterHeaderMap(HTTPCounter):
    """Counter to use in conjunction with the handlers of a Sanic server.
    It is a decorator that counts the http petitions and unexpected exceptions managed
    by the handler. It also labels the metrics with the status codes of the responses
    and the headers of the request.

    Example:
        >>> customer_map = HeaderToLabel(header='Customer', label='customer_id', default_header_value='not available')
        >>>
        >>> @HTTPCounterHeaderMap('orders', header_to_label_maps=[customer_map])
        >>> async def get_all_orders_by_customer_handler(request):
        >>>     ...
        >>>
    """

    def __init__(self, metric_id, *args, **kwargs):
        """
        Args:
            metric_id (str): Metric identifier.
            *args: Arguments for HTTPCounter.
            **kwargs: Keyword arguments for HTTPCounterHeaderMap.
        """
        self.header_to_label_maps = kwargs.get("header_to_label_maps", {})
        super().__init__(metric_id, *args, **kwargs)

    def __call__(self, function):
        @wraps(function)
        async def wrapper(request, *args, **kwargs):
            labels = {"path": request.path, "method": request.method}
            for header_map in self.header_to_label_maps:
                labels.update(
                    {header_map.label: request.headers.get(header_map.header, header_map.default_header_value)}
                )
            with self.exception_counter.new_labels(labels).count_exceptions():
                response = await function(request, *args, **kwargs)
                labels.update({"status_code": response.status})
                self.new_labels(labels).inc()
            return response

        return wrapper
