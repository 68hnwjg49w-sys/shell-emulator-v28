"""Команды навигации по VFS: ls и cd."""

from src.errors import CommandError
from src.options import split_options
from src.sizes import human
from src.vfs import VfsDir, node_size

NOT_FOUND = "Нет такого файла или каталога"
NOT_DIR = "Не является каталогом"
MAX_CD_ARGS = 1
SINGLE_TARGET = 1
LIST_SEPARATOR = "  "
CURRENT_DIR = "."


def cd(shell, name, args):
    """Переходит в каталог VFS; без аргумента — в корень (~)."""
    if len(args) > MAX_CD_ARGS:
        raise CommandError("{}: слишком много аргументов".format(name))
    text = args[0] if args else "~"
    parts = shell.path(text)
    node = shell.vfs.get(parts)
    if node is None:
        raise CommandError("{}: {}: {}".format(name, text, NOT_FOUND))
    if not isinstance(node, VfsDir):
        raise CommandError("{}: {}: {}".format(name, text, NOT_DIR))
    shell.cwd = parts
    return ""


def ls(shell, name, args):
    """Выводит содержимое каталогов и файлов: ls [-lhaq] [путь...]."""
    flags, operands = split_options(name, args, "lhaq")
    files, dirs = _collect(shell, name, operands or [CURRENT_DIR])
    blocks = []
    if files:
        blocks.append(_render(files, flags))
    titled = len(files) + len(dirs) > SINGLE_TARGET
    for text, node in dirs:
        entries = _dir_entries(node, "a" in flags)
        body = _render(entries, flags)
        blocks.append("{}:\n{}".format(text, body) if titled else body)
    return "\n\n".join(block for block in blocks if block)


def _collect(shell, name, texts):
    """Находит узлы по путям и делит их на файлы и каталоги."""
    files, dirs = [], []
    for text in texts:
        node = shell.vfs.get(shell.path(text))
        if node is None:
            raise CommandError(
                "{}: не удаётся получить доступ к '{}': {}".format(
                    name, text, NOT_FOUND)
            )
        target = dirs if isinstance(node, VfsDir) else files
        target.append((text, node))
    return files, dirs


def _dir_entries(node, show_all):
    """Возвращает записи каталога: скрытые файлы только при -a."""
    entries = []
    if show_all:
        entries += [(".", node), ("..", node)]
    for child_name in sorted(node.children):
        if show_all or not child_name.startswith("."):
            entries.append((child_name, node.children[child_name]))
    return entries


def _render(entries, flags):
    """Форматирует записи: в строку или подробным списком (-l)."""
    if "l" not in flags:
        return LIST_SEPARATOR.join(
            _shown(entry_name, flags) for entry_name, _ in entries)
    return "\n".join(_long_line(*entry, flags) for entry in entries)


def _long_line(entry_name, node, flags):
    """Строка подробного списка: тип, размер (с -h удобный) и имя."""
    kind = "d" if isinstance(node, VfsDir) else "-"
    size = node_size(node)
    text = human(size, "") if "h" in flags else str(size)
    return "{} {:>8} {}".format(kind, text, _shown(entry_name, flags))


def _shown(entry_name, flags):
    """Имя для вывода; с -q непечатные символы заменяются на «?»."""
    if "q" not in flags:
        return entry_name
    return "".join(c if c.isprintable() else "?" for c in entry_name)
