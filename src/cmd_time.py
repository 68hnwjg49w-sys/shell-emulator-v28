"""Команды, связанные со временем: uptime и cal."""

import calendar

from src.errors import CommandError

MAX_CAL_ARGS = 2
YEAR_ONLY_ARGS = 1
ONE_DAY = 1
MIN_MONTH, MAX_MONTH = 1, 12
MIN_YEAR, MAX_YEAR = 1, 9999
MINUTES_IN_HOUR = 60
MINUTES_IN_DAY = 24 * MINUTES_IN_HOUR
SECONDS_IN_MINUTE = 60
USERS = "1 user"


def uptime(shell, name, args):
    """Показывает время работы эмулятора: время, «up», число users."""
    if args:
        raise CommandError("{}: аргументы не поддерживаются".format(name))
    now = shell.now()
    span = _format_span(now - shell.started)
    return " {:%H:%M:%S} up {}, {}".format(now, span, USERS)


def _format_span(delta):
    """Форматирует длительность: «5 min», «2:03» или «1 day, 2:03»."""
    total = int(delta.total_seconds() // SECONDS_IN_MINUTE)
    days, rest = divmod(total, MINUTES_IN_DAY)
    hours, minutes = divmod(rest, MINUTES_IN_HOUR)
    clock = "{}:{:02}".format(hours, minutes)
    if days:
        return "{} {}, {}".format(days, "day" if days == ONE_DAY else "days",
                                  clock)
    if hours:
        return clock
    return "{} min".format(minutes)


def cal(shell, name, args):
    """Печатает календарь: cal, cal ГОД или cal МЕСЯЦ ГОД."""
    if len(args) > MAX_CAL_ARGS:
        raise CommandError("{}: слишком много аргументов".format(name))
    text_calendar = calendar.TextCalendar(calendar.MONDAY)
    if not args:
        today = shell.now()
        return _clean(text_calendar.formatmonth(today.year, today.month))
    if len(args) == YEAR_ONLY_ARGS:
        year = _number(name, args[0], "год", MIN_YEAR, MAX_YEAR)
        return _clean(text_calendar.formatyear(year))
    month = _number(name, args[0], "месяц", MIN_MONTH, MAX_MONTH)
    year = _number(name, args[1], "год", MIN_YEAR, MAX_YEAR)
    return _clean(text_calendar.formatmonth(year, month))


def _number(name, text, label, low, high):
    """Разбирает целое число в диапазоне или сообщает об ошибке."""
    try:
        value = int(text)
    except ValueError:
        value = None
    if value is None or not low <= value <= high:
        raise CommandError(
            "{}: неверный {}: '{}'".format(name, label, text)
        )
    return value


def _clean(text):
    """Убирает пробелы в конце строк календаря и пустые строки."""
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip("\n")
