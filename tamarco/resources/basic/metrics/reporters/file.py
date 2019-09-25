from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler
from tamarco.resources.basic.metrics.settings import DEFAULT_FILE_PATH


class FileHandler(CarbonBaseHandler):
    """Handler for the applications metrics that store them in a file."""

    def __init__(self, file_path=DEFAULT_FILE_PATH, metric_prefix=None):
        """Initialize the File handler.

        Args:
            file_path (str): File path.
            metric_prefix (str): Concatenated prefix in all metrics.
        """
        super().__init__(metric_prefix)
        self.file = open(file_path, "a")

    def __del__(self):
        """Close the file when the handler is deleted."""
        if self.file:
            self.file.close()

    def write(self, meters):
        """Build the metrics report from all meters.

        Args:
            meters (list): List of meters from which the metrics will be obtained.
        """
        metrics_str = self.format_metrics(meters)
        self.file.write(metrics_str)
