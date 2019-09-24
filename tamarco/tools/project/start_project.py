import os

from cookiecutter.main import cookiecutter


def main(directory: str = "."):
    print(f"Path of the new microservice project: {directory}")
    self_path = os.path.dirname(os.path.realpath(__file__))
    project_template_path = os.path.join(self_path, "project_template")
    print(f"Project template path: {project_template_path}")
    cookiecutter(template=project_template_path, output_dir=directory)
