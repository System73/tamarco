import os

import pytest

from tamarco.core.settings.backends import EtcdSettingsBackend
from tests.conftest import ETCD_CONFIGURATION
from tests.conftest import get_settings_from_yaml_file

TEST_PATH = os.path.realpath(os.path.dirname(__file__))

settings_backends = [(EtcdSettingsBackend, [ETCD_CONFIGURATION])]


@pytest.fixture
def loaded_test_settings(event_loop):
    yaml_settings = get_settings_from_yaml_file(os.path.join(TEST_PATH, "files/settings.yaml"))

    settings = EtcdSettingsBackend({"host": "127.0.0.1", "port": 2379})

    async def set_settings():
        for key, value in yaml_settings.items():
            try:
                await settings.set(key, value)
            except Exception:
                # Exception configuring yaml in etcd: {yaml_settings}
                pass

    event_loop.run_until_complete(set_settings())
    return settings
