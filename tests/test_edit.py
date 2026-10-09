"""Модульные тесты команд rmdir и cp."""

import tempfile
import unittest
from pathlib import Path

from src.errors import CommandError
from src.vfs import VfsDir, VfsFile
from tests.helpers import make_shell


class RmdirTest(unittest.TestCase):
    """Проверяет команду rmdir."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def test_removes_empty_directory(self):
        """Пустой каталог удаляется, ответа нет."""
        self.assertEqual(self.shell.execute("rmdir home/julia/empty"), "")
        self.assertEqual(self.shell.execute("ls home/julia"), "docs")

    def test_removes_several_directories(self):
        """Можно удалить сразу несколько каталогов."""
        self.shell.vfs.put(["one"], VfsDir())
        self.shell.vfs.put(["two"], VfsDir())
        self.shell.execute("rmdir one two")
        self.assertEqual(self.shell.execute("ls"), "home  motd  readme.txt")

    def test_not_empty(self):
        """Непустой каталог не удаляется."""
        with self.assertRaisesRegex(CommandError, "Каталог не пуст"):
            self.shell.execute("rmdir home")
        self.assertIsNotNone(self.shell.vfs.get(["home"]))

    def test_file_is_not_directory(self):
        """Файл удалить через rmdir нельзя."""
        with self.assertRaisesRegex(CommandError, "Не является каталогом"):
            self.shell.execute("rmdir motd")

    def test_missing_path(self):
        """Несуществующий путь — ошибка."""
        with self.assertRaisesRegex(CommandError, "Нет такого файла"):
            self.shell.execute("rmdir nope")

    def test_without_operand(self):
        """Без аргументов — ошибка."""
        with self.assertRaisesRegex(CommandError, "пропущен операнд"):
            self.shell.execute("rmdir")

    def test_unknown_option(self):
        """Неизвестная опция — ошибка."""
        with self.assertRaisesRegex(CommandError, "неизвестная опция"):
            self.shell.execute("rmdir -p home")

    def test_current_directory_is_busy(self):
        """Нельзя удалить текущий каталог и его родителей."""
        self.shell.execute("cd home/julia/empty")
        for line in ("rmdir .", "rmdir ../empty", "rmdir /home", "rmdir /"):
            with self.assertRaisesRegex(CommandError, "занят"):
                self.shell.execute(line)

    def test_stops_at_first_error(self):
        """Каталоги до ошибки удалены, после — нет."""
        self.shell.vfs.put(["one"], VfsDir())
        self.shell.vfs.put(["two"], VfsDir())
        with self.assertRaises(CommandError):
            self.shell.execute("rmdir one nope two")
        self.assertIsNone(self.shell.vfs.get(["one"]))
        self.assertIsNotNone(self.shell.vfs.get(["two"]))

    def test_change_reaches_saved_vfs(self):
        """После rmdir vfs-save записывает уже изменённую VFS."""
        self.shell.execute("rmdir home/julia/empty")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "saved"
            self.shell.execute("vfs-save {}".format(target))
            self.assertFalse((target / "home/julia/empty").exists())
            self.assertTrue((target / "home/julia/docs/a.txt").exists())


class CpFilesTest(unittest.TestCase):
    """Проверяет копирование файлов командой cp."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def _data(self, path):
        """Возвращает содержимое файла VFS по пути."""
        return self.shell.vfs.get(path.split("/")).data

    def test_copy_to_new_name(self):
        """Команда cp файл новое_имя создаёт копию с тем же содержимым."""
        self.assertEqual(self.shell.execute("cp motd copy.txt"), "")
        self.assertEqual(self._data("copy.txt"), b"hi")
        self.assertEqual(self._data("motd"), b"hi")

    def test_copy_is_independent(self):
        """Изменение оригинала не меняет копию."""
        self.shell.execute("cp motd copy.txt")
        self.shell.vfs.get(["motd"]).data = b"changed"
        self.assertEqual(self._data("copy.txt"), b"hi")

    def test_copy_into_directory(self):
        """Если назначение — каталог, копия кладётся внутрь."""
        self.shell.execute("cp motd home")
        self.assertEqual(self._data("home/motd"), b"hi")

    def test_overwrite_file(self):
        """Существующий файл перезаписывается."""
        self.shell.execute("cp readme.txt motd")
        self.assertEqual(self._data("motd"), b"0123456789")

    def test_several_sources(self):
        """Несколько источников копируются в каталог."""
        self.shell.execute("cp motd readme.txt home/julia")
        self.assertEqual(self._data("home/julia/motd"), b"hi")
        self.assertEqual(self._data("home/julia/readme.txt"), b"0123456789")

    def test_several_sources_need_directory(self):
        """Для нескольких источников назначение должно быть каталогом."""
        with self.assertRaisesRegex(CommandError, "не является каталогом"):
            self.shell.execute("cp motd readme.txt copy.txt")

    def test_relative_paths(self):
        """Пути отсчитываются от текущего каталога."""
        self.shell.execute("cd home/julia")
        self.shell.execute("cp /motd .")
        self.assertEqual(self._data("home/julia/motd"), b"hi")
        self.shell.execute("cp ../julia/motd ../here")
        self.assertEqual(self._data("home/here"), b"hi")

    def test_change_reaches_saved_vfs(self):
        """После cp vfs-save записывает копию на диск."""
        self.shell.execute("cp motd copy.txt")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "saved"
            self.shell.execute("vfs-save {}".format(target))
            self.assertEqual((target / "copy.txt").read_bytes(), b"hi")


