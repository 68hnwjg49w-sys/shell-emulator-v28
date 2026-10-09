"""Команды, изменяющие VFS только в памяти: rmdir и cp."""

from src.cmd_nav import NOT_DIR, NOT_FOUND
from src.errors import CommandError
from src.options import split_options
from src.vfs import VfsDir, clone

NOT_EMPTY = "Каталог не пуст"
BUSY = "Каталог занят: это корень или текущий каталог"
MIN_CP_OPERANDS = 2
SINGLE_SOURCE = 1
RECURSIVE_FLAGS = {"r", "R"}


def rmdir(shell, name, args):
    """Удаляет пустые каталоги: rmdir путь..."""
    _, operands = split_options(name, args, "")
    if not operands:
        raise CommandError("{}: пропущен операнд".format(name))
    for text in operands:
        parts = shell.path(text)
        problem = _rmdir_problem(shell, parts)
        if problem:
            raise CommandError(
                "{}: не удалось удалить '{}': {}".format(name, text, problem)
            )
        shell.vfs.delete(parts)
    return ""


def _rmdir_problem(shell, parts):
    """Возвращает причину, по которой каталог нельзя удалить, или None."""
    node = shell.vfs.get(parts)
    if node is None:
        return NOT_FOUND
    if not isinstance(node, VfsDir):
        return NOT_DIR
    if shell.cwd[:len(parts)] == parts:
        return BUSY
    if node.children:
        return NOT_EMPTY
    return None


def cp(shell, name, args):
    """Копирует в памяти: cp [-r] источник... назначение."""
    flags, operands = split_options(name, args, "rR")
    if not operands:
        raise CommandError("{}: пропущен операнд".format(name))
    if len(operands) < MIN_CP_OPERANDS:
        raise CommandError(
            "{}: после '{}' пропущен операнд, задающий целевой файл".format(
                name, operands[0])
        )
    *sources, dest = operands
    dest_node = shell.vfs.get(shell.path(dest))
    if len(sources) > SINGLE_SOURCE and not isinstance(dest_node, VfsDir):
        raise CommandError(
            "{}: целевой объект '{}' не является каталогом".format(name, dest)
        )
    recursive = bool(flags & RECURSIVE_FLAGS)
    for source in sources:
        _copy_one(shell, name, (source, dest), recursive)
    return ""


def _copy_one(shell, name, texts, recursive):
    """Копирует один источник в назначение; texts — (источник, цель)."""
    source, dest = texts
    src_parts = shell.path(source)
    node = shell.vfs.get(src_parts)
    if node is None:
        raise CommandError("{}: не удалось выполнить stat для '{}': {}".format(
            name, source, NOT_FOUND))
    if isinstance(node, VfsDir) and not recursive:
        raise CommandError(
            "{}: не указан -r; пропускается каталог '{}'".format(name, source)
        )
    target = _target_parts(shell, name, src_parts, dest)
    problem = _target_problem(shell.vfs, src_parts, node, target)
    if problem:
        raise CommandError("{}: {}".format(
            name, problem.format(src=source, dst=dest)))
    _store(shell.vfs, target, clone(node))


def _target_parts(shell, name, src_parts, dest):
    """Определяет путь копии: внутри каталога назначения или под его именем."""
    dest_parts = shell.path(dest)
    if not isinstance(shell.vfs.get(dest_parts), VfsDir):
        return dest_parts
    if not src_parts:
        raise CommandError(
            "{}: нельзя копировать корневой каталог VFS".format(name)
        )
    return dest_parts + [src_parts[-1]]


def _target_problem(vfs, src_parts, node, target):
    """Возвращает шаблон сообщения о проблеме с целью копирования."""
    if target == src_parts:
        return "'{src}' и '{dst}' — один и тот же файл"
    is_dir = isinstance(node, VfsDir)
    if is_dir and target[:len(src_parts)] == src_parts:
        return "нельзя скопировать каталог '{src}' в самого себя '{dst}'"
    parent = vfs.get(target[:-1])
    if not isinstance(parent, VfsDir):
        return "не удалось создать '{dst}': " + (
            NOT_FOUND if parent is None else NOT_DIR)
    return _overwrite_problem(vfs.get(target), is_dir)


def _overwrite_problem(existing, is_dir):
    """Проверяет, можно ли заменить существующий узел копией."""
    if existing is None or isinstance(existing, VfsDir) == is_dir:
        return None
    if is_dir:
        return "невозможно перезаписать не каталог '{dst}' каталогом"
    return "невозможно перезаписать каталог '{dst}' не каталогом"


def _store(vfs, target, node):
    """Кладёт копию по пути; каталог на каталог — объединение."""
    existing = vfs.get(target)
    if isinstance(existing, VfsDir) and isinstance(node, VfsDir):
        for child_name, child in node.children.items():
            _store(vfs, target + [child_name], child)
    else:
        vfs.put(target, node)
