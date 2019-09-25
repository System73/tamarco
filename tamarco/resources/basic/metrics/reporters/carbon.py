import logging
import socket

from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler
from tamarco.resources.basic.metrics.settings import DEFAULT_CARBON_HOST, DEFAULT_CARBON_PORT

logger = logging.getLogger("tamarco.metrics")


class CarbonHandler(CarbonBaseHandler):
    """Handler for the applications metrics that sends them to a Graphite Carbon service."""

    def __init__(self, host=DEFAULT_CARBON_HOST, port=DEFAULT_CARBON_PORT, metric_prefix=None):
        """Initialize the Carbon handler.

        Args:
            host (str): Carbon host address.
            port (int): Carbon port number.
            metric_prefix (str): Concatenated prefix in all metrics.
        """
        super().__init__(metric_prefix)
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def write(self, meters):
        """Build the metrics report from all meters.

        Args:
            meters (list): List of meters from which the metrics will be obtained.
        """
        metrics_str = self.format_metrics(meters)
        metrics_bytes = metrics_str.encode("utf-8")
        try:  # IMPROVEME, reconnection and error handling in socket
            self.socket.send(metrics_bytes)
        except (socket.timeout, socket.error):
            try:
                self.socket.connect((self.host, self.port))
                self.socket.send(metrics_bytes)
            except Exception:
                logger.exception("Unexpected exception sending metrics to carbon")
