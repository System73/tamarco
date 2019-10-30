.. _microservice_base_class:

Microservice base class
=======================

All the microservices must inherit from the Tamarco Microservice class. Let's take a deeper look into this class.

To launch the microservice, we use the `run` function::

.. code-block:: python

    from tamarco.core.microservice import Microservice

    class MyMicroservice(Microservice):
        [...]

    ms = MyMicroservice()
    ms.run()


When we run the microservice, there is a certain order in the setup of the service and then the event loop is running
until an unrecoverable error occurs, or it is stopped.

Setup steps:

1. Configure and load the microservice settings (and of its resources if used).
1. Configure and start the logging service.
1. Pre-start stage: run all the Tamarco resources `pre_start` methods (only the resources actually used by the
microservice). This method can be overriden if we want to do some coding in this step. But don't forget to call to the
Tamarco function too!

.. code-block:: python
    async def pre_start(self):
        await super().pre_start()
        [...]

1. Start stage: run all the Tamarco resources `start` methods (only the resources actually used by the microservice).
Also collects all the task declared in the microservice (using the `@task` decorator in a method) and launch them.
Generally in this stage is when the database connections, or other services used by the resources are started.
This `start` method can be overriden if we want to do some coding in this step. But don't forget to call to the
Tamarco function too!
1. Post-start stage: run all the Tamarco resources `post_start` methods (only the resources actually used by the
microservice). This method can be overriden if we want to do some coding in this step. But don't forget to call to the
Tamarco function too!
1. Stop stage: run all the Tamarco resources `stop` methods (only the resources actually used by the microservice).
In this stage all resources and tasks are stopped. This method can be overriden if we want to do some coding in this
step. But don't forget to call to the Tamarco function too!
2. Post-stop stage: run all the Tamarco resources `post_stop` methods (only the resources actually used by the
microservice). This step is useful if you want to make some instructions when the microservice stops. This `post_stop`
method can be overriden if we want to do some coding in this step. But don't forget to call to the Tamarco function too!