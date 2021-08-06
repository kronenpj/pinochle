import logging
from os import environ
from sys import stdout

name = "pinochle"  # pragma: no mutate

GLOBAL_LOG_LEVEL: int
if "GLOBAL_LOG_LEVEL" in environ:
    print("Setting GLOBAL_LOG_LEVEL from environment.")
    GLOBAL_LOG_LEVEL = int(environ["GLOBAL_LOG_LEVEL"])
else:
    GLOBAL_LOG_LEVEL = logging.WARNING


def setup_logging() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(GLOBAL_LOG_LEVEL)

    handler = logging.StreamHandler(stdout)
    handler.setLevel(root_logger.getEffectiveLevel())
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )  # pragma: no mutate
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return root_logger
