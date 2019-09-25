.. _setup_setting_for_a_resource:

How to setup settings for a resource
====================================

The resources are designed to automatically load their configuration using the setting resource.

The resources should be defined as an attribute of the microservice class:

.. code-block:: python

    class MyMicroservice(Microservice):
        name = 'settings_from_dictionary'

        recommendation_http_api = HTTPServerResource()
        billing_http_api = HTTPServerResource()

        def __init__(self):
            super().__init__()
            self.settings.update_internal({
                'system': {
                    'deploy_name': 'settings_documentation',
                    'logging': {
                        'profile': 'PRODUCTION',
                    },
                    'resources': {
                        'recommendation_http_api': {
                            'host': '127.0.0.1',
                            'port': 8080,
                            'debug': True
                        },
                        'billing_http_api': {
                            'host': '127.0.0.1',
                            'port': 9090,
                            'debug': False
                        }
                    }
                }
            })

The resources load their configuration based on the name of the attribute used to bind the resource to the microservice.
In the example, we have two HTTPServerResource in the same microservice and each one uses a different configuration.

The HTTPServerResource recommendations_api variable is going to find its configuration in the path
'system.resources.recommendation_api'.

You must be cautious about choosing the name when the instances are created. If several microservices use the same
database, the name of the resource instance in the microservice must be the same in all microservices to load the same
configuration.
