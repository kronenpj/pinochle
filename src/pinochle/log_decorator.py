"""
Definition of a decorator that logs function entry/exit with parameters and
return values.
"""
import functools
import os
import sys
from inspect import getframeinfo, stack
from typing import Any

from . import custom_log

# Originally from https://github.com/hima03/log-decorator.git
# Modified for my own preferences.


def log_decorator(_func=None) -> Any:  # pragma: no cover
    """The log decorator is used when a log entry is desired upon function
    entry or exit. The decorator emits the argument list and return values along
    with the begin/end message."""

    def log_decorator_info(func) -> object:
        @functools.wraps(func)
        def log_decorator_wrapper(self=None, *args, **kwargs) -> Any:
            # Build logger object
            logger_obj = custom_log.get_logger()

            # Create a list of the positional arguments passed to function.
            # - Using repr() for string representation for each argument. repr() is
            #   similar to str() only difference being it prints with a pair of quotes
            #   and if we calculate a value we get more precise value than str().
            args_passed_in_function = [repr(a) for a in args]

            # Create a list of the keyword arguments. The f-string formats each
            # argument as key=value, where the !r specifier means that repr() is used
            # to represent the value.
            kwargs_passed_in_function = [f"{k}={v!r}" for k, v in kwargs.items()]

            # The lists of positional and keyword arguments is joined together to form
            # the final string
            formatted_args = ", ".join(args_passed_in_function)
            formatted_kwargs = ", ".join(kwargs_passed_in_function)
            formatted_arguments = f"{formatted_args}, {formatted_kwargs}"

            # Generate file name and function name for calling function. __func.name__
            # will give the name of the caller function ie. wrapper_log_info and caller
            # file name ie log-decorator.py
            # - In order to get actual function and file name we will use 'extra'
            #   parameter.
            # - To get the file name we are using in-built module inspect.getframeinfo
            #   which returns calling file name
            py_file_caller = getframeinfo(stack()[1][0])
            extra_args = {
                "func_name_override": func.__name__,
                "file_name_override": os.path.basename(py_file_caller.filename),
            }

            # Before to the function execution, log function details.
            logger_obj.info(
                f"Begin function: Arguments: {formatted_arguments}", extra=extra_args
            )
            try:
                # log return value from the function
                value = func(self, *args, **kwargs)
                logger_obj.info(
                    f"End function  : Returned: {value!r}", extra=extra_args
                )
            except TypeError:
                # log return value from the function
                value = func(*args, **kwargs)
                logger_obj.info(
                    f"End function  : Returned: {value!r}", extra=extra_args
                )
            except Exception:
                # log exception if occurs in function
                logger_obj.error(f"Exception     : {str(sys.exc_info()[1])}")
                raise
            # Return function value
            return value

        # Return the pointer to the function
        return log_decorator_wrapper

    # Decorator was called with arguments, so return a decorator function that can
    # read and return a function
    if _func is None:
        return log_decorator_info

    # Decorator was called without arguments, so apply the decorator to the function
    # immediately
    return log_decorator_info(_func)
