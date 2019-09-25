# Tamarco

[![Build Status](https://travis-ci.com/System73/tamarco.svg?branch=master)](https://travis-ci.com/System73/tamarco)

Microservices framework designed for asyncio and Python.

## Features

* Lifecycle management.
* Standardized settings via etcd.
* Automatic logging configuration. Support for sending logs to an ELK stack.
* Application metrics via Prometheus. 
* Designed for asyncio.
* Messaging patterns. The framework comes with support for AMQP and Kafka via external resources. The AMQP resource has 
implemented publish/subscribe, request/response and push/pull patterns. 
* Custom encoders and decoders. 
* Pluging oriented architecture. Anyone can create a new resource to add new functionality. External resources are integrated 
into the framework transparently for the user.
* Graceful shutdown.

## Resources

The framework allows to write external resources and integrate them in the lifecycle of a microservice easily. List with
 the available resources:

* Metrics.
* Registry.
* Status.
* Profiler.
* Memory analizer.
* HTTP.
* Kafka. Not released yet.
* AMQP. Not released yet.
* Postgres. Not released yet.
* Influxdb. Not released yet.
* Redis. Not released yet.
* Websocket. Not released yet.

Let us know if you have written a resource.

## Documentation

Can be built doing a `make docs`. It will be publicly available soon.

## Examples

There are several examples in the `examples` folder.

To run them, install tamarco, launch the docker-compose (not necessary for all the examples) and run it.

```python3
pip install tamarco
docker-compose up -d
python examples/http_resource/microservice.py
```

## Requirements

Support for Python >= 3.6.
