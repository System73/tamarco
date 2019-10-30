.. _a_walk_around_the_settings:

A walk around the settings
==========================

Tamarco is an automation framework for managing the lifecycle and resources of the microservices. The
configuration has a critical role in the framework, all the other resources and components of the framework
strongly depend on the settings.

When you have thousands of microservices running in production the way to provide the configuration of the system
becomes critical. Some desirable characteristics of a microservice settings framework are:

#) | The configuration should be centralized. A microservice compiled in a container should be able to run in different
   | environments without any change in the code. For example, the network location of a database or its credentials
   | aren't going to be the same in a production environment or a staging environment.

#) | The configuration should be able to change in runtime without restarting the microservices. For example, you should
   | be able to update the configuration of your WebSocket server without close the existing connections.

#) | The configuration should have redundancy. One of the advantages of a microservice architecture is the facility to
   | obtain redundancy in your services, you should be able to run the microservices in several machines if someone
   | fails, the others should be able to work correctly. Nothing of this has a sense if your services aren't able to
   | read the configuration, so to take the benefits of this architectural advantage, all critical services of the
   | system must be redundant as well.

The external backend supported by this framework right now is etcd v2, we strongly recommend its use in production
with Tamarco.

Other settings backends are available to develop:

* Dictionary
* File based (YML or JSON)

Settings structure
------------------

The settings can be configured from a simple YAML in etcd [Link of how to configure an etcd from a file]. A generic
setting could be the following:

.. code-block:: yaml

    etcd_ready: true
    system:
       deploy_name: tamarco_tutorial
       logging:
           profile: PRODUCTION
           file: false
           stdout: true
       resources:
           amqp:
               host: 172.31.0.102
               port: 5672
               vhost: /
               user: guest
               password: guest
               connection_timeout: 10
               queues_prefix: ""
           kafka:
               bootstrap_servers: 172.31.0.1:9092,172.31.0.2:9092
       microservices:
           http_server:
               application_cache_seconds: 10

The etcd_ready setting is written by the etcd configuration script when it finishes configuring all the other settings.
This prevents the microservices from reading the settings before the environment is properly configured.

All the other tamarco settings are inside a root_path named “system”. The settings under the root path are:

* | Deploy_name. Name that identifies a deploy, used by default by logging and metrics resources with the purpose of
  | distinct logs and metrics from different deploys. Possible use cases: allow to filter logs of deploys in different
  | regions or by develop, staging and production with the same monitoring system.

* | Logging: Configuration of the logging of the system, it is out of resources because this configuration can’t be
  | avoided since it is a core component, all the microservices and all resources emit logs. More information about the
  | possible configuration in [TODO link to logging section].

* | Resources: configurations of the resources of the system, it can be used by one or more microservices. See:
  | :ref:`setup_setting_for_a_resource`.

* | Microservice: configuration of the business logic of each microservice. This section also has a special property,
  | all the other settings can be configured by in this section for a specific microservice. See:
  | :ref:`setup_setting_for_a_specific_microservice`.
