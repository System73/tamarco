import asyncio
import time

import pytest

from tamarco.core.patterns import Flyweight, FlyweightWithLabels
from tamarco.resources.basic.metrics.meters.base import Timer


def test_flyweight():
    class Cat(metaclass=Flyweight):
        def __init__(self, name):
            self.name = name

    garfield_1 = Cat("Garfield")
    garfield_2 = Cat("Garfield")
    doraemon = Cat("Doraemon")

    assert garfield_1 == garfield_2
    assert garfield_1 != doraemon and garfield_2 != doraemon
    assert hasattr(Cat, "_Flyweight__instances")
    assert "Garfield" in Cat._Flyweight__instances


def test_extended_flyweight():
    # Behavior of flyweight
    class Cat(metaclass=FlyweightWithLabels):
        def __init__(self, name):
            self.name = name

    garfield_1 = Cat("Garfield")
    garfield_2 = Cat("Garfield")
    doraemon = Cat("Doraemon")

    assert garfield_1 == garfield_2
    assert garfield_1 != doraemon and garfield_2 != doraemon
    assert hasattr(Cat, "_Flyweight__instances")
    assert "Garfield" in Cat._Flyweight__instances

    class Animal(metaclass=FlyweightWithLabels):
        def __init__(self, name, labels=None):
            self.name = name

    # Behavior of the extended flyweight
    cat = Animal("cat")
    dog = Animal("dog")
    cat_garfield_1 = Animal("cat", labels={"name": "garfield"})
    cat_garfield_2 = Animal("cat", labels={"name": "garfield"})
    dog_garfield = Animal("dog", labels={"name": "garfield"})
    cat_doraemon = Animal("cat", labels={"name": "doraemon"})

    assert cat != dog
    assert cat_garfield_1 == cat_garfield_2
    assert cat_garfield_1 != cat_doraemon and cat_garfield_2 != cat_doraemon
    assert dog_garfield != cat_garfield_1 and dog_garfield != cat_garfield_2

    # Test more than one labels
    cat_garfield_sleep = Animal("cat", labels={"name": "garfield", "power": "sleep"})
    cat_garfield = Animal("cat", labels={"name": "garfield"})
    cat_garfield_sleep_same_instance = Animal("cat", labels={"name": "garfield", "power": "sleep"})

    assert cat_garfield_sleep != cat_garfield
    assert cat_garfield_sleep == cat_garfield_sleep_same_instance


def test_timer_context_manager():
    timer_value = []
    timer = Timer(lambda time: timer_value.append(time))
    with timer:
        time.sleep(0.01)
    assert 0.0075 < timer_value.pop() < 0.1


def test_timer_decorator():
    timer_value = []

    @Timer(lambda time: timer_value.append(time))
    def time_me():
        time.sleep(0.01)

    time_me()
    assert 0.0075 < timer_value.pop() < 0.012


@pytest.mark.asyncio
async def test_timer_async_decorator():
    timer_value = []

    @Timer(lambda time: timer_value.append(time))
    async def time_me():
        await asyncio.sleep(0.01)

    await time_me()
    assert 0.0075 < timer_value.pop() < 0.012
