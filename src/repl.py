"""Консольный интерфейс эмулятора: приглашение, ввод и вывод."""

import getpass
import socket

from src.errors import EmulatorError

HOME_DIR = "~"
UNKNOWN = "unknown"
EXIT_ECHO = "exit"
SCRIPT_STOPPED = "стартовый скрипт остановлен: ошибка в строке {}"


def current_user():
    """Возвращает имя пользователя ОС."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return UNKNOWN


def current_host():
    """Возвращает короткое имя компьютера, как в приглашении bash."""
    return socket.gethostname().split(".")[0] or UNKNOWN


def build_prompt(user, host, directory=HOME_DIR):
    """Собирает приглашение вида username@hostname:~$."""
    return "{}@{}:{}$ ".format(user, host, directory)


class Repl:
    """Цикл «прочитать — выполнить — вывести» в консоли."""

    def __init__(self, shell, prompt, read=input, write=print):
        """Связывает ядро с функциями ввода и вывода."""
        self._shell = shell
        self._prompt = prompt
        self._read = read
        self._write = write

    def run_line(self, line):
        """Выполняет строку; возвращает False, если произошла ошибка."""
        try:
            answer = self._shell.execute(line)
        except EmulatorError as error:
            self._write(str(error))
            return False
        if answer:
            self._write(answer)
        return True

    def run_script(self, commands):
        """Выполняет стартовый скрипт до первой ошибки.

        Каждая команда выводится вместе с приглашением, как будто её
        ввёл пользователь. Возвращает True, если ошибок не было.
        """
        for number, line in commands:
            if not self._shell.running:
                break
            self._write(self._prompt + line)
            if not self.run_line(line):
                self._write(SCRIPT_STOPPED.format(number))
                return False
        return True

    def loop(self):
        """Читает и выполняет команды до exit или конца ввода."""
        while self._shell.running:
            try:
                line = self._read(self._prompt)
            except EOFError:
                self._write(EXIT_ECHO)
                return
            except KeyboardInterrupt:
                self._write("")
                continue
            self.run_line(line)
