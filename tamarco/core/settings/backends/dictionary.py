import asyncio

from tamarco.core.settings.backends.interface import SettingsInterface, _EmptyArg


class DictSettingsBackend(SettingsInterface):
    """Class to handle settings based in a python dictionary."""

    def __init__(self, dict_settings, loop=None):
        self.loop = loop
        self.settings = dict_settings
        self.callbacks = {}

    def set_loop(self, loop):
        self.loop = loop

    async def get(self, key, default=_EmptyArg):
        """Return the setting value.

        Args:
            key (str): Path to the setting.
            default: Default value to return if the key does not exist.

        Returns:
            Setting value.
        """
        setting = self.settings
        for token in key.split("."):
            try:
                setting = setting[token]
            except (KeyError, TypeError):
                if default != _EmptyArg:
                    return default
                else:
                    raise KeyError(key)
        return setting

    async def set(self, key, value):  # noqa: A003
        """Set the setting value.

        Args:
            key (str): Path to the setting.
            value: Setting value to set.
        """
        setting = self.settings
        tokens = key.split(".")[:-1]
        last_token = key.split(".")[-1]
        for token in tokens:
            if token not in setting or not isinstance(setting[token], dict):
                setting[token] = {}
            setting = setting[token]
        setting[last_token] = value
        await self._trigger_callbacks(key)

    async def delete(self, key):
        """Delete a setting.

        Args:
            key (str): Path to the setting.
        """
        setting = self.settings
        tokens = key.split(".")[:-1]
        last_token = key.split(".")[-1]
        for token in tokens:
            setting = setting[token]
        del setting[last_token]
        await self._trigger_callbacks(key)

    async def watch(self, key, callback):
        """Create a hook in the key to trigger the callback when a setting is changed.

        Args:
            key (str): Path to the setting.
            callback: Callback to call when the value of the key change.
        """
        self.callbacks[key] = self.callbacks.get(key, []) + [callback]

    async def _trigger_callbacks(self, key):
        for callback_key in self.callbacks.keys():
            if callback_key in key:
                try:
                    value = await self.get(callback_key)
                except KeyError:
                    value = None
                for callback in self.callbacks[callback_key]:
                    asyncio.ensure_future(callback(callback_key, value), loop=self.loop)
