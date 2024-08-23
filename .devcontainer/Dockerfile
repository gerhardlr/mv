FROM python:3.10

ARG PROXY=proxy

RUN addgroup --gid 1000 nonroot && \
    adduser -uid 1000 --gid 1000 --disabled-password --gecos "" nonroot && \
    echo "nonroot ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

RUN apt-get update

RUN pip install pipx

RUN pipx install poetry

ENV PATH=/root/.local/bin/:$PATH

RUN /root/.local/bin/poetry config virtualenvs.in-project true