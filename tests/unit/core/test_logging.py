import socket
import time

from datetime import datetime
from logging import LogRecord

import ujson

from tamarco.core.logging.formatters.colored import ColoredFormatter
from tamarco.core.logging.formatters.logstash import LogstashFormatterVersion0, LogstashFormatterVersion1
from tamarco.core.logging.formatters.syslog import SyslogFormatter
from tamarco.core.logging.handlers.asyncronous import AsyncWrapperHandler, MAX_QUEUE_SIZE, VALUE_TOLERANCE_PERCENTAGE


def test_logging_colored_formatter_format_timestamp():
    timestamp = time.time()
    _datetime = datetime.fromtimestamp(timestamp).isoformat(sep=" ")
    assert _datetime == ColoredFormatter.format_timestamp(timestamp)


def test_logging_logstash_formatter_version_0():
    log_record = LogRecord(
        name="test_logging_ColoredFormatter_format",
        level=1,
        pathname="test/logging",
        lineno=1,
        msg="hello world",
        args=["args1", "args2"],
        exc_info=None,
    )
    time_stamp = 1_400_000_000
    log_record.created = time_stamp
    formater_base = LogstashFormatterVersion0()
    hostname = socket.gethostname()
    data_format = formater_base.format(log_record).decode()
    data = ujson.loads(data_format)

    assert data == {
        "@timestamp": "2014-05-13T16:53:20.000Z",
        "@message": "hello world",
        "@source": f"Logstash://{hostname}/test/logging",
        "@source_host": f"{hostname}",
        "@source_path": "test/logging",
        "@tags": [],
        "@type": "Logstash",
        "@fields": {"levelname": "Level 1", "logger": "test_logging_ColoredFormatter_format", "stack_info": None},
    }


def test_logging_logstash_formatter_version_1():
    log_record = LogRecord(
        name="test_logging_ColoredFormatter_format",
        level=1,
        pathname="test/logging",
        lineno=1,
        msg="hello world",
        args=["args1", "args2"],
        exc_info=None,
    )
    time_stamp = 1_400_000_000
    log_record.created = time_stamp
    formater_base = LogstashFormatterVersion1()
    hostname = socket.gethostname()
    data_format = formater_base.format(log_record).decode()
    data = ujson.loads(data_format)

    assert data == {
        "@timestamp": "2014-05-13T16:53:20.000Z",
        "@version": "1",
        "message": "hello world",
        "host": f"{hostname}",
        "path": "test/logging",
        "tags": [],
        "type": "Logstash",
        "level": "Level 1",
        "logger_name": "test_logging_ColoredFormatter_format",
        "stack_info": None,
    }


def test_logging_syslog_formatter():
    log_record = LogRecord(
        name="test_logging_ColoredFormatter_format",
        level=1,
        pathname="test/logging",
        lineno=1,
        msg="hello world",
        args=["args1", "args2"],
        exc_info=None,
    )
    timestamp = 1_400_000_000
    log_record.created = timestamp
    log_record.extra_msg = {"extra_msg1": "foo"}
    formater_base = SyslogFormatter()
    hostname = socket.getfqdn()
    formatted_time = datetime.fromtimestamp(timestamp).isoformat(sep=" ")
    assert (
        formater_base.format(log_record).strip() == f"[{formatted_time}] [{hostname}] [Level 1] "
        "[(test_logging_ColoredFormatter_format) logging:1] "
        '[null] [hello world] [{"json_extra_msg1":"foo"}]'
    )


class HandlerCheck:
    check_data = False

    def __init__(self):
        HandlerCheck.check_data = False

    def handle(self, record):
        HandlerCheck.check_data = True


def test_logging_async_wrapper_handler():
    async_wrapper = AsyncWrapperHandler(handler=HandlerCheck)
    assert async_wrapper.queue.maxsize == MAX_QUEUE_SIZE

    log_record_array_inter = []
    log_record_array_outer = []

    assert not HandlerCheck.check_data

    async_wrapper.listener.stop()
    time.sleep(2)

    for _ in range(80):
        log_record = LogRecord(
            name="test_logging_ColoredFormatter_format",
            level=1,
            pathname="test/logging",
            lineno=1,
            msg="hello world",
            args=["args1", "args2"],
            exc_info=None,
        )
        time_stamp = 1_400_000_000
        log_record.created = time_stamp
        log_record_array_inter.append(log_record)
        async_wrapper.emit(log_record)

    for _ in range(80):
        check_enqueue_d = async_wrapper.listener.dequeue(False)
        log_record_array_outer.append(check_enqueue_d)

    assert async_wrapper.queue.empty()
    assert log_record_array_inter == log_record_array_outer


def test_logging_async_wrapper_handler_tolerance():
    async_wrapper = AsyncWrapperHandler(handler=HandlerCheck)
    assert async_wrapper.queue.maxsize == MAX_QUEUE_SIZE

    num_record_array_enqueue = 0
    num_record_array_dequeue = 0
    counter = 0
    assert not HandlerCheck.check_data

    async_wrapper.listener.stop()
    time.sleep(2)

    for _ in range(MAX_QUEUE_SIZE):
        time_stamp = 1_400_000_000
        log_record = LogRecord(
            name="test_logging_ColoredFormatter_format",
            level=1,
            pathname="test/logging",
            lineno=1,
            msg="hello world",
            args=["args1", "args2"],
            exc_info=None,
        )
        log_record.created = time_stamp
        num_record_array_enqueue += 1
        async_wrapper.emit(log_record)
        counter += 1

    try:
        for _ in range(MAX_QUEUE_SIZE * 10):
            async_wrapper.listener.dequeue(False)
            num_record_array_dequeue += 1
    except Exception:
        pass

    assert num_record_array_dequeue == VALUE_TOLERANCE_PERCENTAGE
