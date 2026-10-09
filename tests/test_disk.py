"""Модульные тесты команды du."""

import unittest

from src.errors import CommandError
from src.vfs import VfsFile
from tests.helpers import make_shell


class DuTest(unittest.TestCase):
    """Проверяет команду du."""

    def setUp(self):
        """Создаёт ядро с готовой VFS."""
        self.shell = make_shell()

    def test_bytes_from_inner_to_outer(self):
        """-b: размеры в байтах, вложенные каталоги раньше внешних."""
        answer = self.shell.execute("du -b home/julia")
        self.assertEqual(answer.split("\n"), [
            "1502\thome/julia/docs",
            "0\thome/julia/empty",
            "1502\thome/julia",
        ])

    def test_default_is_kibibytes_rounded_up(self):
        """По умолчанию размер в КиБ с округлением вверх."""
        self.assertEqual(
            self.shell.execute("du home/julia/docs"), "2\thome/julia/docs"
        )

    def test_summary(self):
        """-s: только итог по каталогу."""
        self.assertEqual(self.shell.execute("du -sb home"), "1503\thome")

    def test_human_readable(self):
        """-h: размер с единицей измерения."""
        self.assertEqual(self.shell.execute("du -sh home"), "1.5K\thome")
        self.assertEqual(self.shell.execute("du -h motd"), "2B\tmotd")

    def test_file_operand(self):
        """Для файла выводится его размер."""
        self.assertEqual(self.shell.execute("du -b readme.txt"),
                         "10\treadme.txt")

    def test_current_directory_by_default(self):
        """Без пути считается текущий каталог."""
        self.shell.execute("cd home/julia/docs")
        self.assertEqual(self.shell.execute("du -b"), "1502\t.")

    def test_root_operand(self):
        """Для корня пути вложенных каталогов начинаются с /."""
        first = self.shell.execute("du -b /").split("\n")[0]
        self.assertTrue(first.endswith("\t/home/julia/docs"))

    def test_several_operands(self):
        """Для нескольких путей выводится по строке на каждый."""
        answer = self.shell.execute("du -sb motd readme.txt")
        self.assertEqual(answer, "2\tmotd\n10\treadme.txt")

    def test_large_units(self):
        """Мегабайты и гигабайты получают свои буквы."""
        data = b"0" * (3 * 1024 * 1024)
        self.shell.vfs.root.children["big"] = VfsFile(data)
        self.assertEqual(self.shell.execute("du -h big"), "3.0M\tbig")

    def test_missing_path(self):
        """Несуществующий путь — ошибка."""
        with self.assertRaisesRegex(CommandError, "Нет такого файла"):
            self.shell.execute("du nope")

    def test_unknown_option(self):
        """Неизвестная опция — ошибка."""
        with self.assertRaisesRegex(CommandError, "неизвестная опция"):
            self.shell.execute("du -x")


if __name__ == "__main__":
    unittest.main()
