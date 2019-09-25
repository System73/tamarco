"""
This file is a script that launch all the Continuous Integration tools in the
tamarco project
"""
import os
import subprocess

PROJECT_ROOT = "."

REPORT_PATH = os.path.join(PROJECT_ROOT, "reports")

FLAKE8_REPORT_HTML_DIR = os.path.join(REPORT_PATH, "flake8-html")
FLAKE8_REPORT_FILE = os.path.join(REPORT_PATH, "flake8.report")
SLOCCOUNT_REPORT_FILE = os.path.join(REPORT_PATH, "sloccount.report")
RADON_REPORT_FILE_XML = os.path.join(REPORT_PATH, "ccm.xml")
RADON_REPORT_FILE = os.path.join(REPORT_PATH, "ccm.report")


def create_reports_dir():
    subprocess.call(["mkdir", REPORT_PATH])


def write_stdout_to_file(file, stdout):
    with open(file, "w") as file:
        decoded_stdout = stdout.decode()
        file.write(decoded_stdout)


class Pytest:
    @classmethod
    def run(cls):
        try:
            import pytest
        except ImportError:  # pragma: no cover
            import logging

            logging.getLogger("tamarco.init").error(
                "Tamarco don't have support for ci please reinstall tamarco with support for it"
                "   > pip install tamarco[ci]"
            )
            raise

        pytest_args = [f"--junitxml={REPORT_PATH}/junit.xml", "--verbose"]

        pytest.main(pytest_args)


class Flake8:
    @classmethod
    def run(cls, path):
        cls.run_flake8_html(path)
        cls.run_flake8_file(path)

    @staticmethod
    def run_flake8_file(path):
        print("Running flake8 file report ...")
        flake8_process = subprocess.Popen(["flake8", path], stdout=subprocess.PIPE)
        stdout, stderr = flake8_process.communicate()
        write_stdout_to_file(FLAKE8_REPORT_FILE, stdout)

    @staticmethod
    def run_flake8_html(path):
        print("Running flake8 html report ...")
        flake_8_html_report_command = f"flake8 --format=html --htmldir={FLAKE8_REPORT_HTML_DIR} {path}".split()
        flake8_html_process = subprocess.Popen(flake_8_html_report_command, stdout=subprocess.PIPE)
        flake8_html_process.wait()


class Sloccount:
    @staticmethod
    def run(path: str):
        have_sloccount = not subprocess.call(["which", "sloccount"])
        if have_sloccount:
            print("Running sloccount ...")
            sloccount = subprocess.Popen(
                ["sloccount", "--duplicates", "--wide", "--details", path], stdout=subprocess.PIPE
            )
            stdout, stderr = sloccount.communicate()
            write_stdout_to_file(SLOCCOUNT_REPORT_FILE, stdout)
        else:
            print("sloccount not found in system, install it with your package manager to be able to use it")


class Radon:
    @classmethod
    def run(cls, path: str):
        cls.run_radon_txt(path)
        cls.run_radon_xml(path)

    @staticmethod
    def run_radon_txt(path: str):
        print("Running radon for a human readable report ...")
        radon = subprocess.Popen(["radon", "cc", "-a", "-i", "project_template", path], stdout=subprocess.PIPE)
        stdout, stderr = radon.communicate()
        write_stdout_to_file(RADON_REPORT_FILE, stdout)

    @staticmethod
    def run_radon_xml(path: str):
        print("Running radon for a xml report ...")
        radon = subprocess.Popen(["radon", "cc", "-a", "--xml", "-i", "project_template", path], stdout=subprocess.PIPE)
        stdout, stderr = radon.communicate()
        with open(RADON_REPORT_FILE_XML, "w") as radon_report:
            radon_report.write('<?xml version="1.0" ?>')
            radon_report.write(stdout.decode())


def main(
    path: str, no_pytest: bool = False, no_flake8: bool = False, no_sloccount: bool = False, no_radon: bool = False
):

    create_reports_dir()

    if not no_pytest:
        Pytest.run()

    if not no_flake8:
        Flake8.run(path)

    if not no_sloccount:
        Sloccount.run(path)

    if not no_radon:
        Radon.run(path)
