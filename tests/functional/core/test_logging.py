import asyncio

import pytest
import redis
import ujson

from tamarco.core.logging.logging import Logging
from tamarco.core.settings.settings import Settings, SettingsView
from tamarco.core.utils import ROOT_SETTINGS


@pytest.mark.asyncio
async def test_logging_elastic_search(event_loop):
    settings = SettingsView(Settings(), f"{ROOT_SETTINGS}.logging")
    loggings = Logging()
    await settings.set("redis.port", 7006)
    await settings.set("redis.host", "127.0.0.1")
    await settings.set("profile", "DEVELOP")
    await settings.set(f"{ROOT_SETTINGS}.deploy_name", "functional_logstash", raw=True)
    loggings.configure_settings(settings)
    await asyncio.sleep(5.0)
    await loggings.start(
        ["test_funcional_logstash_logging"], "test_functional_logstash", "test_deploy_name", loop=event_loop
    )
    r = redis.StrictRedis(host="127.0.0.1", port=7006)
    await asyncio.sleep(5.0)
    messages = []
    messages_check = []

    for _ in range(20):
        msg = f"Hello world {_}"
        messages.append(msg)

    q = r.rpop("logstash")
    while q is not None:
        messages_check.append(ujson.loads(q.decode())["@message"])
        q = r.rpop("logstash")

    assert 0 <= len(messages_check)
