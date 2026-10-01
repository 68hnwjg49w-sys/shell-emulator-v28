"""Модульные тесты параметров запуска и стартового скрипта."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from src.config import NOT_SET, Config, parse_arguments, read_script
from src.errors import ConfigError


class ParseArgumentsTest(unittest.TestCase):
    """Проверяет разбор параметров командной строки."""

    def test_no_arguments(self):
        """Без параметров оба пути не заданы."""
        self.assertEqual(parse_arguments([]), Config())

    def test_both_arguments(self):
        """Оба параметра разбираются в соответствующие поля."""
        config = parse_arguments(["--vfs", "v", "--script", "s.txt"])
        self.assertEqual(config, Config("v", "s.txt"))

    def test_vfs_path_is_not_checked(self):
        """Путь к VFS на этом этапе только запоминается."""
        config = parse_arguments(["--vfs", "no/such/dir"])
        self.assertEqual(config.vfs_path, "no/such/dir")

    def test_unknown_argument(self):
        """Неизвестный параметр завершает разбор с ошибкой."""
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            parse_arguments(["--wat"])

    def test_items(self):
        """Незаданный параметр помечается особым значением."""
        self.assertEqual(
            Config(vfs_path="v").items(),
            [("vfs", "v"), ("script", NOT_SET)],
        )


class ReadScriptTest(unittest.TestCase):
    """Проверяет чтение и проверку стартового скрипта."""

    def setUp(self):
        """Создаёт временный каталог."""
        self._tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self._tmp.name)

    def tearDown(self):
        """Удаляет временный каталог."""
        self._tmp.cleanup()

    def test_commands_with_line_numbers(self):
        """Команды возвращаются с номерами строк; комментарии пропущены."""
        path = self.directory / "start.txt"
        path.write_text("# c\n\nls\n  cd x  \n", encoding="utf-8")
        self.assertEqual(read_script(path), [(3, "ls"), (4, "cd x")])

    def test_missing_file(self):
        """Отсутствующий файл — ошибка параметров."""
        with self.assertRaisesRegex(ConfigError, "не найден"):
            read_script(self.directory / "missing.txt")

    def test_directory(self):
        """Каталог вместо файла — ошибка параметров."""
        with self.assertRaisesRegex(ConfigError, "указан не файл"):
            read_script(self.directory)

    def test_empty_path(self):
        """Пустой путь — ошибка параметров."""
        with self.assertRaisesRegex(ConfigError, "пуст"):
            read_script("")

    def test_not_utf8(self):
        """Файл не в UTF-8 — ошибка параметров."""
        path = self.directory / "bad.txt"
        path.write_bytes(b"\xff\xfe\xfa")
        with self.assertRaisesRegex(ConfigError, "не удалось прочитать"):
            read_script(path)


if __name__ == "__main__":
    unittest.main()
