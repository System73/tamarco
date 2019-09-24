import ujson

from tamarco.core.settings.backends.dictionary import DictSettingsBackend


class JsonSettingsBackend(DictSettingsBackend):
    """Class to handle settings that are in a Json file."""

    def __init__(self, file, loop=None):
        settings_dict = ujson.load(open(file))
        super().__init__(settings_dict, loop)


class YamlSettingsBackend(DictSettingsBackend):
    """Class to handle settings that are in a Yaml file."""

    def __init__(self, file, loop=None):
        import yaml

        settings_dict = yaml.full_load(open(file))
        super().__init__(settings_dict, loop)


class PythonSettingsBackend(DictSettingsBackend):
    """Class to handle settings that are in a Python file."""

    def __init__(self, file, loop=None):
        import importlib.util

        spec = importlib.util.spec_from_file_location("settings.python", file)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        settings_dict = settings.__dict__
        super().__init__(settings_dict, loop)
