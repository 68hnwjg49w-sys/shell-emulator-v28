"""Точка входа эмулятора командной оболочки."""

import sys

from src.config import parse_arguments, read_script
from src.errors import ConfigError
from src.repl import Repl, build_prompt, current_host, current_user
from src.shell import Shell

EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
DEBUG_PREFIX = "[debug] "


def print_debug(config):
    """Выводит все параметры запуска эмулятора (отладочный вывод)."""
    print(DEBUG_PREFIX + "параметры запуска:")
    for key, value in config.items():
        print("{}  {} = {}".format(DEBUG_PREFIX, key, value))


def main(argv=None):
    """Запускает эмулятор и возвращает код завершения процесса."""
    try:
        config = parse_arguments(argv)
        print_debug(config)
        script = []
        if config.script_path is not None:
            script = read_script(config.script_path)
    except ConfigError as error:
        print("ошибка запуска: {}".format(error), file=sys.stderr)
        return EXIT_CONFIG_ERROR

    repl = Repl(Shell(), build_prompt(current_user(), current_host()))
    repl.run_script(script)
    repl.loop()
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
