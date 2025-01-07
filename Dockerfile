FROM python:3.11.9

# add-apt-repository -y ppa:deadsnakes/ppa && apt update && apt install -y python3.11 python3.8-venv

RUN apt-get update && apt-get install telnet -y

RUN pip install pipx && pipx install poetry 

ENV PATH=/root/.local/bin/:$PATH

RUN poetry config virtualenvs.in-project true

WORKDIR /root/app

COPY poetry.lock pyproject.toml README.md /root/app/

COPY tests /root/app/tests

# COPY dependencies seperate from app to create a cache

RUN poetry install --no-root

COPY mv mv

RUN poetry install

COPY --chmod=777 scripts/check_tango_zmq_event_port.sh /root/app/.venv/bin/check_tango_zmq_event_port

COPY --chmod=777 scripts/check_tango_zmq_heartbeat_port.sh /root/app/.venv/bin/check_tango_zmq_heartbeat_port

ENV PATH=/root/app/.venv/bin/:$PATH


CMD ["serve"]
