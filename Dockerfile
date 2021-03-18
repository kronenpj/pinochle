FROM docker.io/library/python:3.8-slim

RUN pip install poetry

ENV SRC_DIR /usr/local/src/pinochle

WORKDIR ${SRC_DIR}

COPY pyproject.toml poetry.lock poetry.toml ${SRC_DIR}/
RUN poetry install --no-dev --no-root

COPY src/pinochle/ ${SRC_DIR}/pinochle/
COPY src/instance/ ${SRC_DIR}/pinochle/instance/
COPY run-gunicorn ${SRC_DIR}
RUN chmod +x ${SRC_DIR}/run-gunicorn

ENV FLASK_APP pinochle
ENV FLASK_DEBUG=1

CMD ["./run-gunicorn"]
