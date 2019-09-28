import asyncio
import logging
import socket

import aio_etcd

from tamarco.core.patterns import Singleton
from tamarco.core.utils import get_etcd_configuration_from_environment_variables
from tamarco.resources.bases import BaseResource
from tamarco.resources.basic.status.status_codes import StatusCodes
from .settings import ETCD_DEFAULT_REGISTRY_PATH, ETCD_REGISTRY_PERIOD_SECONDS, ETCD_REGISTRY_TTL_SECONDS


class Registry(BaseResource, metaclass=Singleton):
    """Class that registers the instance of the microservice in etcd.
    This functionality is thought to have auto discovery of microservices using etcd.
    """

    loggers_names = ["tamarco.registry"]

    def __init__(self, *args, **kwargs):
        self.etcd_config = get_etcd_configuration_from_environment_variables()
        self.etcd_client = None
        self.register_task = None
        self.logger = logging.getLogger("tamarco.registry")
        self.own_ip = self._get_own_ip()
        super().__init__(*args, **kwargs)

    def _get_own_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            self.logger.exception("Could not determine the IP to expose in the registry resource")
            return "Unknown"

    async def post_start(self):
        enabled_setting = await self.settings.get("enabled", False)
        if enabled_setting:
            self.logger.info("Registry resource enabled")
            await self.connect_to_etcd()
            self.register_task = asyncio.ensure_future(self.register_coroutine(), loop=self.microservice.loop)
        else:
            self.logger.info("Registry resource disabled")

    async def connect_to_etcd(self):
        self.etcd_client = aio_etcd.Client(**self.etcd_config, loop=self.microservice.loop)

    async def register_coroutine(self):
        try:
            register_path = await self.settings.get("path", ETCD_DEFAULT_REGISTRY_PATH)
            register_key = self.get_register_key(register_path)
            while True:
                await self.register_in_etcd(register_key)
                await asyncio.sleep(ETCD_REGISTRY_PERIOD_SECONDS)
        except Exception:
            self.logger.critical(
                "Unexpected exception registering the coroutine. Reporting failed status", exc_info=True
            )
            self._status = StatusCodes.FAILED

    def get_register_key(self, register_path):
        return f"{register_path}.{self.microservice.name}.{self.microservice.instance_id}".replace(".", "/")

    async def register_in_etcd(self, register_key):
        try:
            await self.etcd_client.set(key=register_key, value=self.own_ip, ttl=ETCD_REGISTRY_TTL_SECONDS)
        except Exception:
            self.logger.warning("Unexpected exception registering instance in ETCD", exc_info=True)

    async def stop(self):
        self.logger.info(f"Stopping Registry resource: {self.name}")
        await super().stop()

    async def post_stop(self):
        if self.register_task is not None:
            self.register_task.cancel()
