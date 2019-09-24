from tamarco.core.microservice import Microservice


class MyMicroservice(Microservice):
    name = "{{cookiecutter.project_slug}}"


def main():
    ms = MyMicroservice()
    ms.run()
