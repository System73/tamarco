.. _setup_a_metric_backend:


How to setup a metric backend
=============================

The Microservice class comes by default with the metrics resource, this means that the microservice is going to read
the configuration without any explicit code in your microservice.


Prometheus
----------

Prometheus, unlike other metric backends, follows a pull-based (over HTTP) architecture at the metric collection. It
means that the microservices just have the responsibility of exposing the metrics via an HTTP server and Prometheus
collects the metrics requesting them to the microservices.

It is the supported metric backend with a more active development right now.

The metrics resource uses other resource named tamarco_http_report_server, that it is an HTTP server, to expose the
application metrics. The metrics always are exposed to the `/metrics` endpoint. To expose the Prometheus metrics the
microservices should be configured as follows:

.. code-block:: yaml

    system:
      resources:
        metrics:
          collect_frequency: 10
          handlers:
            prometheus:
              enabled: true
        tamarco_http_report_server:
          host: 127.0.0.1
          port: 5747

With this configuration, a microservice is going to expose the Prometheus metrics at http://127.0.0.1:5747/metrics.

The collect frequency defines the update period in seconds of the metrics in the HTTP server.

The microservice name is automatically added as metric suffix to the name of the metrics. Example: A summary named
http_response_time in a microservice named billing_api is going to be named billing_api_http_response_time in the
exposed metrics.


Carbon
------

Only the plaintext protocol sent directly via a TCP socket is supported.

To configure a carbon handler:

.. code-block:: yaml

    system:
      resources:
        metrics:
          handlers:
            carbon:
              enabled: true
              host: 127.0.0.1
              port: 2003
        collect_frequency: 15

The collect frequency defines the period in seconds where the metrics are collected and sent to carbon.


File
----

It is an extension of the carbon handler, instead of sending the metrics to carbon it just appends the metrics to a
file. The format is the following: `<metric path> <metric value> <metric timestamp>`.

To configure the file handler:

.. code-block:: yaml

    system:
      resources:
        metrics:
          handlers:
            file:
              enabled: true
              path: /tmp/tamarco_metrics
        collect_frequency: 15

The collect frequency defines the period in seconds where the metrics are collected and written to a file.


Stdout
------

It is an extension of the carbon handler, instead of sending the metrics to carbon it just writes the metrics in the
stdout. The format is the following: `<metric path> <metric value> <metric timestamp>`.

To configure the file handler:

.. code-block:: yaml

    system:
      resources:
        metrics:
          handlers:
            stdout:
              enabled: true
        collect_frequency: 15


The collect frequency defines the period in seconds where the metrics are collected and written to a file.
