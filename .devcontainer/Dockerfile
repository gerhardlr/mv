FROM mcr.microsoft.com/vscode/devcontainers/python:3.11-bookworm

RUN pipx install poetry

ENV PATH=/home/vscode/.local/bin/:$PATH

RUN poetry config virtualenvs.in-project true

RUN eval $(minikube docker-env)