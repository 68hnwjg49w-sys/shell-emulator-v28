"""Разбор опций команд вида -l, -la, -h."""

from src.errors import CommandError

END_OF_OPTIONS = "--"
LONG_PREFIX = "--"
SHORT_PREFIX = "-"


def split_options(name, args, allowed):
    """Делит аргументы на набор букв-опций и список операндов."""
    flags, operands, options_end = set(), [], False
    for arg in args:
        if options_end or arg == SHORT_PREFIX \
                or not arg.startswith(SHORT_PREFIX):
            operands.append(arg)
        elif arg == END_OF_OPTIONS:
            options_end = True
        else:
            flags |= _parse_flags(name, arg, allowed)
    return flags, operands


def _parse_flags(name, arg, allowed):
    """Разбирает один аргумент-опцию и проверяет допустимость букв."""
    if arg.startswith(LONG_PREFIX):
        raise CommandError("{}: неизвестная опция '{}'".format(name, arg))
    letters = set(arg[1:])
    unknown = sorted(letters - set(allowed))
    if unknown:
        raise CommandError(
            "{}: неизвестная опция -- '{}'".format(name, unknown[0])
        )
    return letters
