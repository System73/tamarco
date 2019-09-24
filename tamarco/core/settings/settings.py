import logging
import os
from typing import NewType, TypeVar

from tamarco.core.patterns import Singleton
from tamarco.core.settings.backends import DictSettingsBackend, EtcdSettingsBackend, YamlSettingsBackend
from tamarco.core.settings.backends.interface import SettingsInterface, _EmptyArg, _Undefined
from tamarco.core.settings.utils import dict_deep_update
from tamarco.core.utils import get_etcd_configuration_from_environment_variables

UNDEFINED = _Undefined
logger = logging.getLogger("tamarco.settings")


class SettingsNotLoadedYet(Exception):
    pass


class SettingNotFound(Exception):
    def __init__(self, key):
        self.key = key


Key = NewType("Key", str)
Value = TypeVar("Value", str, int, float, dict)


def get_yml_file_from_enviroment_variable():
    tamarco_yml_file = os.environ.get("TAMARCO_YML_FILE", None)
    return tamarco_yml_file


class Settings(SettingsInterface, metaclass=Singleton):
    """Core settings class, here is the unique True of settings all the settings values are cached by this class in his
    internal_backend, all of the other settings are views of the data that this class holds.

    The external backend is where the settings should be originally loaded, the internal backend acts as cache
    to avoid making many requests to the external backend.
    """

    def __init__(self):
        super().__init__()
        self.promised_settings = {}
        self.internal_backend = DictSettingsBackend({})
        self.external_backend = None
        self.loop = None
        self.etcd_external = False

    def update_internal(self, dict_settings):
        """Update the internal cache with new settings.

        Args:
            dict_settings (dict): Settings to add to the internal backend.
        """
        dict_deep_update(self.internal_backend.settings, dict_settings)

    async def bind(self, loop):
        """Binds the settings to one event loop.

        Args:
            loop: Main asyncio event loop.
        """
        self.loop = loop

    async def start(self):
        """Start the settings.
        First loads the settings from the external settings backend (etcd or yaml file) once the internal and external
        settings backends are ready, the promised settings (when_loaded_settings) are resolved and the proxies start to
        holds the settings values.
        """
        self.internal_backend.set_loop(self.loop)
        await self._load_external_backend()
        await self._resolve_promised_settings()

    async def _load_external_backend(self):
        """Loads a external backend either etcd or yaml file in that order.
        To load it uses the environment variables TAMARCO_ETCD_HOST, TAMARCO_ETCD_PORT and TAMARCO_YAML_FILE.
        """
        yaml_file = get_yml_file_from_enviroment_variable()
        etcd_config = get_etcd_configuration_from_environment_variables()

        if etcd_config:
            self.external_backend = EtcdSettingsBackend(etcd_config=etcd_config, loop=self.loop)
            await self.external_backend.check_etcd_health()
            self.etcd_external = True
        elif yaml_file:
            self.external_backend = YamlSettingsBackend(file=yaml_file, loop=self.loop)
        else:
            logger.warning("Could not get any settings external backend from the environment")

    async def _resolve_promised_settings(self):
        """Set all the settings proxies with his correspondent values."""
        for key, proxies in self.promised_settings.items():
            try:
                setting_value = await self.get(key)
            except Exception:
                logger.warning(f"Error loading promised setting : {key}")
            else:
                for proxy in proxies:
                    object.__setattr__(proxy, "_obj", setting_value)

    def register_promised_setting(self, key, promised_setting):
        """Register a SettingProxy to be resolved when the settings are loaded.

        Args:
            key (str): setting key to register.
            promised_setting: setting proxy to register.
        """
        self.promised_settings[key].setdefault([]).append(promised_setting)

    async def get(self, key, default=_EmptyArg):
        """Get a setting value for a key.

        Args:
            key(str): Path to the setting.
            default: Default value in the case that it doesn't exists.

        Raises:
            SettingNotFound: The setting can't be resolved and it hasn't default value.

        Returns:
            Setting value.
        """
        logger.debug(f"Getting the setting: {key}")
        try:
            value = await self.internal_backend.get(key)
            if value != UNDEFINED:
                return value
        except KeyError:
            if self.external_backend:
                logger.debug(f"Setting {key} not found in internal cache, searching in external backend")
                return await self.get_external(key, default)

        if default != _EmptyArg:
            return default
        else:
            raise SettingNotFound(key)

    async def get_external(self, key, default=_EmptyArg):
        """Get the setting from the external backend updating the internal one with the value of the external.

        Args:
            key (str): Path to the setting.
            default: Default value in case that the setting doesn't exists in the external backend.

        Returns:
            Setting value.
        """
        try:
            value = await self.external_backend.get(key, default)
        except Exception:
            logger.warning(f"Setting {key} not found in external backend")
            raise SettingNotFound(key)
        else:
            await self.internal_backend.set(key, value)
            return value

    async def set(self, key, value):  # noqa: A003
        """Set a setting value.

        Args:
            key (str): Path to the setting.
            value: Value to be set in the setting key.
        """
        logger.info(f"Changing the value of the setting: {key}")

        await self.internal_backend.set(key, value)
        if self.external_backend:
            await self.external_backend.set(key, value)

    async def delete(self, key):
        """Delete a setting.

        Args:
            key (str): Path to the setting.
        """
        logger.info(f"Deleting the setting: {key}")

        await self.internal_backend.delete(key)
        if self.external_backend:
            await self.external_backend.delete(key)

    async def watch(self, key, callback):
        """Schedule a callback for when a setting is changed in the etcd backend.

        Args:
            key (str): Path to the setting.
            callback: function or coroutine to be called when the setting changes, it should have with two input
                arguments, one for the setting path and other for the setting value.
        """
        if self.etcd_external:
            await self.external_backend.watch(key, callback)
        else:
            logger.warning(f"Trying to watch the setting {key} when it is not in the ETCD backend")

    async def update_internal_settings(self, key, value):
        """Update an specific internal setting.

        Args:
            key (str): Path to the setting.
            value: Setting value.
        """
        await self.internal_backend.set(key, value)
        logger.debug(f"The internal setting {key} has changed")

    async def watch_and_update(self, key):
        """Watch one specific settings and maintain it updated in the internal settings.

        Args:
            key (str):  Path to the setting.
        """
        if self.etcd_external:
            await self.external_backend.watch(key, self.update_internal_settings)
        else:
            logger.warning(f"Trying to watch the setting {key} when it is not in the ETCD backend")

    async def stop(self):
        """Perform all the needed tasks in order to stop the Settings."""
        await self.cancel_watch_tasks()

    async def cancel_watch_tasks(self):
        """Cancel all the pending watcher tasks of the settings in the etcd backend."""
        if self.etcd_external:
            self.external_backend.cancel_watch_tasks()
        else:
            logger.warning(f"Trying to cancel all settings watcher tasks, but not ETCD backend found. Doing nothing")


