from random import random

import pytest

from tamarco.resources.basic.metrics.meters import Counter, Gauge, Summary


@pytest.fixture
def sample_metrics():
    return [
        ("index.requests", 45, "requests", 126874812.0),
        ("main.requests", 60, "requests", 126874812.0),
        ("response.time", 12.64, "s", 126874812.0),
    ]


@pytest.fixture
def clean_flyweights():
    Counter._Flyweight__instances = {}
    Gauge._Flyweight__instances = {}
    Summary._Flyweight__instances = {}

    Counter._ExtendedFlyweight__instances = {}
    Gauge._ExtendedFlyweight__instances = {}
    Summary._ExtendedFlyweight__instances = {}


@pytest.fixture
def sample_meters(clean_flyweights):
    cat_counter = Counter("cat", "cats")
    cat_counter.value = 5

    cat_weight_gauge = Gauge("cat_weight", "kg")
    cat_weight_gauge.value = 2.785

    meow_time_summary_doraemon = Summary("meow_time", "seconds", labels={"name": "Doraemon"})
    meow_time_summary_doraemon.values = [random() for _ in range(100)]

    meow_time_summary_garfield = Summary("meow_time", "seconds", labels={"name": "Garfield"})
    meow_time_summary_garfield.values = [random() for _ in range(100)]

    return [cat_counter, cat_weight_gauge, meow_time_summary_doraemon, meow_time_summary_garfield]


@pytest.fixture
def sample_one_metric():
    return [("index.requests", 45, "requests", 126874812.0)]
