import glob
import os
from collections import UserDict

import pytest

from tamarco.resources.debug.profiler import ProfilerResource


class AsyncDict(UserDict):
    async def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class Microservice:
    name = "test_profiler"
    loop = None


@pytest.fixture
def profiler_file_path():
    return "/tmp/test_profiler_profile"


def remove_file(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def clean_fixture_file(profiler_file_path):
    remove_file(profiler_file_path)
    yield
    remove_file(profiler_file_path)


@pytest.mark.asyncio
async def test_is_profiler_enabled():
    profiler_resource = ProfilerResource()
    profiler_resource.microservice = Microservice

    settings = AsyncDict(microservices_with_profiler=[])
    profiler_resource.settings = settings
    assert not await profiler_resource.is_profiler_enabled()

    settings = AsyncDict(microservices_with_profiler=["test_profiler"])
    profiler_resource.settings = settings
    assert await profiler_resource.is_profiler_enabled()


@pytest.mark.asyncio
async def test_start_and_stop(event_loop):
    profiler_resource = ProfilerResource()
    profiler_resource.microservice = Microservice
    profiler_resource.microservice.loop = event_loop
    settings = AsyncDict(microservices_with_profiler=["test_profiler"])
    profiler_resource.settings = settings

    assert not profiler_resource.profiler
    assert not profiler_resource.cpu_watcher_task

    await profiler_resource.start()

    assert profiler_resource.profiler
    assert profiler_resource.cpu_watcher_task
    assert not profiler_resource.cpu_watcher_task.cancelled()

    await profiler_resource.stop()

    assert not profiler_resource.profiler
    assert profiler_resource.cpu_watcher_task._must_cancel


@pytest.mark.asyncio
async def test_save_profile_snapshot_to_file(event_loop, profiler_file_path, clean_fixture_file):
    profiler_resource = ProfilerResource()
    profiler_resource.profiler_file_path = profiler_file_path
    assert not glob.glob(profiler_file_path)

    profiler_resource._initialize_profiler()
    profiler_resource.save_profile_snapshot_to_file()

    assert glob.glob(profiler_file_path)
