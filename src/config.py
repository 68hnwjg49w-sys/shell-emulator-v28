"""Параметры запуска эмулятора и чтение стартового скрипта."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from src.errors import ConfigError

NOT_SET = "(не задан)"
COMMENT_PREFIX = "#"
FIRST_LINE = 1


@dataclass(frozen=True)
class Config:
    """Параметры запуска: путь к VFS и путь к стартовому скрипту."""

    vfs_path: str | None = None
    script_path: str | None = None

    def items(self):
        """Возвращает параметры списком пар «ключ, значение»."""
        return [
            ("vfs", _or_not_set(self.vfs_path)),
            ("script", _or_not_set(self.script_path)),
        ]


def _or_not_set(value):
    """Заменяет None пометкой «не задан»."""
    return NOT_SET if value is None else value


def parse_arguments(argv=None):
    """Разбирает параметры командной строки в объект Config."""
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="Консольный эмулятор командной оболочки UNIX.",
    )
    parser.add_argument(
        "--vfs", dest="vfs_path", metavar="PATH",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script", dest="script_path", metavar="PATH",
        help="путь к стартовому скрипту",
    )
    namespace = parser.parse_args(argv)
    return Config(namespace.vfs_path, namespace.script_path)


def read_script(path):
    """Читает стартовый скрипт: пары (номер строки, команда)."""
    check_script_path(path)
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(
            "стартовый скрипт {}: не удалось прочитать: {}".format(
                path, error)
        ) from error
    lines = enumerate(text.splitlines(), start=FIRST_LINE)
    return [(number, line.strip()) for number, line in lines
            if _is_command(line)]


def check_script_path(path):
    """Проверяет, что путь к стартовому скрипту ведёт к файлу."""
    if not path:
        raise ConfigError("путь к стартовому скрипту пуст")
    script = Path(path)
    if not script.exists():
        raise ConfigError("стартовый скрипт не найден: {}".format(path))
    if not script.is_file():
        raise ConfigError(
            "стартовый скрипт {}: указан не файл".format(path)
        )


def _is_command(line):
    """Проверяет, что строка скрипта не пустая и не комментарий."""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_PREFIX)
