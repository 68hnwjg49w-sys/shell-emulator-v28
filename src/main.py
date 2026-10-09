"""Точка входа эмулятора командной оболочки."""

import sys

from src.config import parse_arguments, read_script
from src.errors import EmulatorError
from src.repl import Repl, build_prompt, current_host, current_user
from src.shell import Shell
from src.vfs import Vfs

EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
DEBUG_PREFIX = "[debug] "


def print_debug(config):
    """Выводит все параметры запуска эмулятора (отладочный вывод)."""
    print(DEBUG_PREFIX + "параметры запуска:")
    for key, value in config.items():
        print("{}  {} = {}".format(DEBUG_PREFIX, key, value))


def prepare(config):
    """Загружает VFS и читает стартовый скрипт по параметрам."""
    vfs = Vfs()
    if config.vfs_path is not None:
        vfs = Vfs.load(config.vfs_path)
    script = []
    if config.script_path is not None:
        script = read_script(config.script_path)
    return vfs, script


def greet(vfs):
    """Сообщает о загруженной VFS и выводит motd, если он есть."""
    dirs, files = vfs.stats()
    print("{}VFS в памяти: каталогов {}, файлов {}".format(
        DEBUG_PREFIX, dirs, files))
    motd = vfs.motd()
    if motd:
        print(motd.rstrip("\n"))


def make_prompt(shell):
    """Возвращает функцию, строящую приглашение с текущим каталогом."""
    user, host = current_user(), current_host()

    def prompt():
        """Приглашение вида username@hostname:~/каталог$."""
        return build_prompt(user, host, shell.cwd_label())

    return prompt


def main(argv=None):
    """Запускает эмулятор и возвращает код завершения процесса."""
    try:
        config = parse_arguments(argv)
        print_debug(config)
        vfs, script = prepare(config)
    except EmulatorError as error:
        print("ошибка запуска: {}".format(error), file=sys.stderr)
        return EXIT_CONFIG_ERROR

    greet(vfs)
    shell = Shell(vfs)
    repl = Repl(shell, make_prompt(shell))
    repl.run_script(script)
    repl.loop()
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
