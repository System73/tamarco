import asyncio

import pytest

from tamarco.resources.basic.metrics.meters import Summary
from tamarco.resources.basic.metrics.meters.summary import DEFAULT_SUMMARY_QUANTILES


def test_summary():
    meow_summary = Summary("meow_time", "cats")

    [meow_summary.observe(n) for n in range(100)]

    assert all(n in meow_summary.values for n in range(100))

    metrics = meow_summary._collect_metrics()

    assert len(metrics) == 7

    assert metrics[0].id == "meow_time_sum"
    assert metrics[0].value == sum(range(100))

    assert metrics[1].id == "meow_time_count"
    assert metrics[1].value == 100

    for quantile_metric, quantile in zip(metrics[2:], DEFAULT_SUMMARY_QUANTILES):
        assert quantile_metric.id == "meow_time"
        assert quantile_metric.labels.pop("quantile") == quantile
        assert quantile_metric.value == round(quantile * 100) - 1


def test_summary_invalid_values():
    meow_summary = Summary("meow_time", "cats")

    with pytest.raises(AssertionError):
        meow_summary.observe("invalid_value")


@pytest.mark.asyncio
async def test_summary_timeit_values(event_loop):
    meow_time_summary = Summary("meow_timeit_values", "cats")

    @meow_time_summary.timeit()
    async def meow():
        await asyncio.sleep(0.01)

    # opening 100 concurrent meows()
    futures = [asyncio.ensure_future(meow(), loop=event_loop) for _ in range(10)]
    # waiting for the 100 futures to complete
    await asyncio.wait(fs=futures, loop=event_loop, timeout=1)

    metrics = meow_time_summary._collect_metrics()

    # The time have less than a 10% of error
    assert 0.007 * 10 < metrics[0].value < 0.013 * 10
    assert metrics[1].value == 10
    assert 0.007 < metrics[2].value < 0.013
    assert len(metrics) == 2 + len(DEFAULT_SUMMARY_QUANTILES)


@pytest.mark.asyncio
async def test_summary_new_labels():
    summary = Summary("test.summary.new_labels", "test", labels={1: 1})
    summary_new_label = summary.new_labels({2: 2})
    assert 1 in summary.labels and 2 not in summary.labels
    assert 2 in summary_new_label.labels and 2 in summary_new_label.labels
