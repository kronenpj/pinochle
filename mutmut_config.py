""" Adjust mutmut's behavior a little."""


def pre_mutation(context):
    strings = [
        r"argp.add_argument",
        r"argparse.ArgumentParser",
        r"assert",
        r"_get_input",
        r"help=",
        r"if __name__ ==",
        r"InvalidDeckError",
        r"InvalidSuiteError",
        r"InvalidValueError",
        r"is not an instance of",
        r"jokers=",
        r"Joker",
        r"List",
        r"log",
        r"mylog",
        r"outstream.write",
        r"print",
        r"raise",
        r"sys.exit",
        r"Union",
    ]
    for string in strings:
        if string in context.current_source_line:
            context.skip = True
            break
