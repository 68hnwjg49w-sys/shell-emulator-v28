"""Модульные тесты виртуальной файловой системы."""

import tempfile
import unittest
from pathlib import Path

from src.errors import VfsError
from src.vfs import Vfs, VfsDir, VfsFile

BINARY = bytes(range(256))


class VfsTestCase(unittest.TestCase):
    """Создаёт на диске каталог-источник VFS для тестов."""

    def setUp(self):
        """Создаёт дерево: motd, вложенные каталоги, двоичный файл."""
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = self.base / "source"
        (self.source / "home" / "julia" / "docs").mkdir(parents=True)
        (self.source / "empty").mkdir()
        (self.source / "motd").write_text("Привет!\n", encoding="utf-8")
        docs = self.source / "home" / "julia" / "docs"
        (docs / "a.txt").write_text("текст", encoding="utf-8")
        (docs / "image.bin").write_bytes(BINARY)

    def tearDown(self):
        """Удаляет временный каталог."""
        self._tmp.cleanup()


class LoadTest(VfsTestCase):
    """Проверяет загрузку VFS из каталога."""

    def test_structure_is_loaded(self):
        """Вложенные каталоги и файлы попадают в память."""
        vfs = Vfs.load(self.source)
        docs = vfs.root.children["home"].children["julia"].children["docs"]
        self.assertIsInstance(docs, VfsDir)
        self.assertEqual(docs.children["a.txt"].data, "текст".encode())
        self.assertEqual(docs.children["image.bin"].data, BINARY)

    def test_stats(self):
        """Подсчёт каталогов и файлов без корня."""
        self.assertEqual(Vfs.load(self.source).stats(), (4, 3))

    def test_works_in_memory(self):
        """После загрузки VFS не зависит от файлов на диске."""
        vfs = Vfs.load(self.source)
        (self.source / "motd").unlink()
        self.assertEqual(vfs.motd(), "Привет!\n")

    def test_missing_directory(self):
        """Несуществующий каталог — ошибка загрузки."""
        with self.assertRaisesRegex(VfsError, "не найдена"):
            Vfs.load(self.base / "missing")

    def test_file_instead_of_directory(self):
        """Файл вместо каталога — ошибка загрузки."""
        with self.assertRaisesRegex(VfsError, "указан не каталог"):
            Vfs.load(self.source / "motd")

    def test_empty_path(self):
        """Пустой путь — ошибка загрузки."""
        with self.assertRaisesRegex(VfsError, "пуст"):
            Vfs.load("")


class MotdTest(VfsTestCase):
    """Проверяет вывод файла motd."""

    def test_motd_from_root(self):
        """Текст motd берётся из корня VFS."""
        self.assertEqual(Vfs.load(self.source).motd(), "Привет!\n")

    def test_no_motd(self):
        """Без файла motd текста нет."""
        (self.source / "motd").unlink()
        self.assertIsNone(Vfs.load(self.source).motd())

    def test_motd_directory_is_ignored(self):
        """Каталог с именем motd не считается сообщением."""
        vfs = Vfs(VfsDir({"motd": VfsDir()}))
        self.assertIsNone(vfs.motd())

    def test_empty_vfs(self):
        """Пустая VFS не содержит ни файлов, ни motd."""
        self.assertEqual(Vfs().stats(), (0, 0))
        self.assertIsNone(Vfs().motd())


class SaveTest(VfsTestCase):
    """Проверяет команду сохранения VFS на диск."""

    def _tree(self, root):
        """Возвращает словарь «относительный путь → содержимое»."""
        return {
            str(path.relative_to(root)): (
                path.read_bytes() if path.is_file() else None
            )
            for path in root.rglob("*")
        }

    def test_saved_copy_matches_source(self):
        """Сохранённая копия совпадает с исходным каталогом."""
        target = self.base / "copy"
        Vfs.load(self.source).save(target)
        self.assertEqual(self._tree(target), self._tree(self.source))

    def test_parent_directories_are_created(self):
        """Недостающие родительские каталоги создаются."""
        target = self.base / "out" / "deep" / "copy"
        Vfs(VfsDir({"f": VfsFile(b"x")})).save(target)
        self.assertEqual((target / "f").read_bytes(), b"x")

    def test_existing_target(self):
        """Существующий путь не перезаписывается."""
        with self.assertRaisesRegex(VfsError, "уже существует"):
            Vfs.load(self.source).save(self.base)

    def test_inside_source(self):
        """Сохранять внутрь исходной VFS нельзя."""
        vfs = Vfs.load(self.source)
        with self.assertRaisesRegex(VfsError, "внутрь исходной"):
            vfs.save(self.source / "copy")
        self.assertFalse((self.source / "copy").exists())


if __name__ == "__main__":
    unittest.main()
