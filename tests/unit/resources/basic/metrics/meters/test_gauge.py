import asyncio
import time

import pytest

from tamarco.resources.basic.metrics.meters.gauge import Gauge


def test_gauge():
    gauge = Gauge("test_gauge", "requests")

    gauge.inc()
    assert gauge.value == 1
    gauge.dec()
    assert gauge.value == 0

    gauge.inc(2)
    assert gauge.value == 2
    gauge.dec(2)
    assert gauge.value == 0

    gauge.set(15.5)
    assert gauge.value == 15.5

    gauge.set_to_current_time()
    assert time.time() - gauge.value < 0.01


def test_gauge_invalid_values():
    gauge = Gauge("test_gauge_invalid_values", "requests")

    with pytest.raises(AssertionError):
        gauge.inc("invalid value")

    with pytest.raises(AssertionError):
        gauge.dec("invalid value")

    with pytest.raises(AssertionError):
        gauge.set("invalid value")


def test_gauge_timeit():
    gauge = Gauge("test_gauge_timeit", "function_calls")

    @gauge.timeit()
    def count_time():
        time.sleep(0.01)

    count_time()
    assert 0.0075 < gauge.value < 0.030


@pytest.mark.asyncio
async def test_gauge_async_timeit():
    gauge = Gauge("test_gauge_async_timeit", "function_calls")

    @gauge.timeit()
    async def count_time():
        await asyncio.sleep(0.01)

    await count_time()

    assert 0.0075 < gauge.value < 0.012


@pytest.mark.asyncio
async def test_gauge_new_labels():
    gauge = Gauge("test.gauge.new_labels", "test", labels={1: 1})
    gauge_new_label = gauge.new_labels({2: 2})
    assert 1 in gauge.labels and 2 not in gauge.labels
    assert 2 in gauge_new_label.labels and 2 in gauge_new_label.labels
