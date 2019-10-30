Write your first microservice
=============================

In this section, we will create a simple microservice that inserts data to a Postgres table.


Installation
------------

For this example, we need the Tamarco framework and the Postgres resource plugin. Optionally, you can create
a virtual environment before installing the packages::

    $ virtualenv virtualenv -p python3.6
    $ . virtualenv/bin/activate
    $ pip3 install tamarco tamarco-postgres


Using Tamarco code generation
-----------------------------

Tamarco provides the generation of a microservice skeleton using `cookiecutter
<https://github.com/cookiecutter/cookiecutter>`_. templates. To use this feature, go to the path where you want to
create the microservice and type::

    $ tamarco start_project

This command will ask you a few questions to get a minimum service configuration and will generate the code in a new
folder named with the chosen `project_name`. The main script file is called `microservice.py` and for simplification, we
will code all our example in this file.

More information about the microservice code generation: :ref:`microservice_cookiecutter_template`.


Our microservice step by step
-----------------------------

The code generated in `microservice.py` is very simple:

.. code-block:: python

    from tamarco.core.microservice import Microservice


    class MyMicroservice(Microservice):
        name = "my_awesome_project_name"


    def main():
        ms = MyMicroservice()
        ms.run()

In the previous code, we can see that our service inherits from the Tamarco base class `Microservice`. This class will
be the base of all the microservices and it is responsible for starting all the resources and at the same time stop all
the resources properly when the microservice exits. It has several execution stages in its lifecycle. For more
information see: :ref:`microservice_base_class`.

The next step is to declare the Postgres resource we want to use:

.. code-block:: python

    from tamarco.core.microservice import Microservice
    from tamarco-postgres import PostgresClientResource


    class MyMicroservice(Microservice):
        name = "my_awesome_project_name"
        postgres = PostgresClientResource()


In a production environment, we normally get the service settings/configuration from a storage service like etcd, but
to simplify, now we set the required configuration using an internal function. More info about the Tamarco settings in:
:ref:`a_walk_around_the_settings`.


.. code-block:: python

    from tamarco.core.microservice import Microservice
    from tamarco-postgres import PostgresClientResource

    class MyMicroservice(Microservice):
        name = "my_awesome_project_name"
        postgres = PostgresClientResource()

        def __init__(self):
            super().__init__()
            self.settings.update_internal({
                "system": {
                    "deploy_name": "my_first_microservice",
                    "logging": {
                        "profile": "DEVELOP",
                    },
                    "resources": {
                        "postgres": {
                            "host": "127.0.0.1",
                            "port": 5432,
                            "user": "postgres"
                        }
                    }
                }
            })

Our service already knows where to connect to the database, so, we have to create the table and make the queries.
Tamarco provides a decorator (`@task`) to convert a method in an asyncio task. The task is started and stopped when
the microservice starts and stops respectively:


.. code-block:: python

    from tamarco.core.microservice import Microservice, task
    from tamarco-postgres import PostgresClientResource

    class MyMicroservice(Microservice):
        name = "my_awesome_project_name"
        postgres = PostgresClientResource()

        def __init__(self):
            super().__init__()
            self.settings.update_internal({
                "system": {
                    "deploy_name": "my_first_microservice",
                    "logging": {
                        "profile": "DEVELOP",
                    },
                    "resources": {
                        "postgres": {
                            "host": "127.0.0.1",
                            "port": 5432,
                            "user": "postgres"
                        }
                    }
                }
            })

        @task
        async def postgres_query(self):
            create_query = '''
                CREATE TABLE my_table (
                    id INT PRIMARY KEY NOT NULL,
                    name TEXT NOT NULL
                  );
                '''
            insert_query = "INSERT INTO my_table (id, name) VALUES (1, 'John Doe');"
            select_query = "SELECT * FROM my_table"

            try:
                await self.postgres.execute(create_query)
                await self.postgres.execute(insert_query)
                response = await self.postgres.fetch(select_query)
            except Exception:
                self.logger.exception("Error executing query")
            else:
                self.logger.info(f"Data: {response}")


NOTICE that we imported `task` from tamarco.core.microservice!!


Running our microservice
------------------------

Firstly, we need a running Postgres, so we can launch a docker container::

    $ docker run -d -p 5432:5432 postgres

In the root of our project, there is the service entry point: `app.py`. You can execute this file and check the result
(don't forget to activate the virtualenv if you have one)::

    $ python app.py

