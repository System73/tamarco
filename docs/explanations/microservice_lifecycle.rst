Microservice lifecycle
======================

Start
-----

When the microservice is initialized, the following steps are performed, automatically:

#. | Start provisional logging with default parameters. Needed in case of some error before being able to read the final
   | logging configuration from the settings.
#. | Initialize the settings. All the other resources of the framework depend on being able to read the centralized
   | configuration.
#. | Initialize the logging with the proper settings. With the settings available, the next step is to be sure that all
   | the resources can send proper log messages in case of failure before starting them.
#. | Call the pre_start of the microservice, that triggers the pre_start of the microservices. Operations that need to
   | be performed before starting the microservice. For example, a HTTP server could need to render some templates before
   | start the server. It is not advisable to perform I/O operations in the pre_start statement.
#. | Call the start of the microservice, they are going to start all the resources. In the start statement the resources
   | are expected to perform the initial I/O operations, start a server, connect to a database, etc.
#. | Call the post_start of the microservice, it is going to call the post_start of all the resources. In this step all
   | the resources should be working normally because they should be started in the previous step.

Tamarco builds a dependency graph of the order in that the resources should be initialized.

Status of a resource
--------------------

All the resources should report their state, it can be one of the followings:

#. NOT_STARTED
#. CONNECTING
#. STARTED
#. STOPPING
#. STOPPED
#. FAILED

The status of all the resources are exposed via an HTTP API and used by the default restart policies to detect when a
resource is failing.

Resource restart policies
-------------------------

The status resources come by default with the microservice and their responsibility is to apply the
restart policies of the microservice and report the state of the resources via an HTTP API.

There are two settings to control automatically that a resource should do when it has a FAILED status:

.. code-block:: yaml

   system:
       resources:
           status:
               restart_policy:
                   resources:
                       restart_microservice_on_failure: ['redis']
                       restart_resource_on_failure: ['kafka']

Where the microservice is identified by the name of the resource instance in the microservice class.

Keep in mind that the most recommended way is not to use these restart policies and implement a circuit breaker in each
resource. But sometimes you could want a simpler solution and in some cases, the default restart policies can be an
acceptable way to go.

Stop
----

The shut down of a microservice can be triggered by a restart policy (restart_microservice_on_failure), by a system
signal, by a resource (not recommended, a resource shouldn't have the responsibility of stopping a service) or by
business code.

A service only should be stopped calling the method `stop_gracefully` of the microservice instance.

The shut down is performed doing the following steps:

#. Call stop() method of the microservice, it is going to call the stop() of all the resources.
#. Call post_stop() method of the microservice, it is going to call the post_stop() method of all the resources.
#. | The exit is going to be forced after 30 seconds if the microservice didn't finish the shut down in this time or
   | some resource raises an exception stopping the service.


Overwrite lifecycle methods
---------------------------

The lifecycle methods are designed to be overwritten by the user, allowing to execute code at a certain point of the
lifecycle. Just take into account that these methods are asynchronous and that the `super()` method should be called.

The available methods are:

* pre_start
* start
* post_start
* stop
* post_stop

.. code-block:: python

    from tamarco import Microservice

    class LifecycleMicroservice(Microservice):

        async def pre_start(self):
            print("Before pre_start of the service")
            await super().pre_start()
            print("After pre_start of the service")

        async def start(self):
            print("Before start of the service")
            await super().start()
            print("After start of the service")

        async def post_start(self):
            print("Before post_start of the service")
            await super().start()
            print("After post_start of the service")

        async def stop(self):
            print("Before stop of the service")
            await super().stop()
            print("After stop of the service")

        async def post_stop(self):
            print("Before post_stop of the service")
            await super().stop()
            print("After post_stop of the service")


    def main():
        microservice = LifecycleMicroservice(Microservice)
        microservice.run()

    def __name__ == '__main__':
        main()
