"""Общие помощники для тестов: готовая VFS и управляемые часы."""

from datetime import datetime, timedelta

from src.shell import Shell
from src.vfs import Vfs, VfsDir, VfsFile

START = datetime(2026, 10, 8, 12, 0, 0)


class Clock:
    """Управляемые часы: текущее время меняется вручную."""

    def __init__(self, value=START):
        """Запоминает начальное время."""
        self.value = value

    def __call__(self):
        """Возвращает текущее время часов."""
        return self.value

    def advance(self, **kwargs):
        """Сдвигает часы вперёд на заданный интервал."""
        self.value += timedelta(**kwargs)


def make_vfs():
    """Строит VFS: файлы разного размера, скрытый файл, пустой каталог."""
    docs = VfsDir({
        "a.txt": VfsFile(b"x" * 1500),
        "b.txt": VfsFile(b"yy"),
    })
    julia = VfsDir({"docs": docs, "empty": VfsDir()})
    home = VfsDir({"julia": julia, ".hidden": VfsFile(b"h")})
    return Vfs(VfsDir({
        "home": home,
        "motd": VfsFile(b"hi"),
        "readme.txt": VfsFile(b"0123456789"),
    }))


def make_shell(clock=None):
    """Создаёт ядро с готовой VFS и, при желании, своими часами."""
    return Shell(make_vfs(), clock or Clock())
