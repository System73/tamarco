import asyncio

import pytest

from tamarco.core.settings.backends import EtcdSettingsBackend
from tests.functional.core.settings.conftest import settings_backends


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_get(settings_class, init_args, event_loop, loaded_test_settings):
    settings = settings_class(*init_args)
    redis_port = await settings.get("redis.port")
    assert redis_port == 7006

    redis_host = await settings.get("redis.host")
    assert redis_host == "127.0.0.1"

    redis_conf = await settings.get("redis")
    assert redis_conf["host"] == "127.0.0.1"

    elasticsearch = await settings.get("elasticsearch")
    assert len(elasticsearch) == 2
    assert all("127.0.0.1" in x for x in elasticsearch)

    not_a_key = await settings.get("not_a_key", default=99)
    assert not_a_key == 99


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_get_wrong_key(settings_class, init_args, event_loop):
    settings = settings_class(loop=event_loop, *init_args)
    with pytest.raises(KeyError):
        await settings.get("non_existing_key")


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_get_multiple_dict_level(settings_class, init_args, event_loop, loaded_test_settings):
    settings = settings_class(loop=event_loop, *init_args)

    signaler = await settings.get("signaler")

    assert signaler["redis"]["port"] == 7006


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_set(settings_class, init_args, event_loop, add_logging):
    settings = settings_class(loop=event_loop, *init_args)
    await settings.set("redis.port", 9999)
    assert (await settings.get("redis.port")) == 9999

    await settings.set("redis.host", "127.0.0.2")
    assert (await settings.get("redis.host")) == "127.0.0.2"

    await settings.set("logging.test.loggers", "StreamLogger")
    assert (await settings.get("logging.test.loggers")) == "StreamLogger"


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_delete(settings_class, init_args, event_loop, loaded_test_settings):
    settings = settings_class(loop=event_loop, *init_args)
    await settings.delete("redis.port")
    with pytest.raises(KeyError):
        await settings.get("redis.port")

    await settings.delete("elasticsearch")
    with pytest.raises(KeyError):
        await settings.get("elasticsearch")


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_watch_set(settings_class, init_args, event_loop):
    settings = settings_class(loop=event_loop, *init_args)

    fut = asyncio.Future()

    async def callback(key, value):
        fut.set_result((key, value))

    await settings.set("redis.port", 8888)
    await settings.watch("redis.port", callback)
    await asyncio.sleep(0.1)
    await settings.set("redis.port", 9999)
    key, value = await fut
    assert key == "redis.port"
    assert value == 9999


@pytest.mark.asyncio
@pytest.mark.parametrize("settings_class,init_args", settings_backends)
async def test_settings_watch_delete(settings_class, init_args, event_loop):
    settings = settings_class(loop=event_loop, *init_args)

    fut = asyncio.Future()

    async def callback(key, value):
        fut.set_result((key, value))

    await settings.watch("redis.port", callback)
    await asyncio.sleep(0.1)
    await settings.delete("redis.port")
    key, value = await fut
    assert key == "redis.port"
    assert value is None


@pytest.mark.asyncio
async def test_etcd_settings_check_machines():
    backend = EtcdSettingsBackend({"host": "127.0.0.1", "port": 2379})
    assert await backend._check_servers()
