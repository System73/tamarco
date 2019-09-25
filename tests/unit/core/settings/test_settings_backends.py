import asyncio

import pytest

from tamarco.core.settings.backends.dictionary import DictSettingsBackend
from tamarco.core.settings.backends.file_based import JsonSettingsBackend, PythonSettingsBackend, YamlSettingsBackend


@pytest.mark.asyncio
async def test_dict_settings_backend(event_loop):
    backend = DictSettingsBackend(dict_settings={"setting1": "foo", "setting2": "bar", "setting3": {"setting4": 3}})
    backend.set_loop(event_loop)
    # Get
    assert await backend.get("setting1") == "foo"
    assert await backend.get("setting1", "bar") == "foo"
    assert await backend.get("setting3.setting4") == 3
    assert await backend.get("foo", 10) == 10
    with pytest.raises(KeyError):
        await backend.get("foo")

    # Set, delete
    await backend.set("setting5", "baz")
    assert await backend.get("setting5") == "baz"
    await backend.delete("setting5")
    with pytest.raises(KeyError):
        await backend.get("setting5")

    callback_called = asyncio.Future(loop=event_loop)

    # Watch
    async def callback(key, value):

        nonlocal callback_called
        callback_called.set_result("callback called")

    await backend.watch("setting1", callback)
    await backend.set("setting1", "foo2")
    assert await asyncio.wait_for(callback_called, 0.5, loop=event_loop) == "callback called"


@pytest.mark.asyncio
async def test_json_file_based_settings_backend(event_loop):
    backend = JsonSettingsBackend(file="./tests/unit/core/settings/example_settings.json", loop=event_loop)
    assert await backend.get("hello") == "world"
    assert await backend.get("cheap.is") == "dear"


@pytest.mark.asyncio
async def test_yaml_file_based_settings_backend(event_loop):
    backend = YamlSettingsBackend(file="./tests/unit/core/settings/example_settings.yaml", loop=event_loop)
    assert await backend.get("hello") == "world"
    assert await backend.get("cheap.is") == "dear"


@pytest.mark.asyncio
async def test_python_file_based_settings_backend(event_loop):
    backend = PythonSettingsBackend(file="./tests/unit/core/settings/example_settings.py", loop=event_loop)
    assert await backend.get("settings.hello") == "world"
    assert await backend.get("settings.cheap.is") == "dear"


@pytest.mark.asyncio
async def test_dictsettingsbackend_replace_dict_for_value():
    settings = DictSettingsBackend(dict_settings={"a": {"b": {"c": {"e": "f"}}}})

    await settings.set("a", "d")
    value = await settings.get("a")
    assert value == "d"


@pytest.mark.asyncio
async def test_dictsettingsbackend_replace_value_for_value():
    settings = DictSettingsBackend(dict_settings={"a": {"b": {"c": "d"}}})

    await settings.set("a.b.c", "e")
    value = await settings.get("a")
    assert value == {"b": {"c": "e"}}


@pytest.mark.asyncio
async def test_dictsettingsbackend_replace_value_for_dict():
    settings = DictSettingsBackend(dict_settings={"a": {"b": {"c": "d"}}})

    await settings.set("a.b.c", {"e": "f"})
    value = await settings.get("a")
    assert value == {"b": {"c": {"e": "f"}}}


@pytest.mark.asyncio
async def test_dictsettingsbackend_add_dict():
    settings = DictSettingsBackend(dict_settings={"a": "b"})

    await settings.set("a.b.e", "f")
    value = await settings.get("a")
    assert value == {"b": {"e": "f"}}


@pytest.mark.asyncio
async def test_dictsettingsbackend_add_dict_2():
    settings = DictSettingsBackend(dict_settings={"a": "b"})

    await settings.set("z", "f")
    value = await settings.get("a")
    assert value == "b"
    value = await settings.get("z")
    assert value == "f"