class CpDirectoriesTest(unittest.TestCase):
    """Проверяет копирование каталогов командой cp -r."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def test_directory_needs_r(self):
        """Без -r каталог не копируется."""
        with self.assertRaisesRegex(CommandError, "не указан -r"):
            self.shell.execute("cp home/julia backup")

    def test_recursive_copy_to_new_name(self):
        """Команда cp -r копирует каталог со всем содержимым."""
        self.shell.execute("cp -r home/julia backup")
        self.assertEqual(
            self.shell.execute("du -b backup"),
            self.shell.execute("du -b home/julia").replace(
                "home/julia", "backup"),
        )
        self.assertEqual(self.shell.execute("ls backup/docs"), "a.txt  b.txt")

    def test_capital_r_is_also_allowed(self):
        """Опция -R действует так же, как -r."""
        self.shell.execute("cp -R home/julia backup")
        self.assertIsNotNone(self.shell.vfs.get(["backup", "docs"]))

    def test_copy_into_existing_directory(self):
        """Каталог назначения существует — копия кладётся внутрь."""
        self.shell.execute("cp -r home/julia/docs home/julia/empty")
        self.assertIsNotNone(
            self.shell.vfs.get(["home", "julia", "empty", "docs", "a.txt"])
        )

    def test_merge_with_existing_directory(self):
        """Каталог с тем же именем объединяется с копией."""
        self.shell.vfs.put(["x"], VfsDir({"docs": VfsDir(
            {"old.txt": VfsFile(b"o")})}))
        self.shell.execute("cp -r home/julia/docs x")
        self.assertEqual(self.shell.execute("ls x/docs"),
                         "a.txt  b.txt  old.txt")

    def test_into_itself(self):
        """Копировать каталог внутрь самого себя нельзя."""
        with self.assertRaisesRegex(CommandError, "в самого себя"):
            self.shell.execute("cp -r home home/julia/inside")
        with self.assertRaisesRegex(CommandError, "в самого себя"):
            self.shell.execute("cp -r home/julia home/julia")

    def test_root_cannot_be_copied(self):
        """Корень VFS скопировать нельзя."""
        with self.assertRaises(CommandError):
            self.shell.execute("cp -r / backup")
        with self.assertRaisesRegex(CommandError, "корневой каталог"):
            self.shell.execute("cp -r / home")


class CpErrorsTest(unittest.TestCase):
    """Проверяет ошибки команды cp."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def _fails(self, line, pattern):
        """Проверяет, что команда падает с ожидаемым сообщением."""
        with self.assertRaisesRegex(CommandError, pattern):
            self.shell.execute(line)

    def test_missing_operands(self):
        """Без операндов и с одним операндом — ошибка."""
        self._fails("cp", "пропущен операнд")
        self._fails("cp motd", "пропущен операнд, задающий целевой файл")

    def test_missing_source(self):
        """Несуществующий источник — ошибка."""
        self._fails("cp nope copy.txt", "Нет такого файла")

    def test_missing_parent_of_target(self):
        """Нет каталога, в котором нужно создать копию, — ошибка."""
        self._fails("cp motd nope/copy.txt", "не удалось создать")
        self._fails("cp motd readme.txt/copy.txt", "Не является каталогом")

    def test_same_file(self):
        """Копирование файла в самого себя — ошибка."""
        self._fails("cp motd motd", "один и тот же файл")

    def test_conflicting_types(self):
        """Каталог на месте файла и файл на месте каталога — ошибка."""
        self.shell.vfs.put(["x"], VfsDir({"motd": VfsDir()}))
        self._fails("cp motd x", "перезаписать каталог")
        self.shell.vfs.put(["y"], VfsDir())
        self.shell.vfs.put(["y", "empty"], VfsFile(b"f"))
        self._fails("cp -r home/julia/empty y", "перезаписать не каталог")

    def test_unknown_option(self):
        """Неизвестная опция — ошибка."""
        self._fails("cp -z motd copy.txt", "неизвестная опция")


if __name__ == "__main__":
    unittest.main()
