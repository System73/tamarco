import asyncio
import logging
import os
from concurrent.futures._base import CancelledError, TimeoutError
from typing import NewType, TypeVar

import aio_etcd
import ujson
from etcd import EtcdNotDir, EtcdResult

from tamarco.core.settings.backends.interface import SettingsInterface, _EmptyArg
from tamarco.core.settings.utils import format_key_to_etcd, parse_dir_response

Key = NewType("Key", str)
Value = TypeVar("Value", str, int, float)

logger = logging.getLogger("tamarco.settings")

WATCHER_ERROR_WAIT_TIME = 5


class EtcdSettingsBackend(SettingsInterface):
    """Class to handle settings that are in a etcd service."""

    @staticmethod
    def _format_response_key(response_key):
        key = response_key.replace("/", ".")
        if key.startswith("."):
            key = key[1:]
        return key

    def __init__(self, etcd_config, loop=None):
        self.watch_tasks = []
        self.client = aio_etcd.Client(**etcd_config, loop=loop)

    async def check_etcd_health(self):
        """Check if a key specified in the enviroment variable ETCD_CHECK_KEY exists.
        It is to ensure that the etcd is correctly configured before starting to read them.
        The configuration script of etcd should write the ETCD_CHECK_KEY when all the parameters are correctly
        configured.

        Raises:
            KeyError: If the etcd key is not created in 4 seconds.
        """
        if "ETCD_CHECK_KEY" in os.environ:
            print(f"Checking if ETCD_CHECK_KEY={os.environ['ETCD_CHECK_KEY']} exists in Etcd.")
            for _ in range(4):
                try:
                    await self.get(f"{os.environ['ETCD_CHECK_KEY']}")
                except KeyError:
                    await asyncio.sleep(1)
                else:
                    return
            raise KeyError

    async def get(self, key, default=_EmptyArg):
        """Return the setting value.

        Args:
            key (str): Path to the setting.
            default: Default value to return if the key does not exist.

        Returns:
            Setting value.
        """
        try:
            response = await self.client.read(key=format_key_to_etcd(key), recursive=True)
        except aio_etcd.EtcdKeyNotFound:
            logger.debug(f"Could not found the key {key} in ETCD")
            if default != _EmptyArg:
                return default
            else:
                raise KeyError
        except Exception:
            logger.warning(f"Error retrieving key {key} from ETCD", exc_info=True)
            raise

        logger.debug(f"Got setting {key} from ETCD with response: {response}")

        if response.dir:
            return parse_dir_response(response, key)
        else:
            return ujson.loads(response.value)

    async def set(self, key, value, ttl=None):  # noqa: A003
        """Set the setting value.

        Args:
            key (str): Path to the setting.
            value: Setting value to set.
        """
        if isinstance(value, dict):
            try:
                await self.mkdir(key)
            except EtcdNotDir:
                logger.warning(f"Exception creating the ETCD directory {key}. It is not a directory")
            return await self.recursive_set(key, value)
        else:
            logger.debug(f"Adding the key {key} with value: {value}")
            value = ujson.dumps(value)
            await self.client.write(key=format_key_to_etcd(key), value=value, ttl=ttl, append=False)

    async def recursive_set(self, base_key, conf_dict):
        """Set a directory recursively in a certain path.

        Args:
            base_key: Path where to write the settings.
            conf_dict: Settings to update.
        """
        base_key += "/" if base_key != "" else ""
        for key, value in conf_dict.items():
            key = base_key + key
            if isinstance(value, dict):
                try:
                    await self.mkdir(key)
                except EtcdNotDir:
                    logger.warning(f"Exception creating the ETCD directory {key}. It is not a directory")
                await self.recursive_set(key, value)
            else:
                await self.set(key, value)

    async def mkdir(self, key):
        """Create a etcd directory.

        Args:
            key (str): Path to the directory to create.
        """
        logger.info(f"Adding to ETCD the folder: {key}")
        await self.client.write(key=key, value=None, dir=True)

    async def delete(self, key) -> EtcdResult:
        """Delete a setting.

        Args:
            key (str): Path to the setting.
        """
        try:
            result = await self.client.delete(key=format_key_to_etcd(key), recursive=True)
        except Exception:
            logger.warning(f"Could not delete from ETCD the key: {key}", exc_info=True)
            raise KeyError
        else:
            logger.info(f"Deleted from ETCD the key: {key}")
            return result

    async def watch_callback(self, response, key, callback):
        """Intermediary callback to parse the etcd response.

        Args:
            response: Etcd response to be parsed.
            key (str): Setting to watch.
            callback: Callback function to execute.
        """
        if response.action == "delete":
            setting = None
        elif response.dir:
            setting = parse_dir_response(response, key)
        else:
            setting = ujson.loads(response.value)
        logger.info(f"ETCD watcher: change in setting {key}. New value: {setting}. Triggering callback")
        await callback(key, setting)

    async def watch(self, key, callback):
        """Create a hook in the key to trigger the callback when a setting is changed.

        Args:
            key (str): Path to the setting.
            callback: Callback to call when the value of the key change.
        """

        async def watch_task():
            """Watch task executed once per key to watch."""
            logger.info(f"Creating the task to watch the ETCD key: {key}")
            formatted_key = format_key_to_etcd(key)
            while True:
                try:
                    response = await self.client.watch(formatted_key, recursive=True)
                    if not hasattr(response, "_prev_node") or (response.value != response._prev_node.value):
                        formatted_response_key = self._format_response_key(response.key)
                        await self.watch_callback(response, formatted_response_key, callback)
                except TimeoutError:
                    # ETCD v2 issue with socket Timeout in watcher. v3 will solve the problem.
                    logger.warning(f"Socket timeout reached, re-watching the ETCD key: {key}")
                except CancelledError:
                    logger.warning(f"ETCD watcher for the key {key} has been cancelled")
                    return
                except Exception:
                    logger.warning(
                        f"Error watching the key {key}. Waiting {WATCHER_ERROR_WAIT_TIME} seconds before "
                        f"retrying. (Changes during this time won't trigger the callbacks!)",
                        exc_info=True,
                    )
                    await asyncio.sleep(WATCHER_ERROR_WAIT_TIME)
                await asyncio.sleep(0.1)

        self.watch_tasks.append(asyncio.ensure_future(watch_task()))

    def cancel_watch_tasks(self):
        """Remove all the watchers from the settings to close the coroutines properly."""
        for task in self.watch_tasks:
            if not task.done():
                try:
                    print(f"Cancelling this task -> {task}")
                    task.cancel()
                except Exception:
                    raise

    def __del__(self):
        """When the setting object is deleted cancels all the watch tasks."""
        self.cancel_watch_tasks()
        self.close()

    async def _check_servers(self):
        machines = await self.client.machines()
        assert machines
        return machines

    def close(self):
        """Close the connections."""
        self.client.close()
