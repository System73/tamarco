import aio_etcd
import pytest

from tamarco.resources.basic.registry.resource import Registry
from tests.conftest import ETCD_CONFIGURATION


@pytest.fixture
def etcd_client(event_loop):
    return aio_etcd.Client(**ETCD_CONFIGURATION, loop=event_loop)


@pytest.mark.asyncio
async def test_register_in_etcd(etcd_client):
    registry = Registry()
    registry.etcd_client = etcd_client
    await registry.register_in_etcd("test_registry")
    get = await etcd_client.get("test_registry")
    assert get.value == registry.own_ip
