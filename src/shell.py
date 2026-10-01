"""Ядро эмулятора: разбор строки и выполнение команд."""

from src.errors import CommandError

MAX_CD_ARGS = 1


def tokenize(line):
    """Разделяет строку ввода на команду и аргументы по пробелам."""
    return line.split()


class Shell:
    """Ядро эмулятора: хранит состояние и выполняет команды."""

    def __init__(self):
        """Создаёт ядро с набором встроенных команд."""
        self.running = True
        self._commands = {
            "ls": self._ls,
            "cd": self._cd,
            "exit": self._exit,
        }

    def execute(self, line):
        """Выполняет строку ввода и возвращает текст ответа."""
        tokens = tokenize(line)
        if not tokens:
            return ""
        name, args = tokens[0], tokens[1:]
        handler = self._commands.get(name)
        if handler is None:
            raise CommandError("{}: команда не найдена".format(name))
        return handler(name, args)

    @staticmethod
    def _ls(name, args):
        """Заглушка ls: выводит своё имя и аргументы."""
        return stub_answer(name, args)

    @staticmethod
    def _cd(name, args):
        """Заглушка cd: принимает не больше одного аргумента."""
        if len(args) > MAX_CD_ARGS:
            raise CommandError("{}: слишком много аргументов".format(name))
        return stub_answer(name, args)

    def _exit(self, name, args):
        """Завершает работу эмулятора."""
        if args:
            raise CommandError(
                "{}: аргументы не поддерживаются".format(name)
            )
        self.running = False
        return ""


def stub_answer(name, args):
    """Формирует ответ заглушки: имя команды и её аргументы."""
    if not args:
        return "{}: вызвана без аргументов".format(name)
    return "{}: аргументы: {}".format(name, ", ".join(args))
