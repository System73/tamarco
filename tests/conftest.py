import asyncio
import functools
import logging
import os

import pytest
import yaml

from tamarco.core.patterns import Singleton

ETCD_CONFIGURATION = {"host": "127.0.0.1", "port": 2379}
SETTINGS_FILE_PATH = "tests/custom_settings/settings.yml"


@pytest.fixture
def tests_root_path():
    return os.path.split(os.path.abspath(__file__))[0]


@pytest.fixture
def project_root_path(tests_root_path):
    return os.path.split(tests_root_path)[0]


@pytest.fixture
def inject_in_env_settings_file_path():
    os.environ["TAMARCO_YML_FILE"] = SETTINGS_FILE_PATH
    yield
    os.environ["TAMARCO_YML_FILE"] = ""


@pytest.fixture
def add_logging():
    logger = logging.getLogger("s73_logging")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    yield
    logger.handlers = []


@pytest.fixture
def settings():
    return get_settings_from_yaml_file(SETTINGS_FILE_PATH)


def get_settings_from_yaml_file(settings_path: str):
    with open(settings_path, "r") as stream:
        yaml_file = yaml.full_load(stream)
    return yaml_file


def clear_singleton_instance(instance_name):
    for instance in Singleton._instances.copy():
        try:
            if instance.name == instance_name:
                del Singleton._instances[instance]
        except Exception:
            pass


def decorator_async(func):
    @functools.wraps(func)
    def wrap_func(*args, **kwargs):
        async def b():
            return func(*args, **kwargs)

        return asyncio.get_event_loop().run_until_complete(b())

    return wrap_func