class SettingsView(SettingsInterface):
    """View/chroot/jail/box of main settings class.
    Used in the resources to provide them with their subset of settings.
    """

    def __init__(self, settings, prefix, microservice_name=None):
        """
        Args:
            settings: settings main object.
            prefix: prefix where the view is going to operate.
            microservice_name: name of the microservice, it is going to be used to find custom settings for a specific
                microservice.
        """
        self.prefix = prefix
        self.settings = settings
        self.microservice_name = microservice_name
        if microservice_name:
            framework_prefix, *setting_route = prefix.split(".")
            self.microservice_prefix = f"{framework_prefix}.microservices.{microservice_name}.{'.'.join(setting_route)}"

    async def get(self, key, default=_EmptyArg, raw=False):
        """Get setting.

        Args:
            key (str): Path to the setting.
            default: Default value in case that the setting doesn't exists in the external backend.
            raw: if True no prefix is used so is not a view.
        """
        if not raw:
            general_key = f"{self.prefix}.{key}"
            if self.microservice_name:
                microservice_key = f"{self.microservice_prefix}.{key}"
                value = await self.settings.get(microservice_key, UNDEFINED)
                if value != UNDEFINED:
                    return value
                logger.warning(
                    f"Setting {microservice_key} not found in external backend, it will use {general_key} instead."
                )
            return await self.settings.get(general_key, default)
        else:
            return await self.settings.get(key, default)

    async def set(self, key, value, raw=False):  # noqa: A003
        """Set a setting value.

        Args:
            key (str): Path to the setting.
            default: Default value in the case that it doesn't exists.
            raw: If True no prefix is used so is not a view.

        Returns:
            Setting value.
        """
        if not raw:
            key = f"{self.prefix}.{key}"
        return await self.settings.set(key, value)

    async def delete(self, key, raw=False):
        """Delete a setting.

        Args:
            key (str): Path to the setting.
            raw: If True no prefix is used so is not a view.
        """
        if not raw:
            key = f"{self.prefix}.{key}"
        return await self.settings.delete(key)

    async def watch(self, key, callback, raw=False):
        """Schedule a callback for when a setting is changed in the etcd backend.

        Args:
            key (str): Path to the setting.
            callback: Callback to run whenever the `key` changes.
            raw: If True no prefix is used so is not a view.
        """
        key_microservice = key
        if not raw:
            if self.microservice_name:
                key_microservice = f"{self.microservice_prefix}.{key}"
            key = f"{self.prefix}.{key}"

        await self.settings.watch(key, callback)
        if self.microservice_name:
            await self.settings.watch(key_microservice, callback)

    async def update_internal_settings(self, key, value):
        """Update internal settings.

        Args:
            key (str): Path to the setting.
            value: Setting value.
        """
        await self.settings.update_internal_settings(key, value)
        logger.debug(f"The internal setting {key} has changed")

    async def cancel_watch_tasks(self):
        """Cancel all the pending watcher tasks of the settings in the etcd backend."""
        await self.settings.cancel_watch_tasks()
