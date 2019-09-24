import asyncio
import logging
from collections import deque

import aiohttp
import ujson

from tamarco.core.logging.formatters.logstash import LogstashFormatterVersion0, LogstashFormatterVersion1

MAX_RECORDS_STORE = 1001


class HTTPSHandler(logging.Handler):
    """Logging handler that sends a set of logs by HTTP with basic authentication."""

    def __init__(
        self,
        url,
        user=None,
        password=None,
        max_time_seconds=None,
        max_records=None,
        fqdn=False,
        localname=None,
        facility=None,
        record_type="record",
        service_name=None,
        deploy_name=None,
        version=0,
        loop=None,
    ):
        """Initialize the HTTP logging handler.

        Args:
            url (str): URL where the logs are sent.
            user (str): HTTP session user authentication.
            password (str): HTTP session password authentication.
            max_time_seconds (int): The maximum seconds interval where the logs are sent.
            max_records (int): If the logs queue reaches to this maximum number of logs, the set of logs are
                sent although the max_time_seconds it has not been reached.
            fqdn: If True, the host field in the log record will be the fully qualified domain. Otherwise,
                the system hostname.
            localname:
            facility:
            record_type (str): The record type always will be 'record'.
            service_name (str): Service name.:
            deploy_name (str): Deploy name.:
            version (int): If 1 it is used the Logstash formatter version 1. Otherwise, the logstash formatter
             version 0.
            loop: Asyncio event loop.
        """
        logging.Handler.__init__(self)
        self.url = url
        self.max_time_seconds = max_time_seconds
        self.max_records = max_records
        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        self.record_store = deque(maxlen=MAX_RECORDS_STORE)
        self.loop = loop if loop else asyncio.get_event_loop()
        if version == 1:
            self.formatter = LogstashFormatterVersion1(record_type, fqdn, service_name, deploy_name)
        else:
            self.formatter = LogstashFormatterVersion0(record_type, fqdn, service_name, deploy_name)
        if user and password:
            self.session = aiohttp.ClientSession(auth=aiohttp.BasicAuth(login=user, password=password))
        else:
            self.session = aiohttp.ClientSession()
        self.periodic_send_task = asyncio.ensure_future(coro_or_future=self.periodic_send(), loop=self.loop)

    async def periodic_send(self):
        """Periodic sending of the logs stored in the queue."""
        while True:
            await asyncio.sleep(self.max_time_seconds, loop=self.loop)
            self.send()

    def close(self):
        """Closes the handler instance."""
        self.send()
        self.periodic_send_task.cancel()
        super().close()

    def send(self):
        """HTTP POST request sending the logs stored in the queue."""
        try:
            asyncio.ensure_future(
                coro_or_future=self.session.post(self.url, json=list(self.record_store)), loop=self.loop
            )
        except Exception:
            print(f"[HTTPSHandler] Error sending logs to {self.url}")
        else:
            self.record_store.clear()

    def emit(self, record):
        """Emit the specified log record.

        Args:
            record (LogRecord): Entry log to emit.
        """
        try:
            payload = self.formatter.format(record)
            self.record_store.append(ujson.loads(payload))
            if self.record_store and len(self.record_store) >= self.max_records:
                self.send()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)
