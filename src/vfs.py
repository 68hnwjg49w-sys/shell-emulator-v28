"""Виртуальная файловая система (VFS), размещённая в памяти.

Источник VFS — каталог на диске пользователя. При загрузке каталог
целиком читается в память; дальше эмулятор работает только с копией
в памяти, исходные файлы не изменяются.
"""

import copy
from dataclasses import dataclass, field
from pathlib import Path

from src.errors import VfsError

MOTD_NAME = "motd"
TEXT_ENCODING = "utf-8"


@dataclass
class VfsFile:
    """Файл VFS: содержимое хранится в памяти в виде байтов."""

    data: bytes = b""


@dataclass
class VfsDir:
    """Каталог VFS: словарь «имя → файл или каталог»."""

    children: dict = field(default_factory=dict)


class Vfs:
    """VFS в памяти: загрузка из каталога, motd и сохранение."""

    def __init__(self, root=None, source=None):
        """Создаёт VFS с корневым каталогом и путём к источнику."""
        self.root = root if root is not None else VfsDir()
        self.source = Path(source).resolve() if source else None

    @classmethod
    def load(cls, path):
        """Загружает каталог с диска целиком в память."""
        if not path:
            raise VfsError("путь к VFS пуст")
        source = Path(path)
        if not source.exists():
            raise VfsError("VFS не найдена: {}".format(path))
        if not source.is_dir():
            raise VfsError("VFS {}: указан не каталог".format(path))
        try:
            root = _read_dir(source)
        except OSError as error:
            raise VfsError(
                "не удалось загрузить VFS {}: {}".format(path, error)
            ) from error
        return cls(root, source)

    def motd(self):
        """Возвращает текст файла motd из корня VFS или None."""
        node = self.root.children.get(MOTD_NAME)
        if not isinstance(node, VfsFile):
            return None
        return node.data.decode(TEXT_ENCODING, errors="replace")

    def get(self, parts):
        """Возвращает узел по списку имён от корня или None."""
        node = self.root
        for name in parts:
            if not isinstance(node, VfsDir):
                return None
            node = node.children.get(name)
            if node is None:
                return None
        return node

    def put(self, parts, node):
        """Помещает узел по пути; родительский каталог должен быть."""
        self.get(parts[:-1]).children[parts[-1]] = node

    def delete(self, parts):
        """Удаляет узел по пути из памяти."""
        del self.get(parts[:-1]).children[parts[-1]]

    def stats(self):
        """Возвращает число каталогов и файлов в VFS, не считая корня."""
        return _count(self.root)

    def save(self, path):
        """Сохраняет VFS на диск в исходном формате — в виде каталога."""
        target = Path(path)
        self._check_target(target)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_dir(self.root, target)
        except OSError as error:
            raise VfsError(
                "vfs-save: не удалось сохранить {}: {}".format(path, error)
            ) from error

    def _check_target(self, target):
        """Проверяет, что сохранение не затронет существующие данные."""
        if target.exists():
            raise VfsError("vfs-save: {} уже существует".format(target))
        if self.source and self.source in target.resolve().parents:
            raise VfsError("vfs-save: нельзя сохранять внутрь исходной VFS")


def _read_dir(path):
    """Рекурсивно читает каталог с диска в узел VfsDir."""
    node = VfsDir()
    for entry in sorted(path.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir():
            node.children[entry.name] = _read_dir(entry)
        elif entry.is_file():
            node.children[entry.name] = VfsFile(entry.read_bytes())
    return node


def _write_dir(node, path):
    """Рекурсивно записывает узел VfsDir на диск."""
    path.mkdir()
    for name, child in node.children.items():
        if isinstance(child, VfsDir):
            _write_dir(child, path / name)
        else:
            (path / name).write_bytes(child.data)


def _count(node):
    """Считает каталоги и файлы внутри узла VfsDir."""
    dirs = files = 0
    for child in node.children.values():
        if isinstance(child, VfsDir):
            sub_dirs, sub_files = _count(child)
            dirs += 1 + sub_dirs
            files += sub_files
        else:
            files += 1
    return dirs, files


def node_size(node):
    """Возвращает размер узла в байтах: сумму размеров всех файлов."""
    if isinstance(node, VfsFile):
        return len(node.data)
    return sum(node_size(child) for child in node.children.values())


def clone(node):
    """Возвращает независимую копию узла со всем содержимым."""
    return copy.deepcopy(node)
