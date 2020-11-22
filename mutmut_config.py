""" Adjust mutmut's behavior a little."""


def pre_mutation(context):
    strings = [
        "argp.add_argument",
        "argparse.ArgumentParser",
        "assert",
        "_get_input",
        "help=",
        "if __name__ ==",
        "log",
        "mylog",
        "outstream.write",
        "print",
        "sys.exit",
    ]
    for string in strings:
        if string in context.current_source_line:
            context.skip = True
            break
