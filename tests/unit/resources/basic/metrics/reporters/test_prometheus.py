from tamarco.resources.basic.metrics.reporters.prometheus import PrometheusHandler


def test_prometheus_handler_parse_labels():
    labels = {"protocol": "http", "method": "get"}
    parsed_labels = PrometheusHandler.parse_labels(labels)
    assert parsed_labels == '{protocol="http",method="get"}'


def test_prometheus_handler_parse_line():
    type_line = PrometheusHandler.parse_type_line("http_request_time", "counter")
    assert type_line == "# TYPE http_request_time counter\n"


def test_prometheus_handler_format_metrics(sample_meters):
    http_body = PrometheusHandler().format_metrics(sample_meters)
    assert http_body
