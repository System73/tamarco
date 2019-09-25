How to setup the logging
========================

The profile
-----------

Two different profiles are allowed:

* DEVELOP. The logging level is set to debug.
* PRODUCTION. The logging level is set to info.

The profile setting needs to be in capital letters.

.. code-block:: yaml

    system:
      logging:
        profile: <DEVELOP or PRODUCTION>


Stdout
------

The logging by stdout can be enabled or disabled:

It comes with the

.. code-block:: yaml

    system:
      logging:
        stdout: true


File handler
------------

Write all logs in files with a `RotatingFileHandler`. It is enabled
when the system/logging/file_path exits, saving the logs in the specified location.

.. code-block:: yaml

    system:
      logging:
        file_path: <file_path>


Logstash
--------

Logstash is the log collector used by Tamarco, it collects, processes, enriches and unifies all the logs sent by different
components of an infrastructure. Logstash supports multiple choices for the log ingestion, we support three of them
simply by activating the corresponding settings:


Logstash UDP handler
````````````````````

Send logs to Logstash using a raw UDP socket.

.. code-block:: yaml

    system:
      logging:
        logstash:
          enabled: true
          host: 127.0.0.1
          port: 5044
          fqdn: false
          version: 1


Logstash Redis handler
``````````````````````

Send logs to Logstash using the Redis pubsub pattern.

.. code-block:: yaml

    system:
      logging:
        redis:
          enabled: true
          host: 127.0.0.1
          port: 6379
          password: my_password
          ssl: false


Logstash HTTP handler
`````````````````````

Send logs to Logstash using HTTP requests.


.. code-block:: yaml

    system:
      logging:
        http:
          enabled: true
          url: http://127.0.0.1
          user:
          password:
          max_time_seconds: 15
          max_records: 100

The logs are sent in bulk, the max_time_seconds is the maximum time without sending the logs, the max_records configures
 the maximum number of logs in a single HTTP request (The first condition triggers the request).
