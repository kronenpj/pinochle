"""
Customized log configuration
"""
import inspect
import logging
import sys

# Originally from https://github.com/hima03/log-decorator.git
# Modified for my own preferences.


class CustomFormatter(logging.Formatter):  # pragma: no cover
    """Custom Formatter does these 2 things:
    1. Overrides 'funcName' with the value of 'func_name_override', if it exists.
    2. Overrides 'filename' with the value of 'file_name_override', if it exists.
    """

    def format(self, record) -> str:  # pragma: no cover
        if hasattr(record, "func_name_override"):
            record.funcName = record.func_name_override
        if hasattr(record, "file_name_override"):
            record.filename = record.file_name_override
            if hasattr(record, "module"):
                record.module = record.file_name_override.rstrip(".py")
        return super(CustomFormatter, self).format(record)


def get_logger() -> logging.Logger:  # pragma: no cover
    """Customizes and returns a Logger object.
    Set the formatter of 'CustomFormatter' type as we want to log base function name
    and base file name
    """

    # Create logger object and set the format for logging and other attributes
    logger = logging.Logger(f"{__package__}.{inspect.stack()[2][3]}")
    if logger.getEffectiveLevel() != logging.getLogger(__package__).getEffectiveLevel():
        logger.setLevel(logging.getLogger(__package__).getEffectiveLevel())

    handler = logging.StreamHandler(stream=sys.stderr)

    handler.setFormatter(
        # CustomFormatter(
        #     "%(asctime)s:%(levelname)-10s:%(filename)s:%(funcName)s:%(message)s"
        # )
        CustomFormatter(
            "[%(asctime)s] - %(module)s:%(funcName)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(handler)

    # Return logger object
    return logger
