from tamarco.core.patterns import Proxy
from tamarco.core.settings.settings import Settings, SettingsNotLoadedYet


class SettingProxy(Proxy):
    """Proxy pattern used as a pointer/reference, this proxy is returned
     by when_loaded_setting function. When the settings are loaded
     the obj that proxies this proxy is set to the value of the setting.
     If is used before the load of settings a SettingsNotLoadedYet exception is raised.
    """

    def __getattribute__(self, name):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        return getattr(obj, name)

    def __delattr__(self, name):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        delattr(obj, name)

    def __setattr__(self, name, value):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        setattr(obj, name, value)

    def __nonzero__(self):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        return bool(obj)

    def __str__(self):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        return str(obj)

    def __repr__(self):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(obj, SettingsNotLoadedYet):
            raise obj
        return repr(obj)

    @staticmethod
    def make_method(name):
        def method(self, *args, **kw):
            obj = object.__getattribute__(self, "_obj")
            if isinstance(obj, SettingsNotLoadedYet):
                raise obj
            return getattr(obj, name)(*args, **kw)

        return method


def when_loaded_setting(key):
    """Helper function that returns a proxy that when the settings is loaded
      the object behind the proxy is the value of the key passed to the function
      so you can instantiate a settings value before the settings are loaded
      and when they are loaded that instance should be the settings value,
      if not raises an exception

    Args:
        key(str): Path to the setting.

    Returns:
        setting proxy.
    """
    promised_setting = SettingProxy(SettingsNotLoadedYet("No settings yet"))
    Settings().register_promised_setting(key, promised_setting)
    return promised_setting
