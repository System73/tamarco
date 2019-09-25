import logging
import sys
import time
from collections import deque

import redis
from redis.exceptions import ConnectionError, TimeoutError

from tamarco.core.logging.formatters import logstash
from tamarco.core.logging.handlers.asyncronous import AsyncWrapperHandler

MAX_RECORDS_STORE = 1000
ELAPSED_ERROR_TIME = 10


class RedisHandler(logging.Handler):
    """Logging handler that sends the logs to a redis database."""

    def __init__(
        self,
        redis_conf=None,
        record_type="record",
        service_name=None,
        deploy_name=None,
        level=logging.NOTSET,
        fqdn=False,
        version=0,
    ):
        """Initialize the handler.

        Args:
            redis_conf (dict): Redis connection info, a key with the host address and other key with the
                port. E.g.: {"host": "127.0.0.1", "port": 7000}
            record_type (str): The record type always will be 'record'.
            service_name (str): Service name.
            deploy_name (str): Deploy name.
            level (str): Logging level. Default: NOTSET
            fqdn (bool): If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            version (int): If 1 it is used the Logstash formatter version 1. Otherwise, the logstash formatter
                version 0.
        """
        logging.Handler.__init__(self, level=level)
        self.redis_conf = {"host": "127.0.0.1", "port": 7006}
        if redis_conf:
            self.redis_conf.update(redis_conf)

        self.key = self.redis_conf.get("key", "logstash")

        self.connected = False
        self.conn = None
        self.try_conn()
        if version == 1:
            self.formatter = logstash.LogstashFormatterVersion1(record_type, fqdn, service_name, deploy_name)
        else:
            self.formatter = logstash.LogstashFormatterVersion0(record_type, fqdn, service_name, deploy_name)

        self.record_store = deque(maxlen=MAX_RECORDS_STORE)
        self.last_error_time = time.time()

    def try_conn(self):
        """Try a new connection to the redis database."""
        try:
            self.conn = redis.StrictRedis(**self.redis_conf)
        except (ConnectionError, TimeoutError) as e:
            print(f"Error connecting to redis of logger !! {e}", file=sys.stderr)

    def elapsed_time(self):
        """Calculate if a certain time has passed since the last error sending the logs. Useful not to saturate
        with error logs.

        Returns:
            bool: True if the last error sending the logs is more that the of a certain time threshold
                (ELAPSED_ERROR_TIME). False otherwise.
        """
        new_error_time = time.time()
        if (new_error_time - self.last_error_time) >= ELAPSED_ERROR_TIME:
            self.last_error_time = new_error_time
            return True
        return False

    def send(self, record):
        """Send the specified log record to redis and, if there are more logs entries in the queue, send them.

        Args:
            record (LogRecord): Entry log.
        """
        try:
            self.conn.rpush(self.key, record)
            for old_record in self.record_store:
                self.conn.rpush(self.key, old_record)
            self.record_store.clear()
        except (ConnectionError, TimeoutError) as e:
            if self.elapsed_time():
                print(f"Error connecting to redis of logger !! {e}", file=sys.stderr)
            self.record_store.append(record)
            self.try_conn()

    def emit(self, record):
        """Format and sends the specified log record."""
        record = self.formatter.format(record)
        self.send(record)


class AsyncRedisHandler(AsyncWrapperHandler):
    """Asynchronous version of the logging handler that sends the logs to a redis database."""

    def __init__(self, *args, **kwargs):
        """Initialize the asynchronous redis handler."""
        super().__init__(RedisHandler, *args, **kwargs)
