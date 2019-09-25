from tamarco.resources.basic.metrics.meters.base import BaseMeter, Timer, metric_factory
from tamarco.resources.basic.metrics.settings import DEFAULT_SUMMARY_QUANTILES


class Summary(BaseMeter):
    """A summary samples observations (usually things like request durations) over sliding windows of time
    and provides instantaneous insight into their distributions, frequencies, and sums.

    The default quantiles are: [0.5, 0.75, 0.9, 0.95, 0.99]

    Example:
        >>> requests_time = Summary("http_requests", 'time')
        >>>
        >>> @requests_time.timeit()
        >>> def http_request():
        >>>     ...
        >>>
        >>> import psutil
        >>> ram_usage = Summary("http_request", 'time')
        >>> ram_usage.observe(psutil.virtual_memory().used)
    """

    def __init__(self, metric_id, measurement_unit, quantiles=None, *args, **kwargs):
        super().__init__(metric_id, measurement_unit, quantiles=quantiles, *args, **kwargs)
        self.values = []
        self.quantiles = quantiles if quantiles else DEFAULT_SUMMARY_QUANTILES

    def observe(self, value):
        """Observe one value.

        Args:
            value: integer or float with the value to observe.
        """
        assert isinstance(value, int) or isinstance(value, float), "Summary values should be int or floats"
        self.values.append(value)

    def timeit(self):
        """Allows the Summary to work as a Timer. The timer can work as a decorator or as a context manager."""
        return Timer(lambda time: self.observe(time))

    def _collect_metrics(self):
        timestamp = self.timestamp
        collected_values = []
        sorted_values = sorted(self.values)

        collected_values += self._get_metric_sum(timestamp, sorted_values)
        collected_values += self._get_metric_count(timestamp, sorted_values)

        for quantile in self.quantiles:
            collected_values += self._get_quantile(timestamp, sorted_values, quantile)

        return collected_values

    def _reset(self):
        self.values = []

    def _get_metric_sum(self, timestamp, values):
        return [
            metric_factory(
                self.metric_id + "_sum",
                sum(values),
                self.measurement_unit,
                timestamp,
                empty=False if values else True,
                labels=self.labels,
            )
        ]

    def _get_metric_count(self, timestamp, values):
        return [
            metric_factory(
                self.metric_id + "_count",
                len(values),
                self.measurement_unit,
                timestamp,
                empty=False if values else True,
                labels=self.labels,
            )
        ]

    def _get_quantile(self, timestamp, values, quantile):
        try:
            return [
                metric_factory(
                    self.metric_id,
                    self._quantile(values, quantile),
                    self.measurement_unit,
                    timestamp,
                    empty=False if values else True,
                    labels={**self.labels, "quantile": quantile},
                )
            ]
        except IndexError:
            return []

    @staticmethod
    def _quantile(data, percentile):
        """Find the percentile of a list of values.

        Args:
            data: A list of values.  N must be sorted.
            percentile: A float value from 0.0 to 1.0.
        Returns:
            The percentile of the values.
        """
        if len(data):
            n = int(round(percentile * len(data)))
            return data[n - 1]
