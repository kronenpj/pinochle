""" Adjust mutmut's behavior a little."""


def pre_mutation(context):
    skip_source = [
        "src/pinochle/custom_log.py",
        "src/pinochle/log_decorator.py",
    ]
    strings = [
        "_get_input",
        "argp.add_argument",
        "argparse.ArgumentParser",
        "assert",
        "help=",
        "if __name__ ==",
        "InvalidDeckError",
        "InvalidSuiteError",
        "InvalidValueError",
        "is not an instance of",
        "Joker",
        "jokers=",
        "List",
        "log",
        "LOG",
        "mylog",
        "outstream.write",
        "print",
        "raise",
        "sys.exit",
        "Union",
    ]
    if context.filename in skip_source:
        context.skip = True
        return
    for string in strings:
        if string in context.current_source_line:
            context.skip = True
            break
