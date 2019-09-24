import pytest
from sanic.response import HTTPResponse

from tamarco.resources.basic.metrics.meters.counter import HTTPCounter, HTTPCounterHeaderMap, HeaderToLabel


@pytest.mark.asyncio
async def test_http_counter():
    http_counter = HTTPCounter("viewers")

    @http_counter
    async def endpoint_handler(request=None):
        return HTTPResponse(status=500)

    assert http_counter.exception_counter.current_value() == 0

    await endpoint_handler()

    assert http_counter.current_value() == 1
    assert (
        (id(http_counter) != id(http_counter.errors_counter))
        and (id(http_counter) != id(http_counter.exception_counter))
        and (id(http_counter.errors_counter) != id(http_counter.exception_counter))
    )
    assert http_counter.errors_counter.current_value() == 1
    assert http_counter.exception_counter.current_value() == 0

    @http_counter
    async def endpoint_handler(request=None):
        raise Exception()

    with pytest.raises(Exception):
        await endpoint_handler()

    assert http_counter.current_value() == 2
    assert http_counter.errors_counter.current_value() == 1
    assert http_counter.errors_counter.current_value() == 1


@pytest.mark.asyncio
async def test_http_counter_header_map():
    header_map = HeaderToLabel(
        header="my_header", label="my_header_label", default_header_value="my_header_default_value"
    )
    http_counter = HTTPCounterHeaderMap("viewers", header_to_label_maps=[header_map])

    class Request:
        headers = {"my_header": "my_header_value"}
        path = "/my_header_test/meow"
        method = "PUT"

    prometheus_labels = {
        "my_header_label": "my_header_value",
        "status_code": 500,
        "path": Request.path,
        "method": Request.method,
    }

    @http_counter
    async def endpoint_handler(request=None):
        return HTTPResponse(status=500)

    await endpoint_handler(Request)

    assert http_counter.new_labels(prometheus_labels).current_value() == 1
    assert (
        (id(http_counter) != id(http_counter.new_labels(prometheus_labels).errors_counter))
        and (id(http_counter) != id(http_counter.new_labels(prometheus_labels).exception_counter))
        and (id(http_counter.errors_counter) != id(http_counter.exception_counter))
    )
    assert http_counter.exception_counter.new_labels(prometheus_labels).current_value() == 0

    @http_counter
    async def endpoint_handler(request=None):
        raise Exception()

    with pytest.raises(Exception):
        await endpoint_handler(Request)

    prometheus_labels.pop("status_code")
    assert http_counter.exception_counter.new_labels(prometheus_labels).current_value() == 1
