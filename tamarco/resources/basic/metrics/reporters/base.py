class CarbonBaseHandler:
    """Base handler for all the metrics handlers."""

    def __init__(self, metric_prefix=None):
        """Initialize the base handler.

        Args:
            metric_prefix (str): Prefix of all metrics.
        """
        if metric_prefix is None:
            self.metric_prefix = ""
        else:
            self.metric_prefix = metric_prefix + "."

    def format_metrics(self, meters):
        """Format available metrics from all `meters`.

        Args:
            meters (list): List of meters from which the metrics will be obtained.

        Returns:
            str: A text with a metric per line.
        """
        metrics_str = ""
        for meter in meters:
            metrics = meter._collect_metrics()
            for metric in metrics:
                parsed_labels = self.parse_label(metric.labels)
                metrics_str += (
                    f"{self.metric_prefix}{metric.id}_{meter.metric_type}_{parsed_labels}__{metric.units} "
                    f"{metric.value} {metric.timestamp}\n"
                )
        return metrics_str

    @staticmethod
    def parse_label(labels):
        """Format the labels metric and their values.

        Args:
            labels (list): List of metric labels.

        Returns:
            str: A string with all the labels and their values separated by dots.
        """
        labels_list = [f"{key}_{value}" for key, value in labels.items()]
        labels_str = ".".join(labels_list)
        return labels_str

    def write(self, metrics):
        """The function to override in the handlers for to build the metrics report.

        Args:
            metrics (list): List of meters from which the metrics will be obtained.
        """
        raise NotImplementedError
