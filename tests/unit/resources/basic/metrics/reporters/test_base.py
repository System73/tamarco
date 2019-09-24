from tamarco.resources.basic.metrics.reporters.base import CarbonBaseHandler


def test_base_handler_creation_no_metric_prefix():
    base_handler = CarbonBaseHandler()
    assert base_handler.metric_prefix == ""


def test_base_handler_creation_metric_prefix():
    base_handler = CarbonBaseHandler("test")
    assert base_handler.metric_prefix == "test."


def test_carbon_base_format(sample_meters):
    base_handler = CarbonBaseHandler("test")

    metrics_str = base_handler.format_metrics(meters=sample_meters)
    check_metric_str(metrics_str)


def check_metric_str(metrics_str):
    metrics_by_line = metrics_str.split("\n")[:-1]
    assert all(len(metric.split(" ")) == 3 for metric in metrics_by_line)

    metrics_names = [metric.split(" ")[0] for metric in metrics_by_line]
    assert all("test" in name for name in metrics_names)
    assert all("__" in name for name in metrics_names)
    assert "cat_counter" in metrics_names[0]
    assert "cat_weight" in metrics_names[1]
    assert all("meow_time" in name for name in metrics_names[2:])

    metrics_values = [metric.split(" ")[1] for metric in metrics_by_line]
    metrics_timestamp = [metric.split(" ")[2] for metric in metrics_by_line]
    assert [float(value) for value in metrics_values]
    assert [float(timestamp) for timestamp in metrics_timestamp]
