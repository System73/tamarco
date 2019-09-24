import asyncio
import uuid
from unittest.mock import MagicMock

import pytest

from tamarco.resources.basic.registry.resource import Registry
from tamarco.resources.basic.registry.settings import ETCD_REGISTRY_TTL_SECONDS
from tests.utils import AsyncMock


@pytest.fixture
def instance_id():
    return uuid.uuid4()


@pytest.fixture
def registry(instance_id):
    microservice = MagicMock()
    microservice.instance_id = instance_id
    microservice.name = "test_registry"
    registry = Registry()
    registry.microservice = microservice
    return registry


@pytest.mark.asyncio
async def test_registry_post_stop(registry, event_loop):
    registry.register_task = asyncio.ensure_future(asyncio.Future(), loop=event_loop)
    await registry.post_stop()


@pytest.mark.asyncio
async def test_register_in_etcd(registry):
    registry.etcd_client = AsyncMock()
    registry.etcd_client.set = AsyncMock()
    await registry.register_in_etcd("key")
    registry.etcd_client.set.assert_called_once_with(key="key", value=registry.own_ip, ttl=ETCD_REGISTRY_TTL_SECONDS)


def test_get_register_key(registry, instance_id):
    assert registry.get_register_key("test") == f"test/test_registry/{instance_id}"
