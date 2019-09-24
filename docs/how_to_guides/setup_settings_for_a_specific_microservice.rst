.. _setup_setting_for_a_specific_microservice:

How to setup settings for a specific microservice
=================================================

The settings under `system.microservice.<microservice_name>.<setting_paths_to_override>`
overrides the general settings of `system.<setting_paths_to_override>` in the microservice
named <microservice_name>.

In the following example, the microservice dog is going to read the logging profile "DEVELOP" and
the other microservices are going to stay in the logging profile "PRODUCTION":

.. code-block:: yaml

    system:
      deploy_name: tamarco_doc
      logging:
        profile: PRODUCTION
        file: false
        stdout: true
      microservices:
        dog:
          logging:
            profile: DEVELOP

The microservice name is declared when the microservice class is defined:

.. code-block:: python

    class MicroserviceExample(Microservice):

        name = 'my_microservice_name'
