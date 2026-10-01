"""Модульные тесты ядра эмулятора."""

import tempfile
import unittest
from pathlib import Path

from src.errors import CommandError
from src.shell import Shell, tokenize
from src.vfs import Vfs, VfsDir, VfsFile


class TokenizeTest(unittest.TestCase):
    """Проверяет разбор строки на команду и аргументы."""

    def test_empty_line(self):
        """Пустая строка не содержит токенов."""
        self.assertEqual(tokenize(""), [])

    def test_only_spaces(self):
        """Строка из пробелов не содержит токенов."""
        self.assertEqual(tokenize("   "), [])

    def test_command_with_arguments(self):
        """Команда и аргументы разделяются пробелами."""
        self.assertEqual(tokenize("ls -la /tmp"), ["ls", "-la", "/tmp"])

    def test_repeated_spaces(self):
        """Несколько пробелов подряд считаются одним разделителем."""
        self.assertEqual(tokenize("  cd    docs  "), ["cd", "docs"])


class ShellTest(unittest.TestCase):
    """Проверяет выполнение команд."""

    def setUp(self):
        """Создаёт новое ядро перед каждым тестом."""
        self.shell = Shell()

    def test_blank_line(self):
        """Пустой ввод не порождает ответа."""
        self.assertEqual(self.shell.execute("  "), "")

    def test_ls_without_arguments(self):
        """Заглушка ls сообщает, что вызвана без аргументов."""
        self.assertEqual(self.shell.execute("ls"), "ls: вызвана без аргументов")

    def test_ls_with_arguments(self):
        """Заглушка ls выводит своё имя и аргументы."""
        answer = self.shell.execute("ls -la /home")
        self.assertEqual(answer, "ls: аргументы: -la, /home")

    def test_cd_with_argument(self):
        """Заглушка cd выводит своё имя и аргумент."""
        self.assertEqual(self.shell.execute("cd docs"), "cd: аргументы: docs")

    def test_cd_too_many_arguments(self):
        """Команда cd с двумя аргументами — ошибка."""
        with self.assertRaisesRegex(CommandError, "слишком много"):
            self.shell.execute("cd a b")

    def test_unknown_command(self):
        """Неизвестная команда — ошибка с её именем."""
        with self.assertRaisesRegex(CommandError, "wat: команда не найдена"):
            self.shell.execute("wat 1 2")

    def test_exit_stops_shell(self):
        """Команда exit завершает работу."""
        self.shell.execute("exit")
        self.assertFalse(self.shell.running)

    def test_exit_rejects_arguments(self):
        """Команда exit не принимает аргументов."""
        with self.assertRaises(CommandError):
            self.shell.execute("exit now")
        self.assertTrue(self.shell.running)


class VfsSaveCommandTest(unittest.TestCase):
    """Проверяет команду vfs-save."""

    def setUp(self):
        """Создаёт ядро с небольшой VFS и временный каталог."""
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.shell = Shell(Vfs(VfsDir({"motd": VfsFile(b"hi")})))

    def tearDown(self):
        """Удаляет временный каталог."""
        self._tmp.cleanup()

    def test_save(self):
        """vfs-save путь сохраняет VFS на диск."""
        target = self.base / "copy"
        answer = self.shell.execute("vfs-save {}".format(target))
        self.assertIn("сохранена", answer)
        self.assertEqual((target / "motd").read_bytes(), b"hi")

    def test_without_path(self):
        """vfs-save без пути — ошибка."""
        with self.assertRaisesRegex(CommandError, "ровно один"):
            self.shell.execute("vfs-save")

    def test_two_paths(self):
        """vfs-save с двумя путями — ошибка."""
        with self.assertRaises(CommandError):
            self.shell.execute("vfs-save a b")

    def test_default_vfs_is_empty(self):
        """Без VFS ядро работает с пустой VFS."""
        self.assertEqual(Shell().vfs.stats(), (0, 0))


if __name__ == "__main__":
    unittest.main()
