from tamarco.resources.basic.metrics.meters.base import BaseMeter, Timer, metric_factory, spy_factory


class Gauge(BaseMeter):
    """A gauge is a metric that represents a single numerical value that can arbitrarily go up and down.
    Gauges are typically used for measured values like temperatures or current memory usage,
    but also "counts" that can go up and down, like the number of running routines.
    The initial value is 0 by default and the reset it at the restart.
    It can be used as a timer, it is useful for batch jobs. You need to take in account that this kind
    of data only save the last value, so if the Gauge is called a lot of times in the collect period
    probably a summary is a best choice, because it computes some useful statistics.

    Example:
        >>> current_websocket_connections = Gauge("current_websocket_connections", "ws")
        >>>
        >>> class WebSocketServer:
        >>>     @current_websocket_connections
        >>>     def on_open(self):
        >>>         ...
        >>>
        >>>     def on_close(self):
        >>>         current_websocket_connections.dec()
        >>>         ...
        >>>
        >>>     @Gauge("close_all_conections", "seconds").timeit()
        >>>     def close_all_conections(self):
        >>>         ...
    """

    def __init__(self, metric_id, measurement_unit, start_value=0, labels=None):
        super().__init__(metric_id, measurement_unit, labels=labels, start_value=start_value)
        self.value = start_value
        self.parent_meter = None

    def timeit(self):
        """Allows a gauge to work as a Timer.
        The returned object of timeit() is a Timer and can be used as decorator and context manager.

            >>> import time
            >>>
            >>> task_gauge = Gauge("task", "time")
            >>>
            >>> # This are going to print the elapsed time in this function every time it is called.
            >>> @task_gauge.timeit()
            >>> def some_task():
            >>>         time.sleep(1)
            >>>
            >>> # It also works with coroutines.
            >>> import asyncio
            >>>
            >>> @task_gauge.timeit()
            >>> async def some_task():
            >>>         await asyncio.sleep(1)
            >>>
            >>> # And as a context manager
            >>> with task_gauge.timeit()
            >>>     time.sleep(1)
        """
        return Timer(callback=lambda time: self.set(time))

    def inc(self, value=1):
        """Increase the value of the gauge.

        Args:
            value: Integer or float with the value to increment, the default value is 1.
        """
        self._check_valid_value(value)
        self.value += value

    def dec(self, value=1):
        """Decrease the value of the gauge.

        Args:
            value: Integer or float with the value to decrease, the default value is 1.
        """
        self._check_valid_value(value)
        self.value -= value

    def set(self, value):  # noqa: A003
        """Set the gauge to one value.

        Args:
            value: Integer or float with the value to set.
        """
        self._check_valid_value(value)
        self.value = value

    def set_to_current_time(self):
        """Set the gauge to the current unix timestamp in seconds."""
        self.value = self.timestamp

    @staticmethod
    def _check_valid_value(value):
        assert isinstance(value, int) or isinstance(
            value, float
        ), "Invalid value for Gauge, it only works with integers and floats"

    def _collect_metrics(self):
        return [metric_factory(self.metric_id, self.value, self.measurement_unit, self.timestamp, labels=self.labels)]

    def __call__(self, function):
        """Allow the gauge to work as a decorator, it increases the gauge once every time the function is called."""
        spy_factory(function, lambda: self.inc())
