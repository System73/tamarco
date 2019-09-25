import asyncio

import pytest

from tamarco.resources.basic.metrics.meters import Counter


class MyException(Exception):
    pass


@pytest.mark.asyncio
async def test_counter():
    counter = Counter("test.count", "request/s")
    assert counter.counter == 0
    counter.inc()
    assert counter.counter == 1

    @Counter("test.count", "request/s")
    def count_a_request():
        pass

    count_a_request()
    assert counter.counter == 2

    @Counter("test.count", "request/s")
    async def count_a_async_request():
        pass

    assert asyncio.iscoroutinefunction(count_a_async_request)
    assert count_a_async_request.__name__ == "count_a_async_request"

    await count_a_async_request()
    assert counter.counter == 3

    collected_data = counter._collect_metrics()[0]

    assert collected_data.id == counter.metric_id
    assert counter.metric_type == "counter"
    assert collected_data.units == counter.measurement_unit


def test_counter_invalid_value():
    counter = Counter("test.count.invalid_value", "request/s")

    with pytest.raises(AssertionError):
        counter.inc(-0.1)


@pytest.mark.asyncio
async def test_exception_counter_decorator():
    ex_counter = Counter("test.exceptions.count", "exception/s")
    assert ex_counter.counter == 0
    ex_counter.inc()
    assert ex_counter.counter == 1

    @ex_counter.count_exceptions()
    def exception_count():
        raise MyException

    with pytest.raises(MyException):
        exception_count()

    assert ex_counter.counter == 2

    @ex_counter.count_exceptions()
    def async_exception_count():
        raise MyException

    with pytest.raises(MyException):
        await async_exception_count()

    assert ex_counter.counter == 3

    collected_data = ex_counter._collect_metrics()[0]
    assert collected_data.id == ex_counter.metric_id
    assert ex_counter.metric_type == "counter"
    assert collected_data.units == ex_counter.measurement_unit


@pytest.mark.asyncio
async def test_exception_counter_context_manager():
    ex_counter = Counter("test.exceptions.context_manager", "exception/s")
    assert ex_counter.current_value() == 0

    with pytest.raises(MyException):
        with ex_counter.count_exceptions():
            raise MyException("testing exception")

    assert ex_counter.current_value() == 1

    with ex_counter.count_exceptions():
        pass

    assert ex_counter.current_value() == 1


@pytest.mark.asyncio
async def test_counter_new_labels():
    counter = Counter("test.counter.new_labels", "test", labels={1: 1})
    counter_new_label = counter.new_labels({2: 2})
    assert 1 in counter.labels and 2 not in counter.labels
    assert 2 in counter_new_label.labels and 2 in counter_new_label.labels
