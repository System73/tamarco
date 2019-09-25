.. _setup_a_setting_backend:

How to setup a setting backend
==============================

There are some ways to set up the settings, etcd is the recommended backend for a centralized configuration. The YML and
file and dictionary are useful for development.

etcd
----

etcd is the recommended backend for a centralized configuration. All the configuration of the system can be in etcd,
but before being able to read it, we should specify to the microservices how to access an etcd.

The following environment variables need to be properly configured to use etcd:

* TAMARCO_ETCD_HOST: Needed to setup the etcd as setting backend.
* TAMARCO_ETCD_PORT: Optional variable, by default is 2379.
* ETCD_CHECK_KEY: Optional variable, if set the microservice waits until the specified etcd key exits to initialize.
Avoids race conditions between the etcd and microservices initialization. Useful in orchestrators such docker-swarm
where dependencies between components cannot be easily specified.

YML file
--------

For enable the feature, the following environment variable must be set:

* TAMARCO_YML_FILE: Example: 'settings.yml'. Example of a YML file with the system configuration:

.. code-block:: yaml

    system:
      deploy_name: test_tamarco
      logging:
        profile: DEVELOP
        file: false
        stdout: true
        redis:
          enabled: false
          host: "127.0.0.1"
          port: 7006
          password: ''
          ssl: false
      microservices:
        test:
          logging:
            profile: DEVELOP
            file: false
            stdout: true
      resources:
        metrics:
          collect_frequency: 15
        status:
          host: 127.0.0.1
          port: 5747
          debug: False
        amqp:
          host: 127.0.0.1
          port: 5672
          vhost: /
          user: microservice
          password: 1234
          connection_timeout: 10
          queues_prefix: "prefix"

Dictionary
----------

It is possible to load the configuration from a dictionary:


.. code-block:: python

    import asyncio

    from sanic.response import text

    from tamarco.core.microservice import Microservice, MicroserviceContext, thread
    from tamarco.resources.io.http.resource import HTTPClientResource, HTTPServerResource


    class HTTPMicroservice(Microservice):
        name = 'settings_from_dictionary'
        http_server = HTTPServerResource()

        def __init__(self):
            super().__init__()
            self.settings.update_internal({
                'system': {
                    'deploy_name': 'settings_documentation',
                    'logging': {
                        'profile': 'PRODUCTION',
                    },
                    'resources': {
                        'http_server': {
                            'host': '127.0.0.1',
                            'port': 8080,
                            'debug': True
                        }
                    }
                }
            })


    ms = HTTPMicroservice()


    @ms.http_server.app.route('/')
    async def index(request):
        print('Requested /')
        return text('Hello world!')


    def main():
        ms.run()


    if __name__ == '__main__':
        main()

