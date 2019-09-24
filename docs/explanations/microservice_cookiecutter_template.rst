Microservice cookicutter template
=================================

When you install the tamarco python package is available a _tamarco_ command. Calling this command you can create a new
microservice skeleton answering before a few questions::

    $ tamarco start_project

1. Project name: project name. In the same directory when you execute the tamarco command the script will create a
folder with this name and all the initial files insite it. Used also in the docs and README files.
1. Project slug: project short name. Inside of the project name folder, a folder with this name is created and all the
microservice logic code should be here. Used also in the docs files.
1. Full name: author's full name. Used in the docs files.
1. Email: author's email. Used in the docs files.
1. Version: initial project version. It will be copied to the setup.cfg file.
1. Project short description: this text will be in the initial README file created.


The project skeleton will be::

    <project_name>
       |
       |- docs (folder with the files to generate Sphinx documentation)
       |
       |- tests (here will be store the microservice tests)
       |
       |- <project_slug>
       |     |
       |     |- logic (microservice business logic code)
       |     |
       |     |- resources (code related with the microservice resources: databases, ...)
       |     |
       |     |- meters.py (application meters: prometheus, ...)
       |     |
       |     |- microservice.py (microservice class inherited from Tamarco Microservice class)
       |
       |- .coveragerc (coverage configuration file)
       |
       |- .gitignore
       |
       |- app.py (entrypoint file for the microservice)
       |
       |- Dockerfile
       |
       |- HISTORY.md
       |
       |- Makefile (run the tests, generate docs, create virtual environments, install requirements, ...)
       |
       |- README.md
       |
       |- requirements.txt
       |
       |- setup.cfg (several python packages configurations: bumpversion, flake8, pytest, ...)
       |