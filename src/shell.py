"""Ядро эмулятора: разбор строки и выполнение команд."""

from datetime import datetime
from functools import partial

from src import cmd_disk, cmd_nav, cmd_time
from src.errors import CommandError
from src.paths import resolve
from src.vfs import Vfs

SAVE_ARGS = 1
HOME_LABEL = "~"
COMMANDS = {
    "ls": cmd_nav.ls,
    "cd": cmd_nav.cd,
    "du": cmd_disk.du,
    "uptime": cmd_time.uptime,
    "cal": cmd_time.cal,
}


def tokenize(line):
    """Разделяет строку ввода на команду и аргументы по пробелам."""
    return line.split()


class Shell:
    """Ядро эмулятора: хранит состояние и выполняет команды."""

    def __init__(self, vfs=None, now=datetime.now):
        """Создаёт ядро с VFS, часами и набором встроенных команд."""
        self.vfs = vfs if vfs is not None else Vfs()
        self.running = True
        self.cwd = []
        self.now = now
        self.started = now()
        self._commands = {
            name: partial(handler, self) for name, handler in COMMANDS.items()
        }
        self._commands["exit"] = self._exit
        self._commands["vfs-save"] = self._vfs_save

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

    def path(self, text):
        """Превращает путь из команды в список имён от корня VFS."""
        return resolve(self.cwd, text)

    def cwd_label(self):
        """Текущий каталог для приглашения: ~ — корень VFS."""
        return HOME_LABEL + "".join("/" + part for part in self.cwd)

    def _exit(self, name, args):
        """Завершает работу эмулятора."""
        if args:
            raise CommandError(
                "{}: аргументы не поддерживаются".format(name)
            )
        self.running = False
        return ""

    def _vfs_save(self, name, args):
        """Сохраняет состояние VFS на диск: vfs-save путь."""
        if len(args) != SAVE_ARGS:
            raise CommandError(
                "{}: нужен ровно один аргумент — путь".format(name)
            )
        self.vfs.save(args[0])
        return "{}: VFS сохранена в {}".format(name, args[0])
