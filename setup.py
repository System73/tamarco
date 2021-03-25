#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

resources_require = {
    "ci": [
        "radon==3.0.1",
        "pep8==1.7.1",
        "pytest==4.3.0",
        "pytest-asyncio==0.10.0",
        "pytest-timeout==1.3.3",
        "flake8==3.7.7",
        "flake8-html==0.4.0",
        "flake8-deprecated==1.3",
        "flake8-comprehensions==2.1.0",
        "flake8-colors==0.1.6",
        "flake8-builtins==1.4.1",
        "flake8-bugbear==18.8.0",
        "coverage==4.5.3",
        "black==19.3b0",
    ],
    "visibility": ["prctl==1.6.1", "GitPython==2.1.11"],
}

requirements = [
    "sanic-plugins-framework==0.8.1",
    "urllib3==1.25.2",
    "idna==2.8",
    "sanic==19.3.1",
    "cookiecutter==1.6.0",
    "aiohttp==3.5.4",
    "aiohttp_cors==0.7.0",
    "aio_etcd==0.4.6.1",
    "objgraph==3.4.1",
    "pyes==0.99.6",
    "thrift==0.11.0",
    "redis==3.2.1",
    "fire==0.1.3",
    "inflection==0.3.1",
    "sanic-cors==0.9.8",
    "cachetools==3.1.0",
    "ujson==1.35",
    "dnspython==1.15.0",
    "dnspython3==1.15.0",
    "pyYAML==5.4",
]

setup(
    name="tamarco",
    version="0.1.1",
    description="Microservices framework designed for asyncio and Python",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="System73 Engineering Team",
    author_email="opensource@system73.com",
    url="https://github.com/System73/tamarco",
    scripts=["tamarco/tamarco"],
    packages=["tamarco"],
    include_package_data=True,
    install_requires=requirements,
    extras_require=resources_require,
    zip_safe=False,
    keywords="tamarco",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite="pytests",
)
