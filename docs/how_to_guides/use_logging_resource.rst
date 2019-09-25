.. _use_the_logging_resource:

How to use the logging resource
===============================

Tamarco uses the standard logging library, it only interferes doing an automatic configuration based in the settings.

The microservice comes with a logger ready to use:

.. code-block:: python

    import asyncio

    from tamarco.core.microservice import Microservice, task


    class MyMicroservice(Microservice):
        name = 'my_microservice_name'

        extra_loggers_names.append("my_extra_logger")

        @task
        async def periodic_log(self):
            logging.getlogger("my_extra_logger").info("Initializing periodic log")
            while True:
                await asyncio.sleep(1)
                self.logger.info("Sleeping 1 second")

    if __name__ == "__main__":
        ms = MyMicroservice()
        ms.run()

Also can configured more loggers adding their names to `my_extra_logger` list of the Microservice class.

The logger bound to the microservice is the one named as the microservice, so you can get and use the logger whatever
you want:

.. code-block:: python

    import logging

    async def http_handler():
        logger = logging.getlogger('my_microservice_name')
        logger.info('Handling a HTTP request')


Logging exceptions
------------------

A very common pattern programming microservices is log exceptions. Tamarco automatically sends the exception tracing to
Logstash and print the content by stdout when the exc_info flag is active. Only works with logging lines inside an
except statement:

.. code-block:: python

    import asyncio

    from tamarco.core.microservice import Microservice, task


    class MyMicroservice(Microservice):
        name = 'my_microservice_name'

        @task
        async def periodic_exception_log(self):
            while True:
                try:
                    raise KeyError
                except:
                    self.logger.warning("Unexpected exception.", exc_info=True)


    if __name__ == "__main__":
        ms = MyMicroservice()
        ms.run()


Adding extra fields and tags
----------------------------

The fields extend the logging providing more extra information and the tags allow to filter the logs by this key.

A common pattern is to enrich the logs with some information about the context. For example: with a request identifier
the trace can be followed by various microservices.

This fields and tags are automatically sent to Logstash when it is configured.


.. code-block:: python

    logger.info("logger line", extra={'tags': {'tag': 'tag_value'}, 'extra_field': 'extra_field_value'})


Default logger fields
---------------------

Automatically some extra fields are added to the logging.

* `deploy_name`: deploy name configured in `system/deploy_name`, it allows to distinguish logs of different deploys,
for example between staging, develop and production environments.
* `levelname`: log level configured currently in the Microservice.
* `logger`: logger name used when the logger is declared.
* `service_name`: service name declared in the Microservice.
