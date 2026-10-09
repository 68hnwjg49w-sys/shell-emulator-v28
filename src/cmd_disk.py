"""Команда du: размер файлов и каталогов VFS."""

from src.cmd_nav import CURRENT_DIR, NOT_FOUND
from src.errors import CommandError
from src.options import split_options
from src.sizes import BLOCK, human
from src.vfs import VfsDir, node_size



def du(shell, name, args):
    """Показывает размер: du [-hsb] [путь]. По умолчанию — в КиБ."""
    flags, operands = split_options(name, args, "hsb")
    lines = []
    for text in operands or [CURRENT_DIR]:
        node = shell.vfs.get(shell.path(text))
        if node is None:
            raise CommandError(
                "{}: не удаётся получить доступ к '{}': {}".format(
                    name, text, NOT_FOUND)
            )
        lines += _node_lines(text, node, flags)
    return "\n".join(lines)


def _node_lines(text, node, flags):
    """Строки отчёта для одного пути; каталоги — от вложенных к внешним."""
    if "s" in flags or not isinstance(node, VfsDir):
        return [_line(text, node_size(node), flags)]
    lines = []
    _walk(text, node, flags, lines)
    return lines


def _walk(path, node, flags, lines):
    """Обходит подкаталоги в глубину и добавляет их строки в отчёт."""
    for child_name in sorted(node.children):
        child = node.children[child_name]
        if isinstance(child, VfsDir):
            child_path = path.rstrip("/") + "/" + child_name
            _walk(child_path, child, flags, lines)
    lines.append(_line(path, node_size(node), flags))


def _line(path, size, flags):
    """Формирует строку «размер, табуляция, путь»."""
    return "{}\t{}".format(_format_size(size, flags), path)


def _format_size(size, flags):
    """Переводит размер в байты, КиБ (с округлением вверх) или -h."""
    if "b" in flags:
        return str(size)
    if "h" in flags:
        return human(size)
    return str(-(-size // BLOCK))
