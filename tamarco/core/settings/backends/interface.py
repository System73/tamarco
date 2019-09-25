class _EmptyArg:
    pass


class _Undefined:
    pass


class SettingsInterface:
    """Interface for a settings class backend."""

    async def get(self, key, default=_EmptyArg):
        """Return the setting value.

        Args:
            key (str): Path to the setting.
            default: Default value to return if the key does not exist.

        Returns:
            Setting value.
        """
        raise NotImplementedError

    async def set(self, key, value):  # noqa: A003
        """Set the setting value.

        Args:
            key (str): Path to the setting.
            value: Setting value to set.
        """
        raise NotImplementedError

    async def delete(self, key):
        """Delete a setting.

        Args:
            key (str): Path to the setting.
        """
        raise NotImplementedError

    async def watch(self, key, callback):
        """Create a hook in the key to trigger the callback when a setting is changed.

        Args:
            key (str): Path to the setting.
            callback: Callback to call when the value of the key change.
        """
        raise NotImplementedError

    async def cancel_watch_tasks(self):
        """Remove all the watchers from the settings to close the coroutines properly."""
        raise NotImplementedError
