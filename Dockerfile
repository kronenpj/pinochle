FROM docker.io/library/python:3.8-slim

RUN pip install poetry
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

ENV SRC_DIR /usr/local/src/pinochle

WORKDIR ${SRC_DIR}

COPY pyproject.toml poetry.lock poetry.toml ${SRC_DIR}/
RUN poetry install --no-dev --no-root

COPY src/pinochle/ ${SRC_DIR}/pinochle/
COPY src/instance/ ${SRC_DIR}/pinochle/instance/
COPY run-wsgi-server ${SRC_DIR}
RUN chmod +x ${SRC_DIR}/run-wsgi-server

ENV FLASK_APP pinochle
ENV FLASK_DEBUG=1

EXPOSE 8000

CMD ["./run-wsgi-server"]
