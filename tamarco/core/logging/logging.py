import logging.config
import sys

from tamarco.core.patterns import Singleton
from tamarco.core.utils import check_connection_http_url
from .formatters.colored import ColoredFormatter
from .formatters.logstash import LogstashFormatterVersion1
from .formatters.syslog import SyslogFormatter

PROFILES = {"DEVELOP": {"loglevel": "DEBUG"}, "PRODUCTION": {"loglevel": "INFO"}, "TESTING": {"loglevel": "DEBUG"}}


class Logging(metaclass=Singleton):
    """Class that handles the configuration of the standard logging of python using the microservice settings."""

    def __init__(self):
        """Initialize the Tamarco logging class with the available formatters."""
        self.color_blind = False
        self.settings = None
        self.microservice_name = None
        self.deploy_name = None
        self.logging_config = {
            "version": 1,
            "formatters": {
                "detail": {
                    "format": "[%(asctime)s] [%(levelname)s] [(%(processName)s) "
                    "%(filename)s:%(lineno)s %(funcName)s] %(message)s"
                },
                "colored": {"()": ColoredFormatter, "color_blind": self.color_blind},
                "syslog_format": {"()": SyslogFormatter},
                "logstash": {"()": LogstashFormatterVersion1},
            },
            "handlers": {},
            "loggers": {},
        }

    @staticmethod
    def describe_static_settings():
        """Describe all the settings as a dictionary keys and their values are a setting short description.
        These settings are the static settings needed by the class.

        Returns:
            dict: Settings and their description.
        """
        return {
            "profile": "Profile of logging, it can be  DEVELOP, TESTING or PRODUCTION",
            "elasticsearch": 'List of connections string of elasticsearch. Example: ["127.0.0.1:9300"]',
            "redis": "Dictionary with the redis connection parameters: host, port, password",
            "logstash": "Logstash info connection: host and port",
            "http": "HTTP endpoint",
            "file_path": "File path where the logs are going to be stored",
            "stdout": "If true there is logging through stdout",
        }

    @staticmethod
    def describe_dynamic_settings():
        """Describe all the class dynamic settings.

        Returns:
            dict: Settings and their description.
        """
        return {}

    def configure_settings(self, settings):
        """Sets the settings object (a SettingsView(f"{ROOT_SETTINGS}.logging")).

        Args:
            settings (SettingsInterface): Settings object that have the logging settings.
        """
        self.settings = settings

    async def start(self, loggers, microservice_name, deploy_name, loop):
        """Configure the standard python logging, adding handlers and loggers that uses that handlers.

        Args:
            loggers (list): Names of the loggers you want to configure.
            microservice_name (str): Name of the microservice that will use the logging.
            deploy_name (str): Deploy name.
            loop: asyncio event loop.
        """
        self.microservice_name = microservice_name
        self.deploy_name = deploy_name
        await self.__setup_handlers(loop=loop)
        await self.__setup_loggers(loggers)
        logging.config.dictConfig(self.logging_config)
        await self.__setup_watchers()

    async def __setup_handlers(self, loop):
        """Configures the logging handlers needed by the loggers of the microservices.

        Args:
            loop: asyncio event loop.
        """
        await self.__setup_stdout_handler()
        await self.__setup_file_handler()
        await self.__setup_redis_handler()
        await self.__setup_http_handler(loop)
        await self.__setup_logstash_handler()
        await self.__setup_elasticsearch_handler()

    async def __setup_stdout_handler(self):
        """Configures the stdout logging handler."""
        if await self.settings.get("stdout", True):
            self.logging_config["handlers"]["stdout"] = {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                "stream": sys.stdout,
            }

    async def __setup_file_handler(self):
        """Configures the file logging handler."""
        if await self.settings.get("file_path", False):
            self.logging_config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "syslog_format",
                "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                "filename": await self.settings.get("file_path"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 100,
                "encoding": "utf8",
            }

    async def __setup_redis_handler(self):
        """Configures the redis logging handler."""
        if await self.settings.get("redis.enabled", False):
            self.logging_config["handlers"]["redis"] = {
                "class": "tamarco.core.logging.handlers.redis.AsyncRedisHandler",
                "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                "redis_conf": {
                    "host": await self.settings.get("redis.host"),
                    "password": await self.settings.get("redis.password"),
                    "port": await self.settings.get("redis.port"),
                    "ssl": await self.settings.get("redis.ssl"),
                },
                "service_name": self.microservice_name,
                "deploy_name": self.deploy_name,
            }

    async def __setup_logstash_handler(self):
        """Configures the logstash logging handler."""
        if await self.settings.get("logstash.enabled", False):
            self.logging_config["handlers"]["logstash"] = {
                "class": "tamarco.core.logging.handlers.logstash.AsyncUDPLogstashHandler",
                "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                "host": await self.settings.get("logstash.host", "127.0.0.1"),
                "port": await self.settings.get("logstash.port", 5959),
                "fqdn": await self.settings.get("logstash.fqdn", False),
                "service_name": self.microservice_name,
                "deploy_name": self.deploy_name,
                "version": await self.settings.get("version", 1),
            }

    async def __setup_http_handler(self, loop):
        """Configures the HTTP logging handler."""
        if await self.settings.get("http.enabled", False):
            if await check_connection_http_url(url=await self.settings.get("http.url", ""), loop=loop):
                self.logging_config["handlers"]["http"] = {
                    "class": "tamarco.core.logging.handlers.http.HTTPSHandler",
                    "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                    "url": await self.settings.get("http.url"),
                    "user": await self.settings.get("http.user"),
                    "password": await self.settings.get("http.password"),
                    "max_time_seconds": await self.settings.get("http.max_time_seconds", 1),
                    "max_records": await self.settings.get("http.max_records", 10),
                    "service_name": self.microservice_name,
                    "deploy_name": self.deploy_name,
                    "loop": loop,
                }

    async def __setup_elasticsearch_handler(self):
        """Configures the Elasticsearch logging handler."""
        if await self.settings.get("elasticsearch.enabled", False):
            self.logging_config["handlers"]["elasticsearch"] = {
                "class": "tamarco.core.logging.handlers.elasticsearch.AsyncElasticSearchHandler",
                "level": PROFILES[await self.settings.get("profile")]["loglevel"],
                "conn_strs": await self.settings.get("elasticsearch.host"),
                "service_name": self.microservice_name,
                "deploy_name": self.deploy_name,
            }

    async def __setup_loggers(self, loggers_names):
        """Configures all the loggers needed by the microservice adding to them the handlers.

        Args
            loggers_names (list): Names of the loggers you want to configure.
        """
        profile = await self.settings.get("profile")

        for logger_name in loggers_names:
            logger = self.__create_logger(logger_name, PROFILES[profile]["loglevel"])
            self.logging_config["loggers"].update(logger)

    def __create_logger(self, logger_name, level):
        """Configures the loggers (all enable handlers, level) for the logger `logger_name` with the logging
        level `level`.

        Args:
            logger_name (str): Logger name.
            level (str): Logging level.

        Returns:
            dict: Logging configuration, set with the handlers and the logging level.
        """
        logger = {"handlers": [], "level": level, "propagate": False}

        if "stdout" in self.logging_config["handlers"]:
            logger["handlers"].append("stdout")
            print(f"Logging handler stdout configured for {logger_name}.")

        if "elasticsearch" in self.logging_config["handlers"]:
            logger["handlers"].append("elasticsearch")
            print(f"Logging handler elasticsearch configured for {logger_name}.")

        if "redis" in self.logging_config["handlers"]:
            logger["handlers"].append("redis")
            print(f"Logging handler redis logstash configured for {logger_name}.")

        if "http" in self.logging_config["handlers"]:
            logger["handlers"].append("http")
            print(f"Logging handler http configured for {logger_name}.")

        if "file" in self.logging_config["handlers"]:
            logger["handlers"].append("file")
            print(f"Logging handler file configured for {logger_name}.")

        if "logstash" in self.logging_config["handlers"]:
            logger["handlers"].append("logstash")
            print(f"Logging handler logstash configured for {logger_name}.")

        return {logger_name: logger}

    async def __setup_watchers(self):
        """Adds default watchers for the logging level. It adds the watcher to the system logging and
        the microservice logging.
        """

        async def watcher_callback(key, setting):
            """ Callback when the watcher reports that the key `key` has changed in the etcd.

            Args:
                key (str): etcd key.
                setting (str): The setting value already formatted.
            """
            await self.settings.update_internal_settings(key, setting)
            profile = await self.settings.get("profile")

            if profile in PROFILES.keys():
                new_profile = PROFILES[profile]["loglevel"]
                self.logging_config["handlers"]["stdout"]["level"] = new_profile
                for logger in self.logging_config["loggers"].items():
                    logger[1]["level"] = new_profile

                logging.config.dictConfig(self.logging_config)

        await self.settings.watch("profile", watcher_callback)
