FROM docker.io/library/python:3.8-slim

RUN pip install pipenv

ENV SRC_DIR /usr/local/src/pinochle

WORKDIR ${SRC_DIR}

COPY Pipfile Pipfile.lock ${SRC_DIR}/

RUN pipenv --three install --system --clear

COPY pinochle/ ${SRC_DIR}/pinochle/
COPY run-gunicorn ${SRC_DIR}
RUN chmod +x ${SRC_DIR}/run-gunicorn

ENV FLASK_APP pinochle
ENV FLASK_DEBUG=1

# CMD ["flask", "run", "-h", "0.0.0.0"]
CMD ["./run-gunicorn"]