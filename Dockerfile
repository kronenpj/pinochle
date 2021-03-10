FROM docker.io/library/python:3.8-slim as builder

RUN apt-get update && apt-get install -y uuid-dev gcc python3-dev
RUN pip wheel libuuid 

FROM docker.io/library/python:3.8-slim

RUN pip install poetry

ENV SRC_DIR /usr/local/src/pinochle

WORKDIR ${SRC_DIR}

COPY --from=builder libuuid-1.0.0-cp38-cp38-linux_x86_64.whl .
COPY pyproject.toml poetry.lock poetry.toml ${SRC_DIR}/
RUN poetry install --no-dev --no-root

COPY pinochle/ ${SRC_DIR}/pinochle/
COPY run-gunicorn ${SRC_DIR}
RUN chmod +x ${SRC_DIR}/run-gunicorn

ENV FLASK_APP pinochle
ENV FLASK_DEBUG=1

CMD ["./run-gunicorn"]
