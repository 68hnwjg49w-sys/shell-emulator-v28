"""Модульные тесты ядра эмулятора."""

import unittest

from src.errors import CommandError
from src.shell import Shell, tokenize


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


if __name__ == "__main__":
    unittest.main()
