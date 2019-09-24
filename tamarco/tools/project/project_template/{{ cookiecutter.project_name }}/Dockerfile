# {{ cookiecutter.project_name }}

FROM python:3.6.0

ADD . /opt/{{ cookiecutter.project_slug }}

RUN mkdir -p /var/log/{{ cookiecutter.project_slug }}

RUN apt-get -qq update \
    && pip3 install -r /opt/{{ cookiecutter.project_slug }}/requirements.txt \
    && apt-get -qq autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/*

CMD python3 /opt/{{ cookiecutter.project_slug }}/app.py
