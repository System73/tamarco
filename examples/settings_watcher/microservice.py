# How to execute this example: see the "Examples" section in README.md

import asyncio

from tamarco.core.microservice import Microservice, task
from tamarco.core.settings.backends import EtcdSettingsBackend
from tamarco.core.settings.settings import Key, Settings


class WatcherMicroservice(Microservice):
    name = "watcher_example"
    extra_loggers_names = {name, "asyncio", "tamarco"}
    etcd_settings = EtcdSettingsBackend(etcd_config={"host": "127.0.0.1"})

    def __init__(self):
        super().__init__()
        self.settings.update_internal({"system": {"deploy_name": "test", "logging": {"profile": "PRODUCTION"}}})
        # Settings class configuration just to simplify the example. DON'T DO IT!
        settings = Settings()
        settings.etcd_external = True
        settings.external_backend = self.etcd_settings

    async def watcher_callback(self, key, settings):
        self.logger.info(f"Watcher callback called for the key {key} with new value: {settings}")

    @task
    async def change_settings(self):
        await self.etcd_settings.set(Key("system.foo.cow"), "MOOOO")
        try:
            await self.settings.watch("system.foo.cow", self.watcher_callback)
        except Exception:
            self.logger.exception("Could not create the watcher")

        i = 1
        while True:
            await asyncio.sleep(1)
            self.logger.info(f"Changing system.foo.cow with value MOOOO_{i}")
            await self.etcd_settings.set(Key("system.foo.cow"), f"MOOOO_{i}")
            i += 1


def main():
    ms = WatcherMicroservice()
    ms.run()


if __name__ == "__main__":
    main()
